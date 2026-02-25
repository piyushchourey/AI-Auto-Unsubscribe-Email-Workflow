import json
from typing import Dict
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
        
    def _initialize_llm(self):
        """Initialize the appropriate LLM provider"""
        if settings.llm_provider == "ollama":
            print(f"Using Ollama with model: {settings.ollama_model}")
            return OllamaLLM(
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
{
    "has_unsubscribe_intent": true or false,
    "confidence": "high" or "medium" or "low",
    "reasoning": "Clear and concise explanation of why the intent was classified this way."
}

Do not include any additional text outside the JSON.
"""
        
        return PromptTemplate(
            input_variables=["message_text"],
            template=template.strip()
        )
    
    async def detect_intent(self, message_text: str) -> UnsubscribeIntentResponse:
        """
        Detect if the message contains unsubscribe intent
        
        Args:
            message_text: The email message body text
            
        Returns:
            UnsubscribeIntentResponse with detection results
        """
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
            
            # Parse the JSON response
            result_cleaned = result_text.strip()
            
            # Try to extract JSON if there's extra text
            if not result_cleaned.startswith('{'):
                start_idx = result_cleaned.find('{')
                end_idx = result_cleaned.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    result_cleaned = result_cleaned[start_idx:end_idx + 1]
            
            parsed_result = json.loads(result_cleaned)
            
            return UnsubscribeIntentResponse(
                has_unsubscribe_intent=parsed_result.get("has_unsubscribe_intent", False),
                confidence=parsed_result.get("confidence", "low"),
                reasoning=parsed_result.get("reasoning", "")
            )
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {result}")
            print(f"Error: {e}")
            # Fallback: simple keyword matching
            return self._fallback_detection(message_text)
        except Exception as e:
            print(f"Error during intent detection: {e}")
            return self._fallback_detection(message_text)
    
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
