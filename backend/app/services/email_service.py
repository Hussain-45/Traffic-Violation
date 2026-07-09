"""
Email Service Implementation
============================
Handles connection pooling, SMTP/TLS auth, connection reuse, attachments, and timeouts.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from loguru import logger

from backend.app.config import settings


class EmailService:
    """
    Business service layer managing secure SMTP communication and attachment packaging.
    """

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_EMAIL
        self.password = settings.SMTP_APP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.sender = settings.EMAIL_FROM

    def connect_smtp(self, timeout: float = 10.0) -> smtplib.SMTP:
        """
        Establishes and returns an authenticated SMTP connection.
        Supports secure TLS connection upgrades.
        """
        if not self.username or not self.password:
            raise ValueError("Authentication credentials are missing in SMTP configuration.")

        logger.info("SMTP Connecting")
        
        # Connect to SMTP server
        server = smtplib.SMTP(self.host, self.port, timeout=timeout)
        
        if self.use_tls:
            server.ehlo()
            server.starttls()
            server.ehlo()
            logger.debug("Secure TLS upgraded successfully.")

        try:
            server.login(self.username, self.password)
            logger.info("SMTP Connected")
        except Exception as e:
            server.quit()
            logger.error("Authentication failure: Invalid credentials.")
            raise e

        return server

    def close_smtp(self, server: Optional[smtplib.SMTP]) -> None:
        """Safely terminates an active SMTP connection."""
        if server:
            try:
                server.quit()
                logger.info("SMTP Disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting from SMTP: {e}")

    def create_mime_message(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[str]] = None
    ) -> MIMEMultipart:
        """
        Assembles a multipart MIME email structure with HTML/text body and attachments.
        """
        msg = MIMEMultipart("mixed")
        msg["From"] = self.sender
        msg["To"] = recipient
        msg["Subject"] = subject

        # Attach text fallbacks
        msg_alternative = MIMEMultipart("alternative")
        msg_alternative.attach(MIMEText(text_body, "plain"))
        msg_alternative.attach(MIMEText(html_body, "html"))
        msg.attach(msg_alternative)

        # Attach evidence crop files
        if attachments:
            for filepath in attachments:
                if not filepath:
                    continue

                if not os.path.exists(filepath):
                    logger.warning(f"Attachment file not found: {filepath}. Skipping.")
                    continue

                try:
                    filename = os.path.basename(filepath)
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}"
                    )
                    msg.attach(part)
                    logger.debug(f"File attached: {filename}")
                except Exception as e:
                    logger.error(f"Failed to attach file {filepath}: {e}")

        return msg

    def send_email(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[str]] = None,
        timeout: float = 10.0
    ) -> bool:
        """
        Establishes a single-use SMTP session to deliver a compiled email notice.
        """
        if not recipient:
            logger.error("Error: Missing recipient.")
            return False

        server = None
        try:
            server = self.connect_smtp(timeout=timeout)
            msg = self.create_mime_message(recipient, subject, html_body, text_body, attachments)
            
            server.sendmail(self.username, recipient, msg.as_string())
            logger.info(f"Email Sent: To {recipient} with subject '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Email Failed: Failed to deliver mail to {recipient}: {e}")
            return False
        finally:
            self.close_smtp(server)

    def send_with_connection(
        self,
        server: smtplib.SMTP,
        recipient: str,
        subject: str,
        html_body: str,
        text_body: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Sends an email using an already active, reused SMTP connection.
        """
        if not recipient:
            logger.error("Error: Missing recipient.")
            return False

        try:
            msg = self.create_mime_message(recipient, subject, html_body, text_body, attachments)
            server.sendmail(self.username, recipient, msg.as_string())
            logger.info(f"Email Sent: To {recipient} with subject '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Email Failed: Reuse session delivery failed: {e}")
            return False


# Singleton instance
email_service = EmailService()
