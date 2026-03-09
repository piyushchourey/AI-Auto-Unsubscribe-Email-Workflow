import json
import re
from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from models import UnsubscribeIntentResponse


class IntentDetector:
    """Detects unsubscribe intent in email messages using LLM"""
    
    def __init__(self):
        """Initialize the LLM based on configuration"""
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        self.undelivered_subject_prompt = self._create_undelivered_subject_prompt()
        
    def _initialize_llm(self):
        """Initialize the appropriate LLM provider"""
        if settings.llm_provider == "ollama":
            print(f"Using Ollama with model: {settings.ollama_model} and base url: {settings.ollama_base_url}")
            return OllamaLLM(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=0,
                top_p=1,
                repeat_penalty=1.05
            )
        elif settings.llm_provider == "gemini":
            print(f"Using Gemini with model: {settings.gemini_model}")
            return ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.1,
                convert_system_message_to_human=True
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for intent detection"""
        template = """
You are a highly accurate email intent classification system.

Your task is to determine whether the sender is requesting to unsubscribe 
or expressing that they do not want to receive marketing emails anymore.

IMPORTANT:
- Focus on the sender's intent, not just keywords.
- The request may be direct or indirect.
- The sender may be polite, angry, sarcastic, or subtle.
- Questions about how to unsubscribe DO count as unsubscribe intent.
- Complaints alone DO NOT count unless they clearly imply stopping emails.
- Ignore signatures, disclaimers, and quoted previous emails.
- Be conservative in your decision.

CRITICAL RULE:
If you are not confident that the sender clearly wants to unsubscribe,
you MUST classify it as FALSE.

Classify as TRUE only if the unsubscribe intent is clear and explicit.

Email Message:
----------------
{message_text}
----------------

Respond ONLY with valid JSON in this exact format:
{{
    "has_unsubscribe_intent": true or false,
    "confidence": "high" or "medium" or "low",
    "reasoning": "Clear and concise explanation of why the intent was classified this way."
}}

Do not include any additional text outside the JSON.
"""
        
        return PromptTemplate(
            input_variables=["message_text"],
            template=template.strip()
        )

    def _create_undelivered_subject_prompt(self) -> PromptTemplate:
        """Create prompt for detecting undelivered/bounce/delay from subject line only."""
        template = """
You are an email subject classifier. Your task is to decide if an email SUBJECT LINE
indicates that the message is about undelivered mail, delivery failure, bounce, or delivery status (delay/unsuccessful).

Examples of subjects that SHOULD be classified as undelivered/delivery-failure:
- "Not delivered"
- "[SUSPECTIVE] Unfulfilled: [External]"
- "Failure to Deliver Emails"
- "Failure to Deliver Messages"
- "Notification of the Delivery Status (Delay)"
- "Notification of Delivery Status (Unsuccessful)"
- "Delivery has failed"
- "Undeliverable message"
- "Mail delivery failed"
- "Returned mail: see transcript for details"
- Any similar phrasing about non-delivery, bounce, delay, failure notice, bounce notice or delivery status.

Classify as TRUE only if the subject clearly indicates undelivered mail / delivery failure / bounce / delay notice.
Classify as FALSE for normal subjects (newsletters, receipts, conversations, etc.).

Subject line to classify:
----------------
{subject}
----------------

Respond ONLY with valid JSON in this exact format:
{{
    "has_undelivered_sentiment": true or false,
    "confidence": "high" or "medium" or "low",
    "reasoning": "Brief explanation."
}}

