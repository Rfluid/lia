import logging

from langchain.llms.base import BaseLLM
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable

from src.config import env
from src.generate_response.model.response import (
    LLMAPIResponse,
)
from src.llm.service import load_model

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class ResponseGenerator:
    model: BaseLLM | BaseChatModel
    chain: RunnableSerializable
    whatsapp_chain: RunnableSerializable

    def __init__(self):
        self.model = load_model(
            env.LLM_PROVIDER,
            env.LLM_MODEL_NAME,
            env.LLM_API_KEY,
            model_stop=env.LLM_STOP,
            model_temperature=env.LLM_TEMPERATURE,
        )
        self.chain = self._load_chain()

    def generate_response(
        self,
        # data: Any,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> LLMAPIResponse:
        response = self.chain.invoke(
            {
                "query": query,
            },
            config=config,
        )
        logger.info(f"Response: {response}")
        return LLMAPIResponse.model_validate(response)

    def _load_chain(self):
        parser = JsonOutputParser(pydantic_object=LLMAPIResponse)
        prompt = PromptTemplate(
            template="""Based on the chat history
{query}
generate a response to the user considering the data retrieved from the tools.

{format_instructions}""",
            input_variables=[
                "query",
                # "data",
            ],
            output_parser=parser,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = prompt | self.model | parser
        return chain
