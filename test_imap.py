#!/usr/bin/env python
"""
IMAP Connection Diagnostic Tool
Run this to test your IMAP connection and diagnose issues
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from imapclient import IMAPClient
import imaplib

def test_connection_detailed():
    """Test IMAP connection with detailed diagnostics"""
    
    print("="*60)
    print("IMAP CONNECTION DIAGNOSTIC TOOL")
    print("="*60)
    
    # Display configuration
    print("\n📋 Configuration:")
    print(f"  Provider: {settings.imap_provider.upper()}")
    print(f"  Host: {settings.imap_host}")
    print(f"  Port: {settings.imap_port}")
    print(f"  Email: {settings.imap_email}")
    print(f"  Password: {'*' * len(settings.imap_password) if settings.imap_password else '(NOT SET)'}")
    print(f"  Folder: {settings.imap_folder}")
    
    if not settings.imap_email or not settings.imap_password:
        print("\n❌ ERROR: Email or password not configured in .env file")
        return False
    
    # Test 1: Check if host is reachable
    print("\n🔍 Test 1: Checking server reachability...")
    
    imap_host = settings.imap_host
    imap_port = settings.imap_port
    
    if not imap_host:
        print(f"  ❌ No IMAP host configured for provider: {settings.imap_provider}")
        print("  💡 Set IMAP_HOST in .env or choose a different provider")
        return False
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((imap_host, imap_port))
        sock.close()
        
        if result == 0:
            print("  ✅ Server is reachable")
        else:
            print(f"  ❌ Cannot reach server (error code: {result})")
            print("  💡 Check your internet connection or firewall")
            
            if settings.imap_provider == 'rediff':
                print("\n  ⚠️  IMPORTANT: Rediff Mail IMAP Support Issue")
                print("     Rediff Mail does NOT support IMAP on most accounts:")
                print("     - Free accounts: Usually NO IMAP access")
                print("     - Paid accounts: May have IMAP (verify in settings)")
                print("\n  ✅ RECOMMENDED SOLUTION: Use Webhook Mode")
                print("     1. Set IMAP_ENABLED=false in .env")
                print("     2. Use Power Automate to forward emails to API")
                print("     3. See README.md for webhook setup")
                print("\n  📧 Alternative: Use Gmail, Outlook, or Yahoo instead")
            
            return False
            return False
    except Exception as e:
        print(f"  ❌ Error checking reachability: {e}")
        print("  💡 Possible issues:")
        print("     - DNS resolution failed (hostname not found)")
        print("     - No internet connection")
        print("     - Firewall blocking access")
        
        if 'getaddrinfo failed' in str(e):
            print(f"\n  🔍 DNS Issue: Cannot resolve '{imap_host}'")
            print("  💡 Troubleshooting:")
            print("     1. Check your internet connection")
            print("     2. Try pinging the server: ping " + imap_host)
            print("     3. Check if the hostname is correct")
            
            # Suggest alternatives for common providers
            if settings.imap_provider == 'rediff':
                print("\n  📌 Rediff Mail IMAP Options:")
                print("     - Try: mail.rediff.com (current)")
                print("     - OR: imap.rediffmail.com (alternative)")
                print("     - Update IMAP_HOST in .env if needed")
                print("\n  ⚠️  Note: Rediff may have limited IMAP support")
                print("     Consider using Webhook mode instead:")
                print("     Set IMAP_ENABLED=false in .env")
        
        return False
    
    # Test 2: Try to connect with SSL
    print("\n🔍 Test 2: Attempting SSL connection...")
    try:
        client = IMAPClient(imap_host, port=imap_port, ssl=True)
        print("  ✅ SSL connection established")
        
        # Test 3: Try to login
        print("\n🔍 Test 3: Attempting login...")
        try:
            client.login(settings.imap_email, settings.imap_password)
            print("  ✅ Login successful!")
            
            # Test 4: List folders
            print("\n🔍 Test 4: Listing available folders...")
            folders = client.list_folders()
            print("  ✅ Available folders:")
            for flags, delimiter, folder_name in folders:
                print(f"    - {folder_name}")
            
            # Test 5: Select inbox
            print(f"\n🔍 Test 5: Selecting folder '{settings.imap_folder}'...")
            try:
                client.select_folder(settings.imap_folder)
                print(f"  ✅ Successfully selected {settings.imap_folder}")
                
                # Check for unread messages
                messages = client.search('UNSEEN')
                print(f"  📧 Found {len(messages)} unread messages")
                
            except Exception as e:
                print(f"  ❌ Error selecting folder: {e}")
                print("  💡 Make sure the folder name is correct")
            
            client.logout()
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED! Your IMAP configuration is working!")
            print("="*60)
            return True
            
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            print(f"  ❌ Login failed: {error_msg}")
            print("\n" + "="*60)
            print("❌ LOGIN FAILED - TROUBLESHOOTING STEPS:")
            print("="*60)
            
            provider = settings.imap_provider.lower()
            
            if 'LOGIN failed' in error_msg or 'authentication failed' in error_msg.lower():
                print(f"\n🔑 AUTHENTICATION ISSUE for {provider.upper()} - Try these solutions:\n")
                
                if provider == 'outlook' or '@outlook.com' in settings.imap_email or '@hotmail.com' in settings.imap_email:
                    print("📌 For Personal Outlook/Hotmail accounts:")
                    print("  1. Go to: https://account.microsoft.com/security")
                    print("  2. Enable 'Two-step verification'")
                    print("  3. Click 'Advanced security options'")
                    print("  4. Scroll to 'App passwords' and generate one")
                    print("  5. Use the generated App Password (not your regular password)")
                    print("     in IMAP_PASSWORD in .env file\n")
                
                elif provider == 'gmail' or '@gmail.com' in settings.imap_email:
                    print("📌 For Gmail accounts:")
                    print("  1. Go to: https://myaccount.google.com/security")
                    print("  2. Enable 'Two-step verification'")
                    print("  3. Go to: https://myaccount.google.com/apppasswords")
                    print("  4. Select 'Mail' and your device")
                    print("  5. Generate an App Password")
                    print("  6. Use the 16-character App Password in IMAP_PASSWORD\n")
                    print("  📌 Also enable IMAP in Gmail:")
                    print("     Settings → Forwarding and POP/IMAP → Enable IMAP\n")
                
                elif provider == 'rediff' or '@rediffmail.com' in settings.imap_email:
                    print("📌 For Rediff Mail accounts:")
                    print("  1. Log in to Rediffmail.com")
                    print("  2. Use your regular email password (Rediff doesn't use App Passwords)")
                    print("  3. Make sure IMAP is enabled:")
                    print("     - Settings → Accounts → Enable IMAP Access")
                    print("  4. If still failing, try:")
                    print("     - Verify email/password are correct")
                    print("     - Check if account requires verification")
                    print("     - Contact Rediff support if issues persist\n")
                
                elif provider == 'yahoo' or '@yahoo.com' in settings.imap_email:
                    print("📌 For Yahoo Mail accounts:")
                    print("  1. Go to: https://login.yahoo.com/account/security")
                    print("  2. Turn on 'Two-step verification'")
                    print("  3. Click 'Generate app password'")
                    print("  4. Select 'Mail' from the dropdown")
                    print("  5. Generate and copy the password")
                    print("  6. Use this App Password in IMAP_PASSWORD\n")
                
                else:
                    print("📌 For Work/School accounts (@company.com):")
                    print("  1. Your organization might have disabled IMAP access")
                    print("  2. Contact your IT administrator to enable IMAP")
                    print("  3. Some organizations require OAuth instead of passwords")
                    print("  4. Alternative: Use Power Automate webhook mode instead\n")
                    
                print("📌 Common Issues:")
                print("  ❌ Using regular password instead of App Password")
                print("  ❌ App Password not generated correctly")
                print("  ❌ Copy-paste error (spaces in password)")
                print("  ❌ IMAP not enabled in account settings")
                print("  ❌ Account has 2FA but no App Password created")
                
                print("\n📌 How to enable IMAP in Outlook:")
                print("  1. Go to Outlook.com settings (gear icon)")
                print("  2. View all Outlook settings")
                print("  3. Mail → Sync email")
                print("  4. Under 'POP and IMAP', enable IMAP")
                print("  5. Save changes and try again")
                
            return False
            
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        print("\n💡 Possible issues:")
        
        error_str = str(e)
        
        if 'WinError 10013' in error_str or 'access permissions' in error_str.lower():
            print("\n🔥 WINDOWS FIREWALL BLOCKING CONNECTION")
            print("=" * 60)
            print("Error: Windows is blocking access to port 993")
            print("\n✅ SOLUTIONS (try in order):\n")
            
            print("1️⃣  Allow Python through Windows Firewall:")
            print("   - Open 'Windows Defender Firewall'")
            print("   - Click 'Allow an app through firewall'")
            print("   - Click 'Change settings' (may need admin)")
            print("   - Find 'Python' in the list")
            print("   - Check BOTH 'Private' and 'Public' boxes")
            print("   - Click OK\n")
            
            print("2️⃣  Run PowerShell as Administrator and execute:")
            print("   New-NetFirewallRule -DisplayName 'Python IMAP' -Direction Outbound -Program 'C:\\Path\\To\\python.exe' -Action Allow -Protocol TCP -RemotePort 993\n")
            
            print("3️⃣  Temporarily disable firewall to test:")
            print("   - Windows Security → Firewall & network protection")
            print("   - Turn off firewall temporarily")
            print("   - Run test_imap.py again")
            print("   - Turn firewall back on\n")
            
            print("4️⃣  Check antivirus software:")
            print("   - Some antivirus block IMAP/SSL connections")
            print("   - Temporarily disable or add Python to whitelist\n")
            
            print("5️⃣  Try a different network:")
            print("   - Corporate networks may block IMAP")
            print("   - Try from home network or mobile hotspot\n")
            
        elif 'certificate' in error_str.lower() or 'ssl' in error_str.lower():
            print("  - SSL certificate verification issue")
            print("  - Update certificates: pip install --upgrade certifi")
            print("  - Check system date/time is correct")
            
        else:
            print("  - Firewall blocking connection")
            print("  - Incorrect host/port")
            print("  - Network connectivity issue")
        
        return False

if __name__ == "__main__":
    print("\n🔧 Starting IMAP diagnostics...\n")
    success = test_connection_detailed()
    sys.exit(0 if success else 1)
