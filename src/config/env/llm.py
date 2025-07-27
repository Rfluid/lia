import os

from pydantic import SecretStr

from src.llm.model.llm_provider import LLMProvider

# LLM configuration
LLM_PROVIDER = LLMProvider(os.getenv("LLM_PROVIDER", "ollama"))
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "mistral")
LLM_API_KEY = SecretStr(os.getenv("LLM_API_KEY") or "")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
llm_stop = os.getenv("LLM_STOP", None)
LLM_STOP = llm_stop.split(",") if llm_stop else None
TOOL_EVALUATOR_LLM_PROVIDER = LLMProvider(
    os.getenv("TOOL_EVALUATOR_LLM_PROVIDER") or LLM_PROVIDER
)
TOOL_EVALUATOR_LLM_MODEL_NAME = (
    os.getenv("TOOL_EVALUATOR_LLM_MODEL_NAME") or LLM_MODEL_NAME
)
tool_evaluator_llm_api_key = os.getenv("TOOL_EVALUATOR_LLM_API_KEY")
TOOL_EVALUATOR_LLM_API_KEY = (
    SecretStr(tool_evaluator_llm_api_key) if tool_evaluator_llm_api_key else LLM_API_KEY
)
tool_evaluator_llm_temperature = os.getenv("TOOL_EVALUATOR_LLM_TEMPERATURE")
TOOL_EVALUATOR_LLM_TEMPERATURE = (
    float(tool_evaluator_llm_temperature)
    if tool_evaluator_llm_temperature
    else LLM_TEMPERATURE
)
tool_evaluator_llm_stop = os.getenv("TOOL_EVALUATOR_LLM_STOP", None)
TOOL_EVALUATOR_LLM_STOP = (
    tool_evaluator_llm_stop.split(",") if tool_evaluator_llm_stop else None
)


TEXT_EMBEDDING_PROVIDER = LLMProvider(
    os.getenv("TEXT_EMBEDDING_PROVIDER") or LLM_PROVIDER
)
TEXT_EMBEDDING_MODEL_NAME = os.getenv(
    "TEXT_EMBEDDING_MODEL_NAME", "models/text-embedding-004"
)
text_embedding_api_key = os.getenv("TEXT_EMBEDDING_API_KEY")
TEXT_EMBEDDING_API_KEY = (
    SecretStr(text_embedding_api_key) if text_embedding_api_key else LLM_API_KEY
)
