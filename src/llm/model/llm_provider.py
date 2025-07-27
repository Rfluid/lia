from enum import Enum


class LLMProvider(Enum):
    openai = "openai"
    anthropic = "anthropic"
    cohere = "cohere"
    ollama = "ollama"
    gemini = "gemini"
    # huggingface = "huggingface"
    # llamacpp = "llamacpp"
