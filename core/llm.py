# core/llm.py - HuggingFace with detailed logging
"""
LLM client using HuggingFace API with comprehensive logging
"""
from typing import Optional
from config import settings
import logging
import json
import os
import httpx
import traceback

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client using HuggingFace Inference API with detailed logging"""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or "mistralai/Mistral-7B-Instruct-v0.2"
        self.api_key = os.getenv("HF_TOKEN") or settings.HF_TOKEN
        
        # HuggingFace Inference API endpoint
        self.base_url = f"https://router.huggingface.co/hf-inference/models/{self.model}"
        
        logger.info("="*60)
        logger.info("INITIALIZING HUGGINGFACE LLM CLIENT")
        logger.info(f"Model: {self.model}")
        logger.info(f"API Key present: {bool(self.api_key)}")
        logger.info(f"API Key (first 10 chars): {self.api_key[:10] if self.api_key else 'NOT SET'}...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info("="*60)
        
        if not self.api_key:
            logger.error("HF_TOKEN not found in environment variables!")
            raise ValueError("HF_TOKEN required. Get it from https://huggingface.co/settings/tokens")
    
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500
    ) -> str:
        """Get completion from HuggingFace with detailed logging"""
        
        logger.info("\n" + "="*60)
        logger.info("STARTING LLM COMPLETION REQUEST")
        logger.info("="*60)
        
        # Log input details
        logger.debug(f"System prompt: {system_prompt[:200]}...")
        logger.debug(f"User message length: {len(user_message)} chars")
        logger.debug(f"User message preview: {user_message[:300]}...")
        logger.debug(f"Temperature: {temperature}")
        logger.debug(f"Max tokens: {max_tokens}")
        
        try:
            # Format the full prompt for HuggingFace
            # Most HF models expect a specific format
            full_prompt = f"""<s>[INST] <<SYS>>
{system_prompt}

You must return ONLY valid JSON without any markdown formatting or backticks.
<</SYS>>

{user_message}

Remember: Return ONLY the JSON object, no explanations or markdown. [/INST]"""
            
            logger.debug(f"Full prompt length: {len(full_prompt)} chars")
            logger.debug(f"Full prompt:\n{full_prompt[:500]}...")
            
            # Prepare the request
            request_data = {
                "inputs": full_prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False,
                    "do_sample": False if temperature == 0 else True
                }
            }
            
            logger.info(f"Sending request to HuggingFace API...")
            logger.debug(f"Request headers: Authorization=Bearer {self.api_key[:10]}...")
            logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_data
                )
                
                logger.info(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 503:
                    logger.error("Model is loading, please retry in a few seconds")
                    error_data = response.json()
                    logger.error(f"503 Error details: {json.dumps(error_data, indent=2)}")
                    raise Exception("Model is loading, please retry")
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"HuggingFace API error {response.status_code}")
                    logger.error(f"Error response: {error_text}")
                    raise Exception(f"HuggingFace API error {response.status_code}: {error_text}")
                
                # Parse response
                data = response.json()
                logger.debug(f"Raw API response: {json.dumps(data, indent=2)[:1000]}")
                
                # Extract the generated text
                if isinstance(data, list) and len(data) > 0:
                    result = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    result = data.get("generated_text", "")
                else:
                    logger.error(f"Unexpected response format: {type(data)}")
                    raise Exception(f"Unexpected response format from HuggingFace")
                
                logger.info(f"Extracted result length: {len(result)} chars")
                logger.debug(f"Raw extracted result:\n{result}")
                
                # Clean the result - extract JSON from the response
                cleaned_result = self._extract_json(result)
                logger.info(f"Cleaned result length: {len(cleaned_result)} chars")
                logger.debug(f"Cleaned result:\n{cleaned_result}")
                
                # Validate it's proper JSON
                try:
                    parsed = json.loads(cleaned_result)
                    logger.info("✅ Successfully parsed JSON response")
                    logger.debug(f"Parsed JSON structure: {json.dumps(parsed, indent=2)[:500]}")
                    return cleaned_result
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse JSON: {e}")
                    logger.error(f"Invalid JSON content:\n{cleaned_result}")
                    raise
                    
        except Exception as e:
            logger.error("="*60)
            logger.error("LLM COMPLETION FAILED")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error("="*60)
            raise
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from the response text with logging"""
        logger.debug("Extracting JSON from response...")
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Try to find JSON boundaries
        if "{" in text and "}" in text:
            # Find the first { and last }
            start = text.find("{")
            end = text.rfind("}") + 1
            json_str = text[start:end]
            logger.debug(f"Extracted JSON substring: {json_str[:200]}...")
            return json_str
        
        # If no JSON markers found, try to clean common patterns
        if "```json" in text:
            logger.debug("Found markdown JSON block")
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            logger.debug("Found markdown code block")
            text = text.split("```")[1].split("```")[0]
        
        # Remove any remaining markdown or explanatory text
        lines = text.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            if '{' in line:
                in_json = True
            if in_json:
                json_lines.append(line)
            if '}' in line and in_json:
                # Check if this closes all brackets
                temp = '\n'.join(json_lines)
                if temp.count('{') == temp.count('}'):
                    break
        
        result = '\n'.join(json_lines) if json_lines else text
        logger.debug(f"Final extracted text: {result[:200]}...")
        return result