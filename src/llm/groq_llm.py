from llama_index.llms.groq import Groq
from llama_index.core.llms import ChatMessage
from typing import List, Optional
import os
from config.config import GROQ_API_KEY

class GroqLLMWrapper:
    def __init__(
        self,
        model_name: str = "llama-3.3-70b-specdec",
        temperature: float = 0.1
    ):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        
        self.llm = Groq(
            model=model_name,
            api_key=GROQ_API_KEY,
            temperature=temperature
        )
        
    def get_llm(self):
        return self.llm

    def chat(self, messages: List[ChatMessage]) -> str:
        try:
            response = self.llm.chat(messages)
            return response.message.content
        except Exception as e:
            raise Exception(f"Error in Groq API call: {str(e)}")