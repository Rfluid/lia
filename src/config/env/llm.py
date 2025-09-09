import os

from pydantic import SecretStr

from src.llm.model.llm_provider import LLMProvider


# Function to parse kwargs from environment variables
def parse_kwargs(prefix: str) -> dict:
    kwargs = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Extract the part after the prefix to use as the kwargs key
            kwarg_key = key[len(prefix) :].lower()  # Normalize the key to lowercase
            kwargs[kwarg_key] = value
    return kwargs


# LLM configuration
LLM_PROVIDER = LLMProvider(os.getenv("LLM_PROVIDER", "ollama"))
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "mistral")
LLM_API_KEY = SecretStr(os.getenv("LLM_API_KEY") or "")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
llm_stop = os.getenv("LLM_STOP", None)
LLM_STOP = llm_stop.split(",") if llm_stop else None

# Parse kwargs for different configurations
LLM_KWARGS = parse_kwargs("LLM_ARG_")
TOOL_EVALUATOR_LLM_KWARGS = parse_kwargs("TOOL_EVALUATOR_LLM_ARG_")
TEXT_EMBEDDING_KWARGS = parse_kwargs("TEXT_EMBEDDING_ARG_")
SUMMARIZE_LLM_KWARGS = parse_kwargs("SUMMARIZE_LLM_ARG_")

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


TEST_LLM_PROVIDER = LLMProvider(os.getenv("TEST_LLM_PROVIDER") or LLM_PROVIDER)
TEST_LLM_MODEL_NAME = os.getenv("TEST_LLM_MODEL_NAME") or LLM_MODEL_NAME
test_llm_api_key = os.getenv("TEST_LLM_API_KEY")
TEST_LLM_API_KEY = SecretStr(test_llm_api_key) if test_llm_api_key else LLM_API_KEY
test_llm_temperature = os.getenv("TEST_LLM_TEMPERATURE")
TEST_LLM_TEMPERATURE = (
    float(test_llm_temperature) if test_llm_temperature else LLM_TEMPERATURE
)
test_llm_stop = os.getenv("TEST_LLM_STOP", None)
TEST_LLM_STOP = test_llm_stop.split(",") if test_llm_stop else None


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

PARALLEL_GENERATION = bool(
    os.getenv(
        "PARALLEL_GENERATION",
    )
)

SUMMARIZE_LLM_PROVIDER = LLMProvider(
    os.getenv("SUMMARIZE_LLM_PROVIDER") or LLM_PROVIDER
)
SUMMARIZE_LLM_MODEL_NAME = os.getenv("SUMMARIZE_LLM_MODEL_NAME") or LLM_MODEL_NAME
summarize_llm_api_key = os.getenv("SUMMARIZE_LLM_API_KEY")
SUMMARIZE_LLM_API_KEY = (
    SecretStr(summarize_llm_api_key) if summarize_llm_api_key else LLM_API_KEY
)
summarize_llm_temperature = os.getenv("SUMMARIZE_LLM_TEMPERATURE")
SUMMARIZE_LLM_TEMPERATURE = (
    float(summarize_llm_temperature) if summarize_llm_temperature else LLM_TEMPERATURE
)
summarize_llm_stop = os.getenv("SUMMARIZE_LLM_STOP", None)
SUMMARIZE_LLM_STOP = summarize_llm_stop.split(",") if summarize_llm_stop else None
