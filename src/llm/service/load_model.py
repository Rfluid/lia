from langchain.llms.base import BaseLLM
from langchain_anthropic import ChatAnthropic
from langchain_cohere import ChatCohere
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.config import env
from src.llm.model.llm_provider import LLMProvider


def load_model(
    provider: LLMProvider,
    model_name: str,
    api_key: SecretStr = env.LLM_API_KEY,
    model_temperature: float = 0,
    model_timeout: int = 0,
    model_stop: list[str] | None = None,
) -> BaseLLM | BaseChatModel:
    match provider:
        case LLMProvider.openai:
            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                temperature=model_temperature,
                timeout=model_timeout if model_timeout > 0 else None,
            )

        case LLMProvider.anthropic:
            return ChatAnthropic(
                model_name=model_name,
                api_key=api_key,
                timeout=model_timeout if model_timeout > 0 else None,
                stop=model_stop,
                temperature=model_temperature,
            )

        case LLMProvider.cohere:
            return ChatCohere(
                model=model_name,
                cohere_api_key=api_key,
                temperature=model_temperature,
                stop=model_stop,
                timeout_seconds=model_timeout if model_timeout > 0 else None,
            )

        case LLMProvider.ollama:
            return OllamaLLM(
                model=model_name,
                temperature=model_temperature,
                stop=model_stop,
            )

        case LLMProvider.gemini:
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=model_temperature,
                timeout=model_timeout if model_timeout > 0 else None,
            )

        # case LLMProvider.huggingface:
        #     return HuggingFaceHub(
        #         repo_id=model_name,
        #         huggingfacehub_api_token=api_key.get_secret_value(),
        #         temperature=0,
        #     )
        #
        # case LLMProvider.llamacpp:
        #     return LlamaCpp(
        #         model_path=model_name,
        #         temperature=0,
        #     )

        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")
