"""
Gmail Service using LangChain GmailToolkit for automatic authentication
"""

import os
import logging
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.search import GmailSearch
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailService:
    """Handle Gmail operations using LangChain's GmailToolkit"""

    # Keywords to identify claim-related emails
    CLAIM_KEYWORDS = [
        'claim', 'insurance', 'accident', 'injury', 'policy',
        'collision', 'damage', 'incident', 'loss', 'acord'
    ]

    def __init__(self):
        self.toolkit = None
        self.api_resource = None
        self._initialize()

    def _initialize(self):
        """Initialize Gmail toolkit with credentials"""
        try:
            # Set working directory to backend folder to find credentials
            import os
            backend_dir = Path(__file__).parent.parent
            os.chdir(backend_dir)

            # Check if credentials files exist
            creds_file = backend_dir / "credentials.json"
            token_file = backend_dir / "token.json"

            if not creds_file.exists():
                logger.error(f"credentials.json not found at {creds_file}")
                return

            if not token_file.exists():
                logger.error(f"token.json not found at {token_file}")
                return

            logger.info(f"Loading Gmail credentials from {backend_dir}")

            # GmailToolkit automatically uses credentials.json and token.json
            # from the current directory
            self.toolkit = GmailToolkit()
            self.api_resource = self.toolkit.api_resource
            logger.info("Gmail toolkit initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail toolkit: {e}", exc_info=True)
            logger.warning("Make sure credentials.json and token.json are in the backend directory")

    def is_connected(self) -> bool:
        """Check if Gmail is connected"""
        return self.toolkit is not None and self.api_resource is not None

    def get_user_email(self) -> Optional[str]:
        """Get the authenticated user's email address"""
        try:
            if not self.is_connected():
                return None

            profile = self.api_resource.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            logger.error(f"Failed to get user email: {e}")
            return None

    def _decode_message_part(self, part: Dict[str, Any]) -> str:
        """Decode message part data"""
        try:
            data = part.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            return ''
        except Exception as e:
            logger.error(f"Failed to decode message part: {e}")
            return ''

    def _extract_message_body(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract plain text and HTML body from message payload"""
        body = {'text': '', 'html': ''}

        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain':
                    body['text'] = self._decode_message_part(part)
                elif mime_type == 'text/html':
                    body['html'] = self._decode_message_part(part)
                elif 'parts' in part:
                    # Recursive for nested parts
                    nested_body = self._extract_message_body(part)
                    if not body['text']:
                        body['text'] = nested_body['text']
                    if not body['html']:
                        body['html'] = nested_body['html']
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                body['text'] = self._decode_message_part(payload)
            elif mime_type == 'text/html':
                body['html'] = self._decode_message_part(payload)

        return body

    def _extract_attachments(self, message_id: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachment data from message"""
        attachments = []

        if 'parts' not in payload:
            return attachments

        for part in payload['parts']:
            if part.get('filename'):
                filename = part.get('filename')
                mime_type = part.get('mimeType', '')

                # Get attachment data
                if 'data' in part['body']:
                    data = part['body']['data']
                elif 'attachmentId' in part['body']:
                    attachment_id = part['body']['attachmentId']
                    try:
                        attachment = self.api_resource.users().messages().attachments().get(
                            userId='me',
                            messageId=message_id,
                            id=attachment_id
                        ).execute()
                        data = attachment.get('data', '')
                    except Exception as e:
                        logger.error(f"Failed to fetch attachment {filename}: {e}")
                        continue
                else:
                    continue

                # Decode attachment data
                try:
                    attachment_data = base64.urlsafe_b64decode(data)
                    attachments.append({
                        'filename': filename,
                        'mime_type': mime_type,
                        'size': len(attachment_data),
                        'data': attachment_data
                    })
                    logger.info(f"Extracted attachment: {filename} ({len(attachment_data)} bytes)")
                except Exception as e:
                    logger.error(f"Failed to decode attachment {filename}: {e}")

        return attachments

    def fetch_claim_emails(
        self,
        max_results: int = 10,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails that match claim keywords from the last N days

        Args:
            max_results: Maximum number of emails to fetch
            days_back: Number of days to look back

        Returns:
            List of email dictionaries with metadata and content
        """
        try:
            if not self.is_connected():
                raise Exception("Gmail not connected. Check credentials.json and token.json files.")

            # Build search query - search in subject AND body for better coverage
            # Use bare keywords to search everywhere, not just subject
            keyword_query = ' OR '.join(self.CLAIM_KEYWORDS)
            # Add is:unread to only fetch new emails we haven't processed yet
            query = f'({keyword_query}) is:unread newer_than:{days_back}d'

            logger.info(f"Searching Gmail with query: {query}")

            # Search for messages
            search = GmailSearch(api_resource=self.api_resource)
            search_results = search.run(query)

            # Parse search results
            if not search_results or search_results == "No emails found.":
                logger.info("No claim-related emails found")
                return []

            # Get message IDs from search results
            messages = self.api_resource.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute().get('messages', [])

            if not messages:
                logger.info("No claim-related emails found")
                return []

            logger.info(f"Found {len(messages)} claim-related emails")

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    message = self.api_resource.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    # Extract headers
                    headers = {h['name']: h['value'] for h in message['payload']['headers']}

                    # Extract body
                    body = self._extract_message_body(message['payload'])

                    # Extract attachments
                    attachments = self._extract_attachments(msg['id'], message['payload'])

                    email_data = {
                        'id': msg['id'],
                        'thread_id': message.get('threadId'),
                        'from': headers.get('From', ''),
                        'to': headers.get('To', ''),
                        'subject': headers.get('Subject', 'No Subject'),
                        'date': headers.get('Date', ''),
                        'snippet': message.get('snippet', ''),
                        'body_text': body['text'],
                        'body_html': body['html'],
                        'attachments': attachments,
                        'labels': message.get('labelIds', []),
                        'has_attachments': len(attachments) > 0
                    }

                    emails.append(email_data)
                    logger.info(f"Fetched email: {email_data['subject']} ({len(attachments)} attachments)")

                except HttpError as e:
                    logger.error(f"Failed to fetch message {msg['id']}: {e}")
                    continue

            return emails

        except Exception as e:
            logger.error(f"Failed to fetch claim emails: {e}", exc_info=True)
            raise

    def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        try:
            if not self.is_connected():
                return False

            self.api_resource.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Marked message {message_id} as read")
            return True

        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False

    def add_label(self, message_id: str, label: str) -> bool:
        """Add label to email"""
        try:
            if not self.is_connected():
                return False

            # Check if custom label exists, create if not
            labels = self.api_resource.users().labels().list(userId='me').execute()
            label_id = None

            for lbl in labels.get('labels', []):
                if lbl['name'].upper() == label.upper():
                    label_id = lbl['id']
                    break

            if not label_id:
                # Create label
                label_object = {
                    'name': label,
                    'messageListVisibility': 'show',
                    'labelListVisibility': 'labelShow'
                }
                created_label = self.api_resource.users().labels().create(
                    userId='me',
                    body=label_object
                ).execute()
                label_id = created_label['id']

            # Add label to message
            self.api_resource.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            logger.info(f"Added label '{label}' to message {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add label: {e}")
            return False


# Singleton instance
_gmail_service: Optional[GmailService] = None


def get_gmail_service() -> GmailService:
    """Get or create Gmail service instance"""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service
