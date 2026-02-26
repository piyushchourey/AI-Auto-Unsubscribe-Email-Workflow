import imaplib
import email
import email.utils
from email.header import decode_header
from typing import List, Dict
from imapclient import IMAPClient
from config import settings


class EmailFetcher:
    """Service for fetching emails from any IMAP-compatible email provider"""
    
    def __init__(self):
        """Initialize IMAP connection settings"""
        # Use Pydantic settings attributes directly
        self.host = settings.imap_host
        self.port = settings.imap_port
        self.email = settings.imap_email
        self.password = settings.imap_password
        self.folder = settings.imap_folder
        self.provider = settings.imap_provider
        
        # Validate configuration
        if not self.host:
            raise ValueError(f"IMAP host not configured for provider: {self.provider}")
        
    def _decode_mime_header(self, header_value):
        """Decode MIME encoded email headers"""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        
        return decoded_string
    
    def _extract_email_body(self, msg) -> str:
        """Extract plain text body from email message"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get plain text content
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            break
                    except Exception as e:
                        print(f"Error decoding part: {e}")
                        continue
        else:
            # Not multipart
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"Error decoding message: {e}")
        
        return body.strip()
    
    async def fetch_unread_emails(self) -> List[Dict[str, str]]:
        """
        Fetch unread emails from the configured IMAP mailbox
        
        Returns:
            List of email dictionaries with sender_email, message_text, and subject
        """
        emails = []
        
        try:
            print(f"📬 Connecting to IMAP server: {self.host}")
            print(f"📧 Provider: {self.provider.upper()}")
            
            # Connect to IMAP server with SSL
            with IMAPClient(self.host, port=self.port, ssl=True) as client:
                # Login
                client.login(self.email, self.password)
                print(f"✅ Logged in as: {self.email}")
                
                # Select the mailbox folder
                client.select_folder(self.folder)
                print(f"📂 Selected folder: {self.folder}")
                
                # Search for unread messages
                messages = client.search('UNSEEN')
                print(f"📧 Found {len(messages)} unread emails")
                
                if not messages:
                    return emails
                
                # Fetch email data
                for msg_id in messages:
                    try:
                        # Fetch the email message
                        msg_data = client.fetch([msg_id], ['RFC822'])
                        raw_email = msg_data[msg_id][b'RFC822']
                        
                        # Parse the email
                        msg = email.message_from_bytes(raw_email)
                        
                        # Extract sender email
                        from_header = msg.get('From', '')
                        sender_email = email.utils.parseaddr(from_header)[1]
                        
                        # Extract subject
                        subject = self._decode_mime_header(msg.get('Subject', ''))
                        
                        # Extract body
                        body = self._extract_email_body(msg)
                        
                        # Extract message headers
                        headers = {
                            'Message-ID': msg.get('Message-ID', ''),
                            'In-Reply-To': msg.get('In-Reply-To', ''),
                            'References': msg.get('References', ''),
                            'Received': msg.get('Received', ''),
                        }
                        
                        if sender_email and body:
                            emails.append({
                                'sender_email': sender_email,
                                'message_text': body,
                                'subject': subject,
                                'message_id': headers['Message-ID'],
                                'in_reply_to': headers['In-Reply-To'],
                                'references': headers['References'],
                                'received_time': headers['Received']
                            })
                            print(f"  📩 From: {sender_email}")
                            print(f"  📄 Subject: {subject[:50]}...")
                        
                        # Mark as read after processing
                        client.add_flags([msg_id], ['\\Seen'])
                        
                    except Exception as e:
                        print(f"❌ Error processing message {msg_id}: {e}")
                        continue
                
                print(f"✅ Successfully fetched {len(emails)} emails")
                
        except Exception as e:
            print(f"❌ Error connecting to IMAP: {e}")
            raise
        
        return emails
    
    async def test_connection(self) -> bool:
        """Test IMAP connection without fetching emails"""
        try:
            print(f"🔍 Testing IMAP connection to {self.host}...")
            
            with IMAPClient(self.host, port=self.port, ssl=True) as client:
                client.login(self.email, self.password)
                folders = client.list_folders()
                
                print(f"✅ Connection successful!")
                print(f"📁 Available folders: {[f[2] for f in folders]}")
                
                return True
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
