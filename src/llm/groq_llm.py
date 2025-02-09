from llama_index.llms.groq import Groq
from llama_index.core.llms import ChatMessage
from typing import List, Optional
import os
from config.config import GROQ_API_KEY

class GroqLLMWrapper:
    def __init__(
        self,
        model_name: str = "llama-3.3-70b-specdec",
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024  # Increased default token limit
    ):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        
        self.system_prompt = system_prompt
        self.llm = Groq(
            model=model_name,
            api_key=GROQ_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
    def get_llm(self):
        return self.llm

    def chat(self, messages: List[ChatMessage]) -> str:
        try:
            # If system prompt is set and not already in messages, prepend it
            if self.system_prompt and not any(msg.role == "system" for msg in messages):
                system_message = ChatMessage(role="system", content=self.system_prompt)
                messages = [system_message] + messages
            
            response = self.llm.chat(messages)
            return response.message.content
        except Exception as e:
            raise Exception(f"Error in Groq API call: {str(e)}")

    @classmethod
    def create_thinking_llm(cls, system_prompt: str) -> 'GroqLLMWrapper':
        """Creates an LLM instance optimized for detailed thinking/reasoning"""
        return cls(
            #model_name="deepseek-r1-distill-llama-70b",
            model_name="llama-3.3-70b-specdec",
            #model_name="deepseek-r1-distill-llama-70b-specdec",
            temperature=0.1,
            system_prompt=system_prompt,
            # max_tokens=2048  # Larger context for detailed reasoning
        )

    @classmethod
    def create_speech_llm(cls, speech_prompt: str) -> 'GroqLLMWrapper':
        """Creates an LLM instance optimized for natural speech conversion"""
        return cls(
            model_name="llama-3.3-70b-specdec",
            temperature=0.3,  # Slightly higher temperature for more natural speech
            system_prompt=speech_prompt,
            # max_tokens=512
        )