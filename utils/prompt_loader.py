# utils/prompt_loader.py
"""
Prompt template loader
"""
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load and cache prompt templates"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}
    
    def load(self, filename: str) -> str:
        """Load a prompt template"""
        # Check cache
        if filename in self._cache:
            return self._cache[filename]
        
        # Load from file
        filepath = self.prompts_dir / filename
        
        if not filepath.exists():
            logger.error(f"Prompt file not found: {filepath}")
            raise FileNotFoundError(f"Prompt file not found: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Cache it
            self._cache[filename] = content
            logger.debug(f"Loaded prompt: {filename}")
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise
    
    def reload(self):
        """Clear cache to reload prompts"""
        self._cache.clear()
        logger.info("Prompt cache cleared")