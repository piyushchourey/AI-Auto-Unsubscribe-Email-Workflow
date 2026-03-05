"""Protected unsubscribe endpoints: inbound email, test Brevo, test intent."""
from fastapi import APIRouter, Request, HTTPException, status

from config import settings
from core.dependencies import RequireOperator
from models import InboundEmailRequest, UnsubscribeResponse, TestBrevoRequest
from services.email_sender import EmailSender
from services.graph_email_fetcher import GraphEmailFetcher
from services.activity_service import ActivityService

router = APIRouter(tags=["unsubscribe"])


@router.post("/inbound-email", response_model=UnsubscribeResponse, status_code=status.HTTP_200_OK)
async def process_inbound_email(
    body: InboundEmailRequest,
    request: Request,
    current_user: RequireOperator,
):
    """Process inbound email: detect unsubscribe intent and optionally unsubscribe in Brevo. Requires operator or admin."""
    intent_detector = request.app.state.intent_detector
    brevo_service = request.app.state.brevo_service
    db_service = request.app.state.db_service
    activity: ActivityService = request.app.state.activity_service

    try:
        print(f"\n📧 Processing email from: {body.sender_email}")
        print(f"📝 Message preview: {body.message_text[:100]}...")

        intent_result = await intent_detector.detect_intent(body.message_text)
        print(f"🎯 Intent detected: {intent_result.has_unsubscribe_intent}")

        unsubscribed_from_brevo = False
        brevo_details = None
        reply_sent = False

        if intent_result.has_unsubscribe_intent:
            print("🚫 Unsubscribe intent detected! Processing with Brevo...")
            brevo_result = await brevo_service.unsubscribe_contact(body.sender_email)
            unsubscribed_from_brevo = brevo_result["success"]
            brevo_details = brevo_result

            if brevo_result["success"]:
                print(f"✅ Successfully unsubscribed {body.sender_email} from Brevo")
                if settings.send_confirmation_email:
                    try:
                        if settings.use_graph_api:
                            message_id = getattr(body, "message_id", None)
                            if message_id:
                                fetcher = GraphEmailFetcher()
                                reply_sent = await fetcher.send_reply_email(
                                    message_id=message_id,
                                    recipient_email=body.sender_email,
                                    subject=body.subject or "",
                                )
                            else:
                                sender = EmailSender()
                                reply_sent = await sender.send_unsubscribe_confirmation(
                                    to_email=body.sender_email,
                                    original_subject=body.subject or "",
                                )
                        else:
                            sender = EmailSender()
                            reply_sent = await sender.send_unsubscribe_confirmation(
                                to_email=body.sender_email,
                                original_subject=body.subject or "",
                            )
                    except Exception as e:
                        print(f"❌ Failed to send confirmation email: {e}")
            else:
                print(f"⚠️ Failed to unsubscribe from Brevo: {brevo_result['message']}")
        else:
            print("ℹ️ No unsubscribe intent detected - no action taken")

        try:
            db_service.log_unsubscribe_action(
                email=body.sender_email,
                intent_detected=intent_result.has_unsubscribe_intent,
                brevo_success=unsubscribed_from_brevo,
                intent_confidence=intent_result.confidence,
                intent_reasoning=intent_result.reasoning,
                brevo_action=brevo_details.get("action") if brevo_details else None,
                brevo_message=brevo_details.get("message") if brevo_details else None,
                email_subject=body.subject,
                message_text=body.message_text,
                source="webhook",
                performed_by_user_id=current_user.id,
            )
        except Exception as db_error:
            print(f"⚠️ Database logging failed: {str(db_error)}")

        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="process_inbound_email",
            resource="inbound_email",
            details={
                "sender_email": body.sender_email,
                "intent_detected": intent_result.has_unsubscribe_intent,
                "brevo_success": unsubscribed_from_brevo,
            },
            ip_address=ip,
        )

        return UnsubscribeResponse(
            success=True,
            message="Email processed successfully",
            sender_email=body.sender_email,
            unsubscribe_intent_detected=intent_result.has_unsubscribe_intent,
            unsubscribed_from_brevo=unsubscribed_from_brevo,
            details={
                "intent_confidence": intent_result.confidence,
                "intent_reasoning": intent_result.reasoning,
                "brevo_result": brevo_details,
                "reply_sent": reply_sent,
            },
        )
    except Exception as e:
        print(f"❌ Error processing email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing email",
        )


@router.post("/test-brevo")
async def test_brevo(
    body: TestBrevoRequest,
    request: Request,
    current_user: RequireOperator,
):
    """Test Brevo blacklist for an email. Requires operator or admin."""
    brevo_service = request.app.state.brevo_service
    activity: ActivityService = request.app.state.activity_service

    try:
        print(f"\n🧪 Testing Brevo API for: {body.email}")
        result = await brevo_service.unsubscribe_contact(body.email)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="test_brevo",
            resource="brevo",
            details={"email": body.email, "success": result["success"]},
            ip_address=ip,
        )
        return {
            "success": result["success"],
            "email": body.email,
            "message": result["message"],
            "action": result.get("action", "unknown"),
            "details": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing Brevo API",
        )


@router.post("/test-intent")
async def test_intent_detection(
    body: InboundEmailRequest,
    request: Request,
    current_user: RequireOperator,
):
    """Test intent detection without triggering Brevo. Requires operator or admin."""
    intent_detector = request.app.state.intent_detector
    activity: ActivityService = request.app.state.activity_service

    try:
        intent_result = await intent_detector.detect_intent(body.message_text)
        ip = request.client.host if request.client else None
        activity.log(
            user_id=current_user.id,
            action="test_intent",
            resource="intent",
            details={"has_intent": intent_result.has_unsubscribe_intent},
            ip_address=ip,
        )
        return {
            "message_text": body.message_text,
            "has_unsubscribe_intent": intent_result.has_unsubscribe_intent,
            "confidence": intent_result.confidence,
            "reasoning": intent_result.reasoning,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error testing intent detection",
        )
