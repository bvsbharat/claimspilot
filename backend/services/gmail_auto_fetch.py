"""
Gmail Auto-Fetch Service
Periodically polls Gmail for new claim-related emails and processes them automatically
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GmailAutoFetchService:
    """Background service to automatically fetch and process claim emails from Gmail"""

    def __init__(self):
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.last_fetch_time: Optional[datetime] = None
        self.last_fetch_count = 0
        self.total_fetched = 0
        self.fetch_errors = 0

        # Configuration from environment
        self.enabled = os.getenv("GMAIL_AUTO_FETCH_ENABLED", "true").lower() == "true"
        self.interval_minutes = int(os.getenv("GMAIL_AUTO_FETCH_INTERVAL_MINUTES", "5"))
        self.days_back = int(os.getenv("GMAIL_AUTO_FETCH_DAYS_BACK", "7"))
        self.max_results = int(os.getenv("GMAIL_AUTO_FETCH_MAX_RESULTS", "10"))

    async def start(self):
        """Start the auto-fetch service"""
        if not self.enabled:
            logger.info("📧 Gmail auto-fetch is DISABLED (set GMAIL_AUTO_FETCH_ENABLED=true to enable)")
            return

        if self.running:
            logger.warning("Gmail auto-fetch service already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._fetch_loop())
        logger.info(f"✅ Gmail auto-fetch service started (interval: {self.interval_minutes} min)")

    async def stop(self):
        """Stop the auto-fetch service"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Gmail auto-fetch service stopped")

    def get_status(self) -> dict:
        """Get current status of auto-fetch service"""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "interval_minutes": self.interval_minutes,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "last_fetch_count": self.last_fetch_count,
            "total_fetched": self.total_fetched,
            "fetch_errors": self.fetch_errors
        }

    async def fetch_now(self) -> dict:
        """Manually trigger a fetch (bypasses interval)"""
        logger.info("📧 Manual fetch triggered")
        return await self._perform_fetch()

    async def _fetch_loop(self):
        """Main loop that periodically fetches emails"""
        logger.info("🔄 Gmail auto-fetch loop started")

        # Do an initial fetch immediately
        await self._perform_fetch()

        while self.running:
            try:
                # Wait for the configured interval
                await asyncio.sleep(self.interval_minutes * 60)

                if not self.running:
                    break

                # Perform fetch
                await self._perform_fetch()

            except asyncio.CancelledError:
                logger.info("Gmail auto-fetch loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Gmail auto-fetch loop: {e}", exc_info=True)
                self.fetch_errors += 1
                # Wait a bit before retrying after error
                await asyncio.sleep(60)

    async def _perform_fetch(self) -> dict:
        """
        Fetch and process new emails from Gmail

        Returns:
            Dict with fetch results
        """
        try:
            from .gmail_service import get_gmail_service
            from .pdf_generator import get_pdf_generator
            from .event_queue import get_event_queue

            gmail_service = get_gmail_service()

            # Check if Gmail is connected
            if not gmail_service.is_connected():
                logger.warning("Gmail not connected - skipping auto-fetch")
                return {
                    "success": False,
                    "error": "Gmail not connected",
                    "emails_found": 0,
                    "emails_processed": 0
                }

            logger.info(f"📧 Fetching claim emails (max: {self.max_results}, days back: {self.days_back})...")

            # Fetch emails
            emails = gmail_service.fetch_claim_emails(
                max_results=self.max_results,
                days_back=self.days_back
            )

            if not emails:
                logger.info("No new claim emails found")
                self.last_fetch_time = datetime.now()
                self.last_fetch_count = 0
                return {
                    "success": True,
                    "emails_found": 0,
                    "emails_processed": 0
                }

            logger.info(f"📬 Found {len(emails)} new claim emails")

            # Process emails into PDFs
            pdf_generator = get_pdf_generator()
            event_queue = get_event_queue()

            # Get upload directory
            upload_dir = Path(os.getenv("DATA_DIR", "./uploads"))

            processed_count = 0
            claim_ids = []

            for email in emails:
                try:
                    # Generate PDF from email
                    pdf_path = pdf_generator.generate_from_gmail_message(
                        message_id=email['id'],
                        subject=email['subject'],
                        sender=email['from'],
                        date=email['date'],
                        body=email['body_html'] or email['body_text'] or email['snippet'],
                        attachments=email['attachments'],
                        output_dir=upload_dir
                    )

                    if pdf_path:
                        processed_count += 1
                        claim_id = pdf_path.stem
                        claim_ids.append(claim_id)

                        # Mark email as read
                        gmail_service.mark_as_read(email['id'])

                        logger.info(f"✅ Auto-processed email to claim: {claim_id}")

                except Exception as e:
                    logger.error(f"Failed to process email {email['id']}: {e}")
                    continue

            # Update stats
            self.last_fetch_time = datetime.now()
            self.last_fetch_count = processed_count
            self.total_fetched += processed_count

            # Publish SSE event
            await event_queue.publish({
                "type": "gmail_auto_fetch",
                "message": f"📧 Auto-fetched {processed_count} of {len(emails)} claim emails",
                "emails_found": len(emails),
                "emails_processed": processed_count,
                "timestamp": self.last_fetch_time.isoformat()
            })

            logger.info(f"✅ Auto-fetch complete: {processed_count}/{len(emails)} emails processed")

            return {
                "success": True,
                "emails_found": len(emails),
                "emails_processed": processed_count,
                "claim_ids": claim_ids
            }

        except Exception as e:
            logger.error(f"Gmail auto-fetch failed: {e}", exc_info=True)
            self.fetch_errors += 1
            return {
                "success": False,
                "error": str(e),
                "emails_found": 0,
                "emails_processed": 0
            }


# Singleton instance
_gmail_auto_fetch_service: Optional[GmailAutoFetchService] = None


def get_gmail_auto_fetch_service() -> GmailAutoFetchService:
    """Get or create Gmail auto-fetch service instance"""
    global _gmail_auto_fetch_service
    if _gmail_auto_fetch_service is None:
        _gmail_auto_fetch_service = GmailAutoFetchService()
    return _gmail_auto_fetch_service
