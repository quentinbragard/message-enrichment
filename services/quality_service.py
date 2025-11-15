# services/quality_service.py
"""
Quality analysis service
"""
import json
import re
from typing import Optional, Dict, List
from core import llm_client
from utils import PromptLoader
from domains.enums import QualityLevel
import logging

logger = logging.getLogger(__name__)


class QualityService:
    """Service for quality analysis"""
    
    def __init__(self):
        self.llm = llm_client
        self.prompt_loader = PromptLoader()
    
    async def analyze(
        self,
        content: str,
        assistant_response: Optional[str] = None
    ) -> Dict:
        """
        Analyze prompt quality
        """
        try:
            # Quick heuristics
            heuristics = self._analyze_heuristics(content, assistant_response)
            
            # Load prompt
            prompt_template = self.prompt_loader.load("quality_analysis.txt")
            
            # Detect clarification signals
            clarification_signals = self._detect_clarification(assistant_response)
            
            # Build prompt
            prompt = prompt_template.format(
                user_message=content[:2000],
                assistant_response=assistant_response[:2000] if assistant_response else "Not available",
                clarification_signals=clarification_signals
            )
            
            # Get LLM response
            response = await self.llm.complete(
                system_prompt="You are a prompt quality analyzer. Return only valid JSON.",
                user_message=prompt,
                temperature=0.1,
                max_tokens=400
            )
            
            # Parse and merge with heuristics
            result = self._parse_quality_response(response)
            result.update(heuristics)
            
            return result
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return self._get_default_quality()
    
    def _analyze_heuristics(self, content: str, assistant_response: Optional[str]) -> Dict:
        """Quick heuristic analysis"""
        # Check for role setting
        has_role = any(pattern in content.lower() for pattern in [
            "you are", "act as", "pretend", "imagine you",
            "tu es", "agis comme", "en tant que"
        ])
        
        # Check for context
        has_context = any(pattern in content.lower() for pattern in [
            "context:", "background:", "given that",
            "contexte:", "sachant que"
        ])
        
        # Check for clear goal
        has_goal = any(pattern in content.lower() for pattern in [
            "i want", "i need", "please help", "can you",
            "je veux", "j'ai besoin", "peux-tu"
        ])
        
        return {
            "has_clear_role": has_role,
            "has_context": has_context,
            "has_clear_goal": has_goal,
            "word_count": len(content.split()),
            "sentence_count": len(re.split(r'[.!?]+', content))
        }
    
    def _detect_clarification(self, assistant_response: Optional[str]) -> str:
        """Detect if assistant asked for clarification"""
        if not assistant_response:
            return "No assistant response available"
        
        clarification_patterns = [
            "could you clarify",
            "could you provide more",
            "what specifically",
            "can you elaborate",
            "do you mean",
            "which particular",
            "pouvez-vous préciser",
            "pourriez-vous clarifier"
        ]
        
        found_patterns = [p for p in clarification_patterns if p in assistant_response.lower()]
        
        if found_patterns:
            return f"Assistant asked for clarification: {', '.join(found_patterns)}"
        else:
            return "No clarification requested"
    
    def _parse_quality_response(self, response: str) -> Dict:
        """Parse LLM quality response"""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            # Parse JSON
            data = json.loads(response)
            
            return {
                "overall_score": float(data.get("overall_score", 5)),
                "quality_level": data.get("quality_level", "average"),
                "clarity_score": float(data.get("clarity_score", 5)),
                "specificity_score": float(data.get("specificity_score", 5)),
                "completeness_score": float(data.get("completeness_score", 5)),
                "needs_clarification": data.get("needs_clarification", False),
                "ambiguity_level": data.get("ambiguity_level", "medium"),
                "missing_elements": data.get("missing_elements", []),
                "improvement_suggestions": data.get("improvement_suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to parse quality response: {e}")
            return self._get_default_quality()
    
    def _get_default_quality(self) -> Dict:
        """Get default quality analysis"""
        return {
            "overall_score": 5.0,
            "quality_level": "average",
            "clarity_score": 5.0,
            "specificity_score": 5.0,
            "completeness_score": 5.0,
            "needs_clarification": False,
            "ambiguity_level": "medium",
            "missing_elements": [],
            "improvement_suggestions": []
        }