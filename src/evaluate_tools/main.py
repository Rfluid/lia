import os

from langchain.llms.base import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable

from src.config import env
from src.evaluate_tools.model import ToolConfig
from src.llm.service import load_model


class EvaluateTools:
    model: BaseLLM | BaseChatModel
    prompt: str
    chain: RunnableSerializable

    def __init__(self):
        self.model = load_model(
            env.TOOL_EVALUATOR_LLM_PROVIDER,
            env.TOOL_EVALUATOR_LLM_MODEL_NAME,
            env.TOOL_EVALUATOR_LLM_API_KEY,
            model_stop=env.TOOL_EVALUATOR_LLM_STOP,
            model_temperature=env.TOOL_EVALUATOR_LLM_TEMPERATURE,
        )
        self.prompt = self._load_prompt()
        self.chain = self._load_chain()

    def decide_next_step(
        self,
        config: RunnableConfig | None = None,
        query: list | None = None,
    ) -> ToolConfig:
        response = self.chain.invoke(
            {
                "query": query,
            },
            config=config,
        )

        return ToolConfig.model_validate(response)

    def _load_prompt(self) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        prompt_dir = os.path.join(root_dir, "prompts")
        primary_path = os.path.join(prompt_dir, "evaluate_tools.md")
        fallback_path = os.path.join(prompt_dir, "evaluate_tools.example.md")

        if os.path.isfile(primary_path):
            with open(primary_path, encoding="utf-8") as f:
                return f.read()
        elif os.path.isfile(fallback_path):
            with open(fallback_path, encoding="utf-8") as f:
                return f.read()
        else:
            raise FileNotFoundError(
                "Neither prompts/evaluate_tools.md nor prompts/evaluate_tools.example.md found."
            )

    def _load_chain(self):
        parser = JsonOutputParser(pydantic_object=ToolConfig)
        prompt = PromptTemplate(
            template=f"{self.prompt}",
            input_variables=[
                "query",
            ],
            output_parser=parser,
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        chain = prompt | self.model | parser
        return chain
