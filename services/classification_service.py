# services/classification_service.py - With detailed logging
"""
Classification service with comprehensive logging
"""
import json
from typing import Optional, Dict, List
from core import llm_client
from utils import PromptLoader
import logging

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for message classification with detailed logging"""
    
    def __init__(self):
        self.llm = llm_client
        self.prompt_loader = PromptLoader()
        logger.info("ClassificationService initialized")
    
    async def classify(
        self,
        content: str,
        assistant_response: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Perform unified classification with detailed logging
        """
        logger.info("\n" + "="*50)
        logger.info("STARTING CLASSIFICATION")
        logger.info("="*50)
        logger.info(f"Content length: {len(content)} chars")
        logger.info(f"Has assistant response: {bool(assistant_response)}")
        logger.info(f"Has conversation history: {bool(conversation_history)}")
        
        try:
            # Load prompt template
            logger.debug("Loading prompt template...")
            prompt_template = self.prompt_loader.load("unified_classification.txt")
            logger.debug(f"Prompt template loaded, length: {len(prompt_template)} chars")
            
            # Format conversation history
            history_text = self._format_history(conversation_history)
            logger.debug(f"Formatted history: {history_text[:200]}...")
            
            # Build prompt
            logger.debug("Building prompt...")
            prompt = prompt_template.format(
                user_message=content[:2000],
                assistant_response=assistant_response[:2000] if assistant_response else "Not available",
                conversation_history=history_text
            )
            logger.debug(f"Final prompt length: {len(prompt)} chars")
            
            # Call LLM
            logger.info("Calling LLM for classification...")
            response = await self.llm.complete(
                system_prompt="You are a message classifier. Analyze the message and return classification results as valid JSON.",
                user_message=prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            logger.info(f"LLM response received, length: {len(response)} chars")
            logger.debug(f"Raw LLM response:\n{response}")
            
            # Parse response
            logger.debug("Parsing classification response...")
            result = self._parse_classification(response)
            
            logger.info("✅ Classification completed successfully")
            logger.debug(f"Classification result: {json.dumps(result, indent=2)[:500]}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Classification failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return self._get_default_classification()
    
    def _parse_classification(self, response: str) -> Dict:
        """Parse LLM response with detailed logging"""
        logger.debug("="*40)
        logger.debug("PARSING CLASSIFICATION RESPONSE")
        logger.debug("="*40)
        
        try:
            # Log the raw response
            logger.debug(f"Raw response to parse:\n{response}")
            
            # Clean response
            response = response.strip()
            logger.debug(f"After strip: {response[:100]}...")
            
            # Parse JSON
            logger.debug("Attempting JSON parse...")
            data = json.loads(response)
            logger.debug(f"Successfully parsed JSON")
            logger.debug(f"JSON keys: {list(data.keys())}")
            
            # Extract and validate each component
            work = data.get("work", {})
            logger.debug(f"Work classification: {work}")
            
            topic = data.get("topic", {})
            logger.debug(f"Topic classification: {topic}")
            
            intent = data.get("intent", {})
            logger.debug(f"Intent classification: {intent}")
            
            result = {
                "work": self._validate_work(work),
                "topic": self._validate_topic(topic),
                "intent": self._validate_intent(intent)
            }
            
            logger.debug("Classification parsing completed successfully")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            logger.error(f"Failed content:\n{response}")
            return self._get_default_classification()
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            return self._get_default_classification()
    
    def _validate_work(self, work_data: Dict) -> Dict:
        """Validate and fill work classification"""
        return {
            "is_work": work_data.get("is_work", False),
            "work_type": work_data.get("work_type"),
            "confidence": work_data.get("confidence", "low"),
            "reasoning": work_data.get("reasoning", ""),
            "signals": work_data.get("signals", [])
        }
    
    def _validate_topic(self, topic_data: Dict) -> Dict:
        """Validate and fill topic classification"""
        return {
            "primary": topic_data.get("primary", "OTHER"),
            "sub_topics": topic_data.get("sub_topics", []),
            "confidence": topic_data.get("confidence", "low"),
            "keywords": topic_data.get("keywords", [])
        }
    
    def _validate_intent(self, intent_data: Dict) -> Dict:
        """Validate and fill intent classification"""
        return {
            "primary": intent_data.get("primary", "EXPRESSING"),
            "detailed": intent_data.get("detailed", "unknown"),
            "confidence": intent_data.get("confidence", "low"),
            "used_assistant_response": intent_data.get("used_assistant_response", False)
        }
    
    def _get_default_classification(self) -> Dict:
        """Get default classification for errors"""
        logger.debug("Returning default classification due to error")
        return {
            "work": {
                "is_work": False,
                "work_type": None,
                "confidence": "low",
                "reasoning": "Classification failed",
                "signals": []
            },
            "topic": {
                "primary": "OTHER",
                "sub_topics": [],
                "confidence": "low",
                "keywords": []
            },
            "intent": {
                "primary": "EXPRESSING",
                "detailed": "unknown",
                "confidence": "low",
                "used_assistant_response": False
            }
        }
    
    def _format_history(self, history: Optional[List[Dict]]) -> str:
        """Format conversation history"""
        if not history:
            return "No previous messages"
        
        formatted = []
        for msg in history[-3:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)