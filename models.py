from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class InboundEmailRequest(BaseModel):
    """Model for incoming email webhook from Outlook Power Automate"""
    sender_email: EmailStr = Field(..., description="Email address of the sender")
    message_text: str = Field(..., description="Body text of the email message")
    subject: Optional[str] = Field(None, description="Email subject (optional)")


class TestBrevoRequest(BaseModel):
    """Model for testing Brevo API blacklisting"""
    email: EmailStr = Field(..., description="Email address to blacklist")


class UnsubscribeIntentResponse(BaseModel):
    """Response model for intent detection"""
    has_unsubscribe_intent: bool = Field(..., description="Whether unsubscribe intent was detected")
    confidence: str = Field(..., description="Confidence level: high, medium, low")
    reasoning: Optional[str] = Field(None, description="Explanation of the decision")


class UnsubscribeResponse(BaseModel):
    """Response model for the unsubscribe endpoint"""
    success: bool
    message: str
    sender_email: str
    unsubscribe_intent_detected: bool
    unsubscribed_from_brevo: bool = False
    details: Optional[dict] = None
