from llama_index.llms.openai_like import OpenAILike
from llama_index.core.llms import ChatMessage
from typing import List, Optional
from config.config import LOCAL_LLM_BASE_URL, LOCAL_LLM_API_KEY

class LocalLLMWrapper:
    def __init__(
        self,
        model_name: str = "Mistral-Small-Instruct-2409-Q5_K_L",
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024
    ):
        if not LOCAL_LLM_BASE_URL:
            raise ValueError("LOCAL_LLM_BASE_URL not set in configuration")
        if not LOCAL_LLM_API_KEY:
            raise ValueError("LOCAL_LLM_API_KEY not set in configuration")
        
        self.system_prompt = system_prompt
        self.llm = OpenAILike(
            model=model_name,
            api_base=LOCAL_LLM_BASE_URL,
            api_key=LOCAL_LLM_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
            is_chat_model=True,
            additional_headers={"x-goog-api-key": LOCAL_LLM_API_KEY}
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
            # return response.message.content
            return self._strip_thinking_tags(response.message.content)
        except Exception as e:
            raise Exception(f"Error in Local LLM call: {str(e)}")

    def _strip_thinking_tags(self, content: str) -> str:
        """Remove thinking tags and their content from the response."""
        import re
        
        # Remove both <details>...</details> and <think>...</think> sections
        patterns = [
            r'<details.*?</details>\s*',  # Match <details> tags
            r'<think>.*?</think>\s*'      # Match <think> tags
        ]
        
        cleaned_content = content
        for pattern in patterns:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)
        
        # Remove any leading/trailing whitespace
        return cleaned_content.strip()

    @classmethod
    def create_thinking_llm(cls, system_prompt: str) -> 'LocalLLMWrapper':
        """Creates an LLM instance optimized for detailed thinking/reasoning"""
        return cls(
            model_name="DeepSeek-R1-Distill-Llama-8B-Q6_K",
            # model_name="DeepSeek-R1-Distill-Qwen-32B-Q4_K_M",
            # model_name="Janus-Pro-7B-LM-Q6_K",
            temperature=0.1,
            system_prompt=system_prompt,
        )

    @classmethod
    def create_speech_llm(cls, speech_prompt: str) -> 'LocalLLMWrapper':
        """Creates an LLM instance optimized for natural speech conversion"""
        return cls(
            model_name="Mistral-Small-Instruct-2409-Q5_K_L",
            temperature=0.3,
            system_prompt=speech_prompt,
        )

    @classmethod
    def create_markdown_filter_llm(cls, filter_prompt: str) -> 'LocalLLMWrapper':
        """Creates an LLM instance optimized for markdown filtering"""
        return cls(
            model_name="DeepSeek-R1-Distill-Llama-8B-Q6_K",
            temperature=0.1,
            system_prompt=filter_prompt,
        )