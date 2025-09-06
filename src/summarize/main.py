import logging
import os
from uuid import uuid4

from langchain.llms.base import BaseLLM
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, RemoveMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig, RunnableSerializable

from src.agent.model.graph_state import GraphState
from src.config import env
from src.llm.service import load_model
from src.summarize.model.output import SummarizeOutput

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def _is_system(m: BaseMessage) -> bool:
    is_instance = isinstance(m, SystemMessage)
    return is_instance


def _ensure_ids(msgs: list[BaseMessage]) -> None:
    for m in msgs:
        if not getattr(m, "id", None):
            # LangChain messages are Pydantic models; setting .id is fine
            m.id = str(uuid4())


def _clone_with_new_id(m: BaseMessage) -> BaseMessage:
    mc = m.model_copy(deep=True)  # pydantic copy
    mc.id = str(uuid4())
    return mc


class Summarizer:
    model: BaseLLM | BaseChatModel
    prompt: str
    chain: RunnableSerializable

    def __init__(self):
        self.model = load_model(
            env.SUMMARIZE_LLM_PROVIDER,
            env.SUMMARIZE_LLM_MODEL_NAME,
            env.SUMMARIZE_LLM_API_KEY,
            model_stop=env.SUMMARIZE_LLM_STOP,
            model_temperature=env.SUMMARIZE_LLM_TEMPERATURE,
        )
        # make sure prompt is loaded before building the chain
        self.prompt = self._load_prompt()
        self.chain = self._load_chain()

    def summarize_conditionally(
        self, state: GraphState, config: RunnableConfig | None = None
    ):
        total = len(state.messages)
        keep = state.summarize_message_keep
        window = state.summarize_message_window

        pre_keep = max(0, total - keep)
        if pre_keep < window:
            return  # don’t summarize until there’s enough history

        # 1) Split: everything before the keep-tail will be summarized (subject to the flag)
        pre_region = state.messages[:pre_keep]
        keep_tail = state.messages[pre_keep:]

        # 2) Ensure every message has an id (so RemoveMessage can match)
        _ensure_ids(state.messages)

        # 3) Partition the pre-region depending on summarize_system_messages
        if getattr(state, "summarize_system_messages", False):
            system_head: list[BaseMessage] = []
            to_summarize: list[BaseMessage] = pre_region
        else:
            system_head = [m for m in pre_region if _is_system(m)]
            to_summarize = [m for m in pre_region if not _is_system(m)]

        # If there’s nothing to summarize (e.g., only system messages), skip work
        if not to_summarize:
            return

        # 4) Produce the summary text/object ONLY from the chosen set
        summary = self.summarize(to_summarize, config)

        # 5) Build a single reducer update:
        #    - remove ALL current messages (so we control final order deterministically)
        ops: list[BaseMessage] = [RemoveMessage(id=m.id) for m in state.messages]  # type: ignore[assignment]

        #    - re-add preserved system messages (fresh ids to avoid clashes with RemoveMessage)
        system_head_fresh = []
        for m in system_head:
            mc = m.model_copy(deep=True)
            mc.id = str(uuid4())
            system_head_fresh.append(mc)

        #    - append synthetic summary as a SystemMessage (fresh id)
        # summary_msg = AIMessage(
        #     content=summary.summary,  # or summary.text if you prefer plain text
        # )
        summary_msg = BaseMessage(
            content=summary.summary,  # or summary.text if you prefer plain text
            type="summary",
        )

        #    - re-add keep-tail (fresh ids)
        keep_tail_fresh = []
        for m in keep_tail:
            mc = m.model_copy(deep=True)
            mc.id = str(uuid4())
            keep_tail_fresh.append(mc)

        ops.extend(system_head_fresh)
        ops.append(summary_msg)
        ops.extend(keep_tail_fresh)

        # 6) One assignment so downstream reducers see a single atomic rewrite
        state.messages = ops

    def summarize(
        self,
        query: list,
        config: RunnableConfig | None = None,
    ) -> SummarizeOutput:
        response = self.chain.invoke({"query": query}, config=config)
        return SummarizeOutput.model_validate(response)

    def _load_prompt(self) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        prompt_dir = os.path.join(root_dir, "prompts")
        primary_path = os.path.join(prompt_dir, "summarize.md")
        fallback_file = "summarize.example.md"
        fallback_path = os.path.join(prompt_dir, fallback_file)

        if os.path.isfile(primary_path):
            with open(primary_path, encoding="utf-8") as f:
                return f.read()
        elif os.path.isfile(fallback_path):
            with open(fallback_path, encoding="utf-8") as f:
                return f.read()
        else:
            raise FileNotFoundError(
                f"Neither prompts/summarize.md nor prompts/{fallback_file} found."
            )

    def _load_chain(self):
        parser = JsonOutputParser(pydantic_object=SummarizeOutput)
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