Do not include any additional text outside the JSON.
"""
        return PromptTemplate(
            input_variables=["subject"],
            template=template.strip()
        )

    def _parse_undelivered_json(self, raw: str) -> Optional[Dict]:
        """Parse LLM response for undelivered subject (has_undelivered_sentiment, confidence, reasoning)."""
        text = raw.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        for suffix in ('}', '"}', '"}\n}'):
            try:
                return json.loads(text + suffix)
            except json.JSONDecodeError:
                continue
        intent_match = re.search(
            r'"has_undelivered_sentiment"\s*:\s*(true|false)',
            text,
            re.IGNORECASE
        )
        confidence_match = re.search(
            r'"confidence"\s*:\s*"(high|medium|low)"',
            text,
            re.IGNORECASE
        )
        reasoning_match = re.search(
            r'"reasoning"\s*:\s*"((?:[^"\\]|\\.)*)',
            text,
            re.DOTALL
        )
        if intent_match:
            return {
                "has_undelivered_sentiment": intent_match.group(1).lower() == "true",
                "confidence": confidence_match.group(1).lower() if confidence_match else "low",
                "reasoning": (reasoning_match.group(1).replace('\\"', '"') if reasoning_match else "") or "",
            }
        return None

    # Fallback subject patterns when LLM is unavailable (same as in email_worker)
    _UNDELIVERED_SUBJECT_PATTERNS = (
        "not delivered",
        "[suspective] unfulfilled: [external]",
        "failure to deliver emails",
        "failure to deliver messages",
        "notification of the delivery status (delay)",
        "notification of delivery status (delay)",
        "notification of delivery status (unsuccessful)",
    )

    def _fallback_undelivered_subject(self, subject: str) -> bool:
        """Keyword fallback when LLM fails for subject classification."""
        if not subject or not subject.strip():
            return False
        lower = subject.strip().lower()
        return any(phrase in lower for phrase in self._UNDELIVERED_SUBJECT_PATTERNS)

    def _parse_llm_json(self, raw: str) -> Optional[Dict]:
        """
        Parse LLM JSON response, trying repair and regex extraction if needed.
        Returns dict with has_unsubscribe_intent, confidence, reasoning or None.
        """
        text = raw.strip()
        if not text:
            return None

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try repairing truncated JSON (missing closing " and/or })
        for suffix in ('}', '"}', '"}\n}'):
            try:
                return json.loads(text + suffix)
            except json.JSONDecodeError:
                continue

        # Try extracting fields with regex (handles truncated or malformed JSON)
        intent_match = re.search(
            r'"has_unsubscribe_intent"\s*:\s*(true|false)',
            text,
            re.IGNORECASE
        )
        confidence_match = re.search(
            r'"confidence"\s*:\s*"(high|medium|low)"',
            text,
            re.IGNORECASE
        )
        reasoning_match = re.search(
            r'"reasoning"\s*:\s*"((?:[^"\\]|\\.)*)',
            text,
            re.DOTALL
        )
        if intent_match:
            return {
                "has_unsubscribe_intent": intent_match.group(1).lower() == "true",
                "confidence": confidence_match.group(1).lower() if confidence_match else "low",
                "reasoning": (reasoning_match.group(1).replace("\\\"", '"') if reasoning_match else "") or "",
            }
        return None

    async def detect_intent(self, message_text: str) -> UnsubscribeIntentResponse:
        """
        Detect if the message contains unsubscribe intent
        
        Args:
            message_text: The email message body text
            
        Returns:
            UnsubscribeIntentResponse with detection results
        """
        result_text = ""
        try:
            # Format the prompt with the message text
            prompt = self.prompt_template.format(message_text=message_text)

            # Invoke the LLM
            result = await self.llm.ainvoke(prompt)

            # Handle different return types (string vs AIMessage)
            if hasattr(result, 'content'):
                result_text = result.content
            else:
                result_text = str(result)

            if result_text is None:
                result_text = ""
            
            # Parse the JSON response
            result_cleaned = result_text.strip()
            
            # Try to extract JSON if there's extra text
            if not result_cleaned.startswith('{'):
                start_idx = result_cleaned.find('{')
                end_idx = result_cleaned.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    result_cleaned = result_cleaned[start_idx:end_idx + 1]

            parsed_result = self._parse_llm_json(result_cleaned)
            if parsed_result is None:
                raise ValueError("Could not parse LLM response as JSON")
            if not isinstance(parsed_result.get("has_unsubscribe_intent"), bool):
                raise ValueError("missing or invalid has_unsubscribe_intent field")

            confidence_raw = parsed_result.get("confidence", "low")
            confidence = (
                confidence_raw
                if isinstance(confidence_raw, str) and confidence_raw in ("high", "medium", "low")
                else "low"
            )
            reasoning_raw = parsed_result.get("reasoning", "")
            reasoning = str(reasoning_raw) if reasoning_raw is not None else ""

            return UnsubscribeIntentResponse(
                has_unsubscribe_intent=parsed_result.get("has_unsubscribe_intent", False),
                confidence=confidence,
                reasoning=reasoning
            )

        except Exception as e:
            # Try repair/regex parse in case of truncated or malformed JSON
            result_cleaned = (result_text or "").strip()
            if not result_cleaned.startswith("{"):
                start_idx = result_cleaned.find("{")
                end_idx = result_cleaned.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    result_cleaned = result_cleaned[start_idx : end_idx + 1]
            parsed_result = self._parse_llm_json(result_cleaned) if result_cleaned else None
            if parsed_result and isinstance(parsed_result.get("has_unsubscribe_intent"), bool):
                confidence_raw = parsed_result.get("confidence", "low")
                confidence = (
                    confidence_raw
                    if isinstance(confidence_raw, str) and confidence_raw in ("high", "medium", "low")
                    else "low"
                )
                reasoning_raw = parsed_result.get("reasoning", "")
                reasoning = str(reasoning_raw) if reasoning_raw is not None else ""
                return UnsubscribeIntentResponse(
                    has_unsubscribe_intent=parsed_result.get("has_unsubscribe_intent", False),
                    confidence=confidence,
                    reasoning=reasoning or "Parsed from malformed JSON",
                )
            print("Error during intent detection:", e)
            print(result_text or "(response not available)")
            return self._fallback_detection(message_text)

    async def detect_undelivered_from_subject(self, subject: str) -> tuple[bool, str, str]:
        """
        Use LLM to detect if the subject line indicates undelivered/bounce/delay (subject-only sentiment).
        Returns (has_undelivered_sentiment, confidence, reasoning).
        Falls back to keyword matching if LLM fails.
        """
        if not subject or not subject.strip():
            return False, "low", "Empty subject"
        result_text = ""
        try:
            prompt = self.undelivered_subject_prompt.format(subject=subject.strip())
            result = await self.llm.ainvoke(prompt)
            if hasattr(result, "content"):
                result_text = result.content
            else:
                result_text = str(result)
            if result_text is None:
                result_text = ""
            text = result_text.strip()
            if not text.startswith("{"):
                start_idx = text.find("{")
                end_idx = text.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    text = text[start_idx : end_idx + 1]
            parsed = self._parse_undelivered_json(text)
            if parsed is not None and "has_undelivered_sentiment" in parsed:
                has_it = bool(parsed["has_undelivered_sentiment"])
                conf = parsed.get("confidence", "low")
                if conf not in ("high", "medium", "low"):
                    conf = "low"
                reason = str(parsed.get("reasoning", ""))
                return has_it, conf, reason or "LLM subject classification"
        except Exception as e:
            print("Error during undelivered subject detection:", e)
            print(result_text or "(no response)")
        # Fallback to keyword matching
        has_fallback = self._fallback_undelivered_subject(subject)
        return (
            has_fallback,
            "medium" if has_fallback else "low",
            "Fallback keyword matching used due to LLM error",
        )
    
    def _fallback_detection(self, message_text: str) -> UnsubscribeIntentResponse:
        """Fallback keyword-based detection if LLM fails"""
        unsubscribe_keywords = [
            "unsubscribe", "remove me", "stop emails", "stop sending",
            "take me off", "opt out", "cancel subscription", "no longer interested",
            "don't want to receive", "don't send", "stop contacting"
        ]
        
        message_lower = message_text.lower()
        has_intent = any(keyword in message_lower for keyword in unsubscribe_keywords)
        
        return UnsubscribeIntentResponse(
            has_unsubscribe_intent=has_intent,
            confidence="medium" if has_intent else "low",
            reasoning="Fallback keyword matching used due to LLM error"
        )
