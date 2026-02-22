"""
services/llm_client.py
----------------------
Universal LLM client supporting multiple providers.

Supports: OpenRouter, Groq, Gemini, Anthropic, OpenAI
"""

import logging
from typing import List, Dict, Optional

import config

logger = logging.getLogger(__name__)


class LLMClient:
    """Universal LLM client with multi-provider support."""
    
    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.model = config.LLM_MODEL
        self.max_tokens = config.LLM_MAX_TOKENS
        self.temperature = config.LLM_TEMPERATURE
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        try:
            if self.provider == "anthropic":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.model = config.CLAUDE_MODEL
                
            elif self.provider in ["openai", "groq", "openrouter"]:
                from openai import OpenAI
                
                if self.provider == "openai":
                    self._client = OpenAI(api_key=config.OPENAI_API_KEY)
                elif self.provider == "groq":
                    self._client = OpenAI(
                        api_key=config.GROQ_API_KEY,
                        base_url=config.LLM_BASE_URL
                    )
                elif self.provider == "openrouter":
                    self._client = OpenAI(
                        api_key=config.OPENROUTER_API_KEY,
                        base_url=config.LLM_BASE_URL
                    )
                    
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self._client = genai.GenerativeModel(self.model)
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
            logger.info(f"LLM client initialized: {self.provider} / {self.model}")
            
        except ImportError as e:
            logger.error(f"Missing dependency for {self.provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise
    
    def generate(self, system_prompt: str, user_message: str, 
                 messages: Optional[List[Dict]] = None) -> Dict:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: System/instruction prompt
            user_message: User's message
            messages: Optional conversation history
            
        Returns:
            Dict with keys: text, tokens_used, model
        """
        try:
            if self.provider == "anthropic":
                return self._generate_anthropic(system_prompt, user_message, messages)
            elif self.provider in ["openai", "groq", "openrouter"]:
                return self._generate_openai_compatible(system_prompt, user_message, messages)
            elif self.provider == "gemini":
                return self._generate_gemini(system_prompt, user_message, messages)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    def _generate_anthropic(self, system_prompt: str, user_message: str,
                           messages: Optional[List[Dict]] = None) -> Dict:
        """Generate using Anthropic Claude API."""
        msg_list = messages or []
        msg_list.append({"role": "user", "content": user_message})
        
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=msg_list
        )
        
        return {
            "text": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "model": self.model
        }
    
    def _generate_openai_compatible(self, system_prompt: str, user_message: str,
                                   messages: Optional[List[Dict]] = None) -> Dict:
        """Generate using OpenAI-compatible API (OpenAI, Groq, OpenRouter)."""
        msg_list = [{"role": "system", "content": system_prompt}]
        
        if messages:
            msg_list.extend(messages)
        
        msg_list.append({"role": "user", "content": user_message})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=msg_list,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        tokens_used = 0
        if hasattr(response, 'usage') and response.usage:
            tokens_used = response.usage.total_tokens
        
        return {
            "text": response.choices[0].message.content,
            "tokens_used": tokens_used,
            "model": self.model
        }
    
    def _generate_gemini(self, system_prompt: str, user_message: str,
                        messages: Optional[List[Dict]] = None) -> Dict:
        """Generate using Google Gemini API."""
        # Gemini combines system prompt with user message
        full_prompt = f"{system_prompt}\n\n{user_message}"
        
        if messages:
            # Build conversation history
            history_text = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in messages
            ])
            full_prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:\n{history_text}\n\nCURRENT MESSAGE:\n{user_message}"
        
        try:
            response = self._client.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            
            # Gemini doesn't provide token counts in free tier
            tokens_used = len(full_prompt.split()) + len(response.text.split())
            
            return {
                "text": response.text,
                "tokens_used": tokens_used,
                "model": self.model
            }
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Try to extract error details
            error_msg = str(e)
            if "not found" in error_msg.lower():
                logger.error(f"Model '{self.model}' not found. Try: gemini-1.5-flash-latest, gemini-1.5-pro-latest, or gemini-pro")
            raise


# Global client instance
_client = None

def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
