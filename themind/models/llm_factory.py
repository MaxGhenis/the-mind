"""Factory for creating LLM players with different models using expectedparrot."""

from typing import List, Dict, Any, Optional
from enum import Enum
import os

from expectedparrot.chat import ChatCompletionProvider, Chat
from themind.core.player import LLMPlayer


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    TOGETHER = "together"


class ModelConfig:
    """Configuration for different models."""
    
    MODELS = {
        # OpenAI models
        "gpt-4o": {"provider": ModelProvider.OPENAI, "temperature": 0.7},
        "gpt-4o-mini": {"provider": ModelProvider.OPENAI, "temperature": 0.7},
        "gpt-4-turbo": {"provider": ModelProvider.OPENAI, "temperature": 0.7},
        "gpt-3.5-turbo": {"provider": ModelProvider.OPENAI, "temperature": 0.7},
        
        # Anthropic models
        "claude-3-5-sonnet": {"provider": ModelProvider.ANTHROPIC, "temperature": 0.7},
        "claude-3-opus": {"provider": ModelProvider.ANTHROPIC, "temperature": 0.7},
        "claude-3-haiku": {"provider": ModelProvider.ANTHROPIC, "temperature": 0.7},
        
        # Google models
        "gemini-1.5-pro": {"provider": ModelProvider.GOOGLE, "temperature": 0.7},
        "gemini-1.5-flash": {"provider": ModelProvider.GOOGLE, "temperature": 0.7},
        
        # Groq models (fast inference)
        "llama-3.1-70b": {"provider": ModelProvider.GROQ, "temperature": 0.7},
        "llama-3.1-8b": {"provider": ModelProvider.GROQ, "temperature": 0.7},
        "mixtral-8x7b": {"provider": ModelProvider.GROQ, "temperature": 0.7},
        
        # Together AI models
        "llama-3-70b": {"provider": ModelProvider.TOGETHER, "temperature": 0.7},
        "mixtral-8x22b": {"provider": ModelProvider.TOGETHER, "temperature": 0.7},
    }


class LLMFactory:
    """Factory for creating LLM players with expectedparrot."""
    
    def __init__(self) -> None:
        self._providers: Dict[ModelProvider, ChatCompletionProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize providers based on available API keys."""
        # OpenAI
        if os.getenv("OPENAI_API_KEY"):
            self._providers[ModelProvider.OPENAI] = ChatCompletionProvider.OPENAI
        
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            self._providers[ModelProvider.ANTHROPIC] = ChatCompletionProvider.ANTHROPIC
        
        # Google
        if os.getenv("GOOGLE_API_KEY"):
            self._providers[ModelProvider.GOOGLE] = ChatCompletionProvider.GOOGLE
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            self._providers[ModelProvider.GROQ] = ChatCompletionProvider.GROQ
        
        # Together
        if os.getenv("TOGETHER_API_KEY"):
            self._providers[ModelProvider.TOGETHER] = ChatCompletionProvider.TOGETHER
    
    def create_player(
        self,
        name: str,
        model: str,
        use_memory: bool = False,
        temperature: Optional[float] = None
    ) -> LLMPlayer:
        """Create an LLM player with the specified model."""
        if model not in ModelConfig.MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {list(ModelConfig.MODELS.keys())}")
        
        model_config = ModelConfig.MODELS[model]
        provider = model_config["provider"]
        
        if provider not in self._providers:
            raise ValueError(
                f"Provider {provider.value} not configured. "
                f"Please set {provider.value.upper()}_API_KEY environment variable."
            )
        
        # Create expectedparrot chat instance
        chat = Chat(
            provider=self._providers[provider],
            model=model,
            temperature=temperature or model_config["temperature"]
        )
        
        # Create wrapper client for compatibility
        class ExpectedParrotWrapper:
            def __init__(self, chat_instance):
                self.chat_instance = chat_instance
                self.chat = self
                self.completions = self
            
            async def create(self, **kwargs):
                # Transform kwargs to expectedparrot format
                messages = kwargs.get("messages", [])
                response_format = kwargs.get("response_format", {})
                
                # Use expectedparrot's chat method
                response = await self.chat_instance.async_chat(
                    messages=messages,
                    json_mode=response_format.get("type") == "json_object"
                )
                
                # Wrap response to match expected format
                class MockResponse:
                    def __init__(self, content):
                        self.choices = [MockChoice(content)]
                
                class MockChoice:
                    def __init__(self, content):
                        self.message = MockMessage(content)
                
                class MockMessage:
                    def __init__(self, content):
                        self.content = content
                
                return MockResponse(response)
        
        wrapper = ExpectedParrotWrapper(chat)
        
        return LLMPlayer(
            name=name,
            model=model,
            client=wrapper,
            use_memory=use_memory,
            temperature=temperature or model_config["temperature"]
        )
    
    def create_players(
        self,
        models: List[str],
        use_memory: bool = False,
        name_prefix: str = "Player"
    ) -> List[LLMPlayer]:
        """Create multiple LLM players with different models."""
        players = []
        for i, model in enumerate(models):
            name = f"{name_prefix}_{i+1}_{model.split('-')[0]}"
            players.append(self.create_player(name, model, use_memory))
        return players
    
    @classmethod
    def available_models(cls) -> List[str]:
        """Get list of all available models."""
        return list(ModelConfig.MODELS.keys())
    
    @classmethod
    def configured_models(cls) -> List[str]:
        """Get list of models with configured API keys."""
        factory = cls()
        configured = []
        for model, config in ModelConfig.MODELS.items():
            if config["provider"] in factory._providers:
                configured.append(model)
        return configured