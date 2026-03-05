"""
Test script for Microsoft Graph API connection
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.graph_email_fetcher import GraphEmailFetcher
from config import settings


async def test_graph_api():
    """Test Microsoft Graph API connection and email fetching"""
    
    print("="*60)
    print("Microsoft Graph API Connection Test")
    print("="*60)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    print(f"   USE_GRAPH_API: {settings.use_graph_api}")
    print(f"   Client ID: {settings.graph_client_id[:8] if settings.graph_client_id else 'NOT SET'}...")
    print(f"   Tenant ID: {settings.graph_tenant_id[:8] if settings.graph_tenant_id else 'NOT SET'}...")
    print(f"   Client Secret: {'SET' if settings.graph_client_secret else 'NOT SET'}")
    print(f"   Email: {settings.imap_email}")
    
    if not settings.use_graph_api:
        print("\n⚠️  USE_GRAPH_API is set to False")
        print("   Set USE_GRAPH_API=true in .env to enable Graph API")
        return
    
    if not all([settings.graph_client_id, settings.graph_client_secret, settings.graph_tenant_id]):
        print("\n❌ Missing Graph API configuration!")
        print("   Please set the following in .env:")
        print("   - GRAPH_CLIENT_ID")
        print("   - GRAPH_CLIENT_SECRET")
        print("   - GRAPH_TENANT_ID")
        print("\n   See GRAPH_API_SETUP.md for detailed instructions.")
        return
    
    print("\n" + "="*60)
    
    # Initialize fetcher
    try:
        fetcher = GraphEmailFetcher()
    except Exception as e:
        print(f"\n❌ Failed to initialize Graph API client: {str(e)}")
        return
    
    # Test connection
    print("\n1️⃣  Testing Connection...")
    print("-"*60)
    
    connection_ok = fetcher.test_connection()
    
    if not connection_ok:
        print("\n❌ Connection test failed!")
        print("\nTroubleshooting steps:")
        print("1. Verify Client ID, Client Secret, and Tenant ID in .env")
        print("2. Check that API permissions are granted in Azure Portal")
        print("3. Ensure admin consent is given for the permissions")
        print("4. Verify the email address exists in your organization")
        print("\nSee GRAPH_API_SETUP.md for detailed setup instructions.")
        return
    
    print("\n" + "="*60)
    
    # Test fetching emails
    print("\n2️⃣  Testing Email Fetch...")
    print("-"*60)
    
    try:
        emails = await fetcher.fetch_unread_emails()
        
        print(f"\n✅ Successfully fetched {len(emails)} unread emails")
        
        if emails:
            print("\n📧 Sample Email:")
            print("-"*60)
            email = emails[0]
            print(f"From: {email['sender_email']}")
            print(f"Subject: {email['subject']}")
            print(f"Preview: {email['message_text'][:100]}...")
        else:
            print("\n📭 No unread emails in the mailbox")
        
    except Exception as e:
        print(f"\n❌ Failed to fetch emails: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("\n✅ All tests passed!")
    print("\nYou can now start the main application:")
    print("   python main.py")
    print("\n" + "="*60)


if __name__ == "__main__":
    try:
        asyncio.run(test_graph_api())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
