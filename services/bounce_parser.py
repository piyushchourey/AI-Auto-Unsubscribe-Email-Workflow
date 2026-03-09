"""
Extract the failed recipient (actual user email) from bounce/undelivered message body.
Bounce emails are sent by MAILER-DAEMON etc.; the address we want to block is the one
that failed to receive (appears in the body), not the sender of the bounce.
"""
import re
from typing import Optional

# Common MIME/bounce headers and body patterns that contain the failed recipient
FAILED_RECIPIENT_PATTERNS = [
    # Final-Recipient: rfc822; user@example.com
    re.compile(r"Final-Recipient:\s*rfc822;\s*(\S+@\S+)", re.IGNORECASE),
    # Original-Recipient: rfc822; user@example.com
    re.compile(r"Original-Recipient:\s*rfc822;\s*(\S+@\S+)", re.IGNORECASE),
    # Failed Recipient: user@example.com
    re.compile(r"Failed\s+Recipient:\s*\S*(\S+@\S+)", re.IGNORECASE),
    # Delivery to <user@example.com> failed
    re.compile(r"Delivery\s+to\s*(?:<)?(\S+@\S+)(?:>)?\s*failed", re.IGNORECASE),
    # could not be delivered to: user@example.com
    re.compile(r"(?:could not be|cannot be)\s+delivered\s+to[:\s]*(?:<)?(\S+@\S+)", re.IGNORECASE),
    # Recipient: user@example.com (in failure context)
    re.compile(r"Recipient[:\s]+(?:<)?(\S+@\S+)(?:>)?", re.IGNORECASE),
    # "user@example.com" after "failed" or "undeliverable" on same or next line
    re.compile(r"(?:failed|undeliverable|invalid)[^\n]*?(\S+@\S+)", re.IGNORECASE),
]

# Basic email format (local@domain)
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Addresses we should not treat as "failed recipient" (bounce/system senders)
SYSTEM_ADDRESS_PATTERNS = (
    "postmaster",
    "mailer-daemon",
    "mail delivery",
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "bounce",
    "null@",
)


def _normalize_email(s: str) -> str:
    """Strip angle brackets and whitespace."""
    if not s:
        return ""
    return s.strip().strip("<>").strip().lower()


def _is_valid_user_email(email: str, bounce_sender: str) -> bool:
    """Return True if email looks like a real user address we should block, not a system address."""
    if not email or not EMAIL_RE.match(email):
        return False
    lower = email.lower()
    if _normalize_email(bounce_sender) and lower == _normalize_email(bounce_sender):
        return False
    for pattern in SYSTEM_ADDRESS_PATTERNS:
        if pattern in lower:
            return False
    return True


def extract_failed_recipient_from_bounce(
    body: str,
    subject: str = "",
    bounce_sender: str = "",
) -> Optional[str]:
    """
    Extract the failed recipient (actual user email) from a bounce/undelivered message.

    Args:
        body: Full message body text of the bounce.
        subject: Subject line (optional; can contain address in some bounces).
        bounce_sender: The From address of the bounce (e.g. MAILER-DAEMON). We exclude this.

    Returns:
        The extracted email to block, or None if not found / not valid.
    """
    if not body:
        body = ""
    text = (subject + "\n" + body).strip()
    if not text:
        return None

    for pattern in FAILED_RECIPIENT_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1).strip().strip(".,;:)")
            if not raw or len(raw) > 254:
                continue
            # Trim trailing punctuation that might have been captured
            email = re.sub(r"[.,;:)\]]+$", "", raw).strip()
            if _is_valid_user_email(email, bounce_sender):
                return email

    return None
