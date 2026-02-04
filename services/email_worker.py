import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from config import settings
from services.email_fetcher import EmailFetcher
from services.intent_detector import IntentDetector
from services.brevo_service import BrevoService


class EmailWorker:
    """Background worker that processes emails from IMAP mailbox every hour"""
    
    def __init__(self, intent_detector: IntentDetector, brevo_service: BrevoService, db_service=None):
        """
        Initialize the email worker
        
        Args:
            intent_detector: Intent detection service
            brevo_service: Brevo API service
            db_service: Database service for logging (optional)
        """
        self.email_fetcher = EmailFetcher()
        self.intent_detector = intent_detector
        self.brevo_service = brevo_service
        self.db_service = db_service
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    async def process_email(self, email_data: dict) -> dict:
        """
        Process a single email for unsubscribe intent
        
        Args:
            email_data: Dictionary with sender_email, message_text, subject
            
        Returns:
            Processing result dictionary
        """
        sender_email = email_data['sender_email']
        message_text = email_data['message_text']
        subject = email_data.get('subject', '')
        
        print(f"\n📧 Processing email from: {sender_email}")
        print(f"📄 Subject: {subject}")
        print(f"📝 Message preview: {message_text[:100]}...")
        
        result = {
            'sender_email': sender_email,
            'subject': subject,
            'unsubscribe_intent_detected': False,
            'unsubscribed_from_brevo': False,
            'error': None
        }
        
        try:
            # Step 1: Detect unsubscribe intent
            print("🤖 Analyzing intent with LLM...")
            intent_result = await self.intent_detector.detect_intent(message_text)
            
            result['unsubscribe_intent_detected'] = intent_result.has_unsubscribe_intent
            result['confidence'] = intent_result.confidence
            result['reasoning'] = intent_result.reasoning
            
            print(f"🎯 Intent detected: {intent_result.has_unsubscribe_intent}")
            print(f"🎲 Confidence: {intent_result.confidence}")
            print(f"💭 Reasoning: {intent_result.reasoning}")

            # Step 2: Process with Brevo if unsubscribe intent detected
            if intent_result.has_unsubscribe_intent:
                print(f"🚫 Unsubscribe intent detected! Processing with Brevo...")
                brevo_result = await self.brevo_service.unsubscribe_contact(sender_email)
                
                result['unsubscribed_from_brevo'] = brevo_result['success']
                result['brevo_details'] = brevo_result
                
                if brevo_result['success']:
                    print(f"✅ Successfully unsubscribed {sender_email} from Brevo")
                else:
                    print(f"⚠️ Failed to unsubscribe from Brevo: {brevo_result['message']}")
            else:
                print(f"ℹ️ No unsubscribe intent detected - no action taken")
            
            # Step 3: Log to database
            if self.db_service:
                try:
                    self.db_service.log_unsubscribe_action(
                        email=sender_email,
                        intent_detected=intent_result.has_unsubscribe_intent,
                        brevo_success=result.get('unsubscribed_from_brevo', False),
                        intent_confidence=intent_result.confidence,
                        intent_reasoning=intent_result.reasoning,
                        brevo_action=result.get('brevo_details', {}).get('action') if result.get('brevo_details') else None,
                        brevo_message=result.get('brevo_details', {}).get('message') if result.get('brevo_details') else None,
                        email_subject=subject,
                        message_text=message_text,
                        source="worker"
                    )
                except Exception as db_error:
                    print(f"⚠️ Database logging failed: {str(db_error)}")
        
        except Exception as e:
            error_msg = f"Error processing email: {str(e)}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
        
        return result
    
    async def check_emails(self):
        """
        Main job function: Fetch emails from IMAP and process them
        This runs on the configured schedule
        """
        if not settings.imap_enabled:
            print("⏭️ IMAP worker is disabled in configuration")
            return
        
        print(f"\n{'='*60}")
        print(f"🔄 EMAIL WORKER RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            # Fetch unread emails
            emails = await self.email_fetcher.fetch_unread_emails()
            
            if not emails:
                print("📭 No unread emails to process")
                return
            
            print(f"\n🔍 Processing {len(emails)} emails...")
            
            # Process each email
            results = []
            for email_data in emails:
                result = await self.process_email(email_data)
                results.append(result)
                
                # Small delay between processing emails
                await asyncio.sleep(1)
            
            # Summary
            print(f"\n{'='*60}")
            print(f"📊 PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"Total emails processed: {len(results)}")
            print(f"Unsubscribe intents detected: {sum(1 for r in results if r['unsubscribe_intent_detected'])}")
            print(f"Successfully unsubscribed from Brevo: {sum(1 for r in results if r['unsubscribed_from_brevo'])}")
            print(f"Errors: {sum(1 for r in results if r.get('error'))}")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ Error in email worker: {str(e)}")
    
    async def start(self):
        """Start the background worker scheduler"""
        if self.is_running:
            print("⚠️ Email worker is already running")
            return
        
        if not settings.imap_enabled:
            print("⏭️ IMAP worker is disabled - skipping scheduler start")
            return
        
        print(f"\n🚀 Starting email worker...")
        print(f"⏰ Check interval: {settings.imap_check_interval} seconds ({settings.imap_check_interval / 3600:.1f} hours)")
        print(f"📧 Monitoring: {settings.imap_email}")
        print(f"📂 Folder: {settings.imap_folder}")
        
        # Test IMAP connection first
        try:
            connection_ok = await self.email_fetcher.test_connection()
            if not connection_ok:
                print("❌ IMAP connection test failed - worker will not start")
                return
        except Exception as e:
            print(f"❌ IMAP connection test failed: {e}")
            print("⚠️ Worker will continue but may fail when checking emails")
        
        # Add job to scheduler
        self.scheduler.add_job(
            self.check_emails,
            trigger=IntervalTrigger(seconds=settings.imap_check_interval),
            id='email_check_job',
            name='Check emails for unsubscribe requests',
            replace_existing=True
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        print(f"✅ Email worker started successfully!")
        print(f"⏰ Next check at: {self.scheduler.get_jobs()[0].next_run_time}")
        
        # Run immediately on startup
        print(f"\n🏃 Running initial email check...")
        await self.check_emails()
    
    async def stop(self):
        """Stop the background worker scheduler"""
        if not self.is_running:
            return
        
        print("\n🛑 Stopping email worker...")
        self.scheduler.shutdown()
        self.is_running = False
        print("✅ Email worker stopped")
    
    def get_status(self) -> dict:
        """Get current worker status"""
        if not self.is_running or not settings.imap_enabled:
            return {
                'running': False,
                'enabled': settings.imap_enabled
            }
        
        jobs = self.scheduler.get_jobs()
        next_run = jobs[0].next_run_time if jobs else None
        
        return {
            'running': True,
            'enabled': settings.imap_enabled,
            'check_interval_seconds': settings.imap_check_interval,
            'next_run': next_run.isoformat() if next_run else None,
            'monitoring_email': settings.imap_email,
            'monitoring_folder': settings.imap_folder
        }
