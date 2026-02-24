"""
Microsoft Graph API Email Fetcher
Uses OAuth 2.0 authentication to fetch emails from Microsoft 365/Outlook
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import msal
from config import settings


class GraphEmailFetcher:
    """Fetch emails using Microsoft Graph API with OAuth authentication"""
    
    def __init__(self):
        """Initialize Graph API client"""
        self.tenant_id = settings.graph_tenant_id
        self.client_id = settings.graph_client_id
        self.client_secret = settings.graph_client_secret
        self.user_email = settings.graph_user_email
        
        # MSAL (Microsoft Authentication Library) client
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )
        
        # Graph API endpoints
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
    def get_access_token(self) -> Optional[str]:
        """
        Get access token using client credentials flow
        
        Returns:
            Access token string or None if failed
        """
        try:
            # Acquire token for application (daemon/service scenario)
            result = self.app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                print("✅ Successfully acquired access token")
                return result["access_token"]
            else:
                error = result.get("error_description", result.get("error"))
                print(f"❌ Failed to acquire token: {error}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            return None
    
    async def fetch_unread_emails(self, folder: str = "Inbox") -> List[Dict]:
        """
        Fetch unread emails from Microsoft 365 mailbox
        
        Args:
            folder: Folder name (default: Inbox)
            
        Returns:
            List of email dictionaries with sender_email, message_text, subject
        """
        try:
            print(f"\n📬 Connecting to Microsoft Graph API...")
            print(f"📧 User: {self.user_email}")
            print(f"📂 Folder: {folder}")
            
            # Get access token
            access_token = self.get_access_token()
            if not access_token:
                print("❌ Failed to get access token")
                return []
            
            # Headers for Graph API requests
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Fetch unread messages
            # Using /users/{email}/mailFolders/{folder}/messages endpoint
            messages_url = (
                f"{self.graph_endpoint}/users/{self.user_email}/"
                f"mailFolders/{folder}/messages"
            )
            
            # Filter for unread messages
            params = {
                "$filter": "isRead eq false",
                "$select": "id,subject,from,body,receivedDateTime,isRead",
                "$top": 50,  # Limit to 50 most recent
                "$orderby": "receivedDateTime desc"
            }
            
            response = requests.get(messages_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get("value", [])
            
            print(f"📧 Found {len(messages)} unread emails")
            
            emails = []
            for msg in messages:
                try:
                    # Extract sender email
                    sender_info = msg.get("from", {}).get("emailAddress", {})
                    sender_email = sender_info.get("address", "unknown@unknown.com")
                    
                    # Extract subject
                    subject = msg.get("subject", "No Subject")
                    
                    # Extract body (prefer text, fallback to HTML)
                    body_obj = msg.get("body", {})
                    content_type = body_obj.get("contentType", "text")
                    message_text = body_obj.get("content", "")
                    
                    # If HTML, strip tags (basic)
                    if content_type == "html":
                        import re
                        message_text = re.sub('<[^<]+?>', '', message_text)
                    
                    # Get message ID for marking as read
                    message_id = msg.get("id")
                    
                    print(f"  📩 From: {sender_email}")
                    print(f"  📄 Subject: {subject}")
                    
                    emails.append({
                        "sender_email": sender_email,
                        "message_text": message_text.strip(),
                        "subject": subject,
                        "message_id": message_id  # Store for marking as read
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error parsing message: {str(e)}")
                    continue
            
            if emails:
                print(f"✅ Successfully fetched {len(emails)} emails")
            else:
                print("📭 No unread emails found")
            
            return emails
            
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Error fetching emails from Graph API: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read
        
        Args:
            message_id: The message ID to mark as read
            
        Returns:
            True if successful, False otherwise
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # PATCH request to update message
            update_url = (
                f"{self.graph_endpoint}/users/{self.user_email}/"
                f"messages/{message_id}"
            )
            
            data = {"isRead": True}
            
            response = requests.patch(update_url, headers=headers, json=data)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"⚠️ Error marking message as read: {str(e)}")
            return False
    
    async def send_reply_email(self, message_id: str, recipient_email: str, subject: str) -> bool:
        """
        Send a reply email using Microsoft Graph API
    
        Args:
            message_id: The original message ID to reply to
            recipient_email: Recipient's email address
            subject: Original subject line
            
        Returns:
            True if successful, False otherwise
        """
        try:
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Compose the reply message
            reply_body = f"""
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
                    <strong>{self.user_email.split('@')[0].replace('.', ' ').title()} Team</strong></p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #888; font-size: 12px;">
                        This is an automated confirmation email. If you change your mind in the future, 
                        you're always welcome to subscribe again.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # Create reply message
            reply_data = {
                "comment": reply_body
            }
            
            # Send as reply to the original message
            reply_url = f"{self.graph_endpoint}/users/{self.user_email}/messages/{message_id}/reply"
            
            response = requests.post(reply_url, headers=headers, json=reply_data)
            response.raise_for_status()
            
            print(f"✅ Confirmation email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send reply email: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the Graph API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            print(f"🔍 Testing Microsoft Graph API connection...")
            print(f"📧 User: {self.user_email}")
            print(f"🔑 Client ID: {self.client_id[:8]}...")
            
            access_token = self.get_access_token()
            if not access_token:
                return False
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Test by getting user profile
            user_url = f"{self.graph_endpoint}/users/{self.user_email}"
            response = requests.get(user_url, headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            print(f"✅ Connection successful!")
            print(f"👤 Display Name: {user_data.get('displayName')}")
            print(f"📧 Email: {user_data.get('mail') or user_data.get('userPrincipalName')}")
            
            # Test mail folders access
            folders_url = f"{self.graph_endpoint}/users/{self.user_email}/mailFolders"
            response = requests.get(folders_url, headers=headers)
            response.raise_for_status()
            
            folders = response.json().get("value", [])
            folder_names = [f.get("displayName") for f in folders]
            print(f"📁 Available folders: {folder_names}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {str(e)}")
            return False
