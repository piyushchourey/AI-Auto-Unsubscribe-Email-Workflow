import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from config import settings


class BrevoService:
    """Service for managing Brevo contact unsubscriptions"""
    
    def __init__(self):
        """Initialize Brevo API client"""
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.brevo_api_key
        self.api_instance = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    async def unsubscribe_contact(self, email: str) -> dict:
        """
        Unsubscribe/blacklist a contact in Brevo
        
        Args:
            email: Email address to unsubscribe
            
        Returns:
            dict with success status and details
        """
        try:
            # First, try to get the contact to see if it exists
            try:
                contact = self.api_instance.get_contact_info(email)
                contact_exists = True
            except ApiException as e:
                if e.status == 404:
                    contact_exists = False
                else:
                    raise
            
            # Update contact to blacklist them
            update_contact = sib_api_v3_sdk.UpdateContact(
                email_blacklisted=True
            )
            
            if contact_exists:
                # Update existing contact
                self.api_instance.update_contact(email, update_contact)
                return {
                    "success": True,
                    "message": f"Contact {email} has been blacklisted in Brevo",
                    "action": "updated"
                }
            else:
                # Create new contact and blacklist immediately
                create_contact = sib_api_v3_sdk.CreateContact(
                    email=email,
                    email_blacklisted=True,
                    update_enabled=True
                )
                self.api_instance.create_contact(create_contact)
                return {
                    "success": True,
                    "message": f"Contact {email} has been created and blacklisted in Brevo",
                    "action": "created"
                }
                
        except ApiException as e:
            error_msg = f"Brevo API error: {e.status} - {e.reason}"
            print(error_msg)
            if e.body:
                print(f"Error body: {e.body}")
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "error": str(e)
            }
