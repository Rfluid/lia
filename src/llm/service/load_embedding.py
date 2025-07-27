from langchain_community.embeddings import (
    CohereEmbeddings,
    OllamaEmbeddings,
)
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from src.llm.model import LLMProvider


def load_embedding(
    provider: LLMProvider,
    api_key: SecretStr,
    model_name: str | None = None,
) -> Embeddings:
    match provider:
        case LLMProvider.openai:
            if not model_name:
                raise ValueError("Model name must be provided for OpenAI.")
            return OpenAIEmbeddings(api_key=api_key, model=model_name)
        # case LLMProvider.anthropic:
        #     return
        case LLMProvider.cohere:
            return CohereEmbeddings(cohere_api_key=str(api_key))
        case LLMProvider.ollama:
            return OllamaEmbeddings()
        case LLMProvider.gemini:
            if not model_name:
                raise ValueError("Model name must be provided for Google Gemini.")
            return GoogleGenerativeAIEmbeddings(
                google_api_key=api_key, model=model_name
            )
        # case LLMProvider.huggingface:
        #     return HuggingFaceHub
        #
        # case LLMProvider.llamacpp:
        #     return LlamaCpp

        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")
