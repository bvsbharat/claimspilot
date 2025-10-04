"""
PDF Generator Service for converting emails and attachments to PDF
"""

import os
import io
import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
from bs4 import BeautifulSoup
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF from email content and attachments"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='EmailHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=HexColor('#1a73e8'),
            spaceAfter=12,
            alignment=TA_LEFT
        ))

        self.styles.add(ParagraphStyle(
            name='EmailMeta',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=HexColor('#5f6368'),
            spaceAfter=6
        ))

        self.styles.add(ParagraphStyle(
            name='EmailBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=10
        ))

    def _clean_html(self, html_content: str) -> str:
        """Convert HTML to plain text, preserving structure"""
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text with line breaks preserved
            text = soup.get_text(separator='\n')

            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines()]
            text = '\n'.join(line for line in lines if line)

            return text
        except Exception as e:
            logger.error(f"HTML cleaning failed: {e}")
            return html_content

    def _add_email_header(self, story: List, email_data: Dict[str, Any]):
        """Add email metadata header to PDF"""
        story.append(Paragraph("Insurance Claim Email", self.styles['EmailHeader']))
        story.append(Spacer(1, 0.1 * inch))

        # Add email metadata
        metadata = [
            f"<b>From:</b> {email_data.get('from', 'Unknown')}",
            f"<b>To:</b> {email_data.get('to', 'Unknown')}",
            f"<b>Subject:</b> {email_data.get('subject', 'No Subject')}",
            f"<b>Date:</b> {email_data.get('date', 'Unknown')}",
        ]

        if email_data.get('cc'):
            metadata.append(f"<b>CC:</b> {email_data['cc']}")

        for line in metadata:
            story.append(Paragraph(line, self.styles['EmailMeta']))

        story.append(Spacer(1, 0.2 * inch))

    def _add_email_body(self, story: List, body_content: str):
        """Add email body to PDF"""
        story.append(Paragraph("<b>Email Content:</b>", self.styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))

        # Clean HTML if present
        clean_text = self._clean_html(body_content)

        # Split into paragraphs and add to story
        paragraphs = clean_text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                try:
                    # Escape special characters for ReportLab
                    safe_para = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_para, self.styles['EmailBody']))
                    story.append(Spacer(1, 0.1 * inch))
                except Exception as e:
                    logger.error(f"Failed to add paragraph: {e}")
                    continue

    def _add_attachment_image(self, story: List, attachment_data: bytes, filename: str, max_width: float = 6 * inch):
        """Add image attachment to PDF"""
        try:
            # Load image from bytes
            img = PILImage.open(io.BytesIO(attachment_data))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background

            # Save to bytes
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_buffer.seek(0)

            # Calculate dimensions
            img_width, img_height = img.size
            aspect_ratio = img_height / img_width

            if img_width > max_width * 72:  # Convert inches to points
                display_width = max_width
                display_height = max_width * aspect_ratio
            else:
                display_width = img_width / 72
                display_height = img_height / 72

            # Add to story
            story.append(Paragraph(f"<b>Attachment:</b> {filename}", self.styles['Heading3']))
            story.append(Spacer(1, 0.1 * inch))

            img_obj = Image(img_buffer, width=display_width, height=display_height)
            story.append(img_obj)
            story.append(Spacer(1, 0.2 * inch))

            logger.info(f"Added image attachment: {filename}")

        except Exception as e:
            logger.error(f"Failed to add image {filename}: {e}")
            story.append(Paragraph(f"<i>[Image attachment '{filename}' could not be displayed]</i>", self.styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

    def _add_attachment_pdf(self, story: List, filename: str):
        """Add reference to PDF attachment"""
        story.append(Paragraph(f"<b>PDF Attachment:</b> {filename}", self.styles['Heading3']))
        story.append(Paragraph(
            f"<i>Note: PDF attachment '{filename}' was included in the original email. "
            f"Please refer to the original attachment for full content.</i>",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2 * inch))

    def generate_email_pdf(
        self,
        email_data: Dict[str, Any],
        attachments: List[Dict[str, Any]],
        output_path: Path
    ) -> bool:
        """
        Generate PDF from email data and attachments

        Args:
            email_data: Dictionary containing email metadata and body
            attachments: List of attachment dictionaries with 'filename' and 'data'
            output_path: Path where PDF should be saved

        Returns:
            bool: True if PDF was generated successfully
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch
            )

            story = []

            # Add email header
            self._add_email_header(story, email_data)

            # Add email body
            body = email_data.get('body', '') or email_data.get('snippet', '')
            if body:
                self._add_email_body(story, body)

            # Add attachments section
            if attachments:
                story.append(PageBreak())
                story.append(Paragraph("<b>Attachments:</b>", self.styles['Heading2']))
                story.append(Spacer(1, 0.2 * inch))

                for attachment in attachments:
                    filename = attachment.get('filename', 'unknown')
                    data = attachment.get('data')

                    if not data:
                        continue

                    # Determine file type and process accordingly
                    ext = Path(filename).suffix.lower()

                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                        self._add_attachment_image(story, data, filename)
                    elif ext == '.pdf':
                        self._add_attachment_pdf(story, filename)
                    else:
                        story.append(Paragraph(
                            f"<b>Attachment:</b> {filename} ({ext} file)",
                            self.styles['Normal']
                        ))
                        story.append(Spacer(1, 0.1 * inch))

            # Build PDF
            doc.build(story)
            logger.info(f"PDF generated successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            return False

    def generate_from_gmail_message(
        self,
        message_id: str,
        subject: str,
        sender: str,
        date: str,
        body: str,
        attachments: List[Dict[str, Any]],
        output_dir: Path
    ) -> Optional[Path]:
        """
        Generate PDF from Gmail message data

        Args:
            message_id: Gmail message ID
            subject: Email subject
            sender: Email sender
            date: Email date
            body: Email body content
            attachments: List of attachments
            output_dir: Directory to save PDF

        Returns:
            Path to generated PDF or None if failed
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_'))[:50]
            filename = f"{timestamp}_gmail_{safe_subject.replace(' ', '_')}.pdf"
            output_path = output_dir / filename

            # Prepare email data
            email_data = {
                'from': sender,
                'to': 'Claims Department',
                'subject': subject,
                'date': date,
                'body': body,
                'message_id': message_id
            }

            # Generate PDF
            success = self.generate_email_pdf(email_data, attachments, output_path)

            if success:
                return output_path
            else:
                return None

        except Exception as e:
            logger.error(f"Failed to generate PDF from Gmail message: {e}", exc_info=True)
            return None


# Singleton instance
_pdf_generator: Optional[PDFGenerator] = None


def get_pdf_generator() -> PDFGenerator:
    """Get or create PDF generator instance"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFGenerator()
    return _pdf_generator
