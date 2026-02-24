import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import settings


class EmailSender:
    """Send reply emails via SMTP for IMAP providers"""
    
    # SMTP configurations for different providers
    SMTP_CONFIGS = {
        "gmail": {
            "host": "smtp.gmail.com",
            "port": 587,
            "use_tls": True
        },
        "outlook": {
            "host": "smtp.office365.com",
            "port": 587,
            "use_tls": True
        },
        "rediff": {
            "host": "smtp.rediffmail.com",
            "port": 587,
            "use_tls": True
        }
    }
    
    def __init__(self):
        self.provider = settings.imap_provider
        self.smtp_config = self.SMTP_CONFIGS.get(self.provider, {})
        self.from_email = settings.imap_email
        self.password = settings.imap_password
    
    async def send_unsubscribe_confirmation(
        self, 
        to_email: str, 
        original_subject: str,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> bool:
        """
        Send unsubscribe confirmation email
        
        Args:
            to_email: Recipient email address
            original_subject: Original email subject
            in_reply_to: Message-ID of original email (for threading)
            references: References header for email threading
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f"Re: {original_subject}"
            
            # Add threading headers for proper reply chain
            if in_reply_to:
                msg['In-Reply-To'] = in_reply_to
            if references:
                msg['References'] = references
            
            # Email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Unsubscribe Request Confirmed</h2>
                    
                    <p>Hello,</p>
                    
                    <p>We have received and processed your unsubscribe request.</p>
                    
                    <div style="background-color: #f0f8ff; border-left: 4px solid #2c5aa0; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>✓ You have been successfully removed from our mailing list.</strong></p>
                    </div>
                    
                    <p>We're sorry to see you go. Your email address has been immediately removed from our system, and you will no longer receive marketing emails from us.</p>
                    
                    <p>If you:</p>
                    <ul>
                        <li>Unsubscribed by mistake</li>
                        <li>Want to update your email preferences instead</li>
                        <li>Have any questions or concerns</li>
                    </ul>
                    <p>Please feel free to reach out to us directly.</p>
                    
                    <br>
                    <p>Best regards,<br>
                    <strong>{self.from_email.split('@')[0].replace('.', ' ').title()} Team</strong></p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #888; font-size: 12px;">
                        This is an automated confirmation email. If you change your mind in the future, 
                        you're always welcome to subscribe again.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"""
Hello,

We have received and processed your unsubscribe request.

✓ You have been successfully removed from our mailing list.

We're sorry to see you go. Your email address has been immediately removed from our system, 
and you will no longer receive marketing emails from us.

If you unsubscribed by mistake or have any questions, please feel free to reach out.

Best regards,
{self.from_email.split('@')[0].replace('.', ' ').title()}

---
This is an automated confirmation email.
            """
            
            # Attach both versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email via SMTP
            print(f"📤 Connecting to SMTP server: {self.smtp_config['host']}")
            
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls'):
                    server.starttls()
                
                server.login(self.from_email, self.password)
                server.send_message(msg)
            
            print(f"✅ Confirmation email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send confirmation email: {str(e)}")
            return False