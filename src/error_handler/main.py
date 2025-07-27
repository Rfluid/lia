import logging
import os

from langchain_core.messages import SystemMessage
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class ErrorHandler:
    prompt: str

    def __init__(self):
        self.prompt = self._load_prompt()
        self.prompt_template = self._load_prompt_template()
        pass

    def handle(
        self,
        error: str,
        **template_vars,
    ) -> SystemMessage:
        """
        Render self.prompt_template with the provided variables and return the
        result as a SystemMessage.  Re-raises the error once max_retries is hit.
        """

        # Make the raw error available to the template under 'current_error'
        template_vars.setdefault("current_error", error)

        rendered_prompt = self.prompt_template.format(
            # current_error=error
            **template_vars,
        )

        logger.info(f"Rendered prompt: {rendered_prompt}")
        return SystemMessage(content=rendered_prompt)

    def _load_prompt(self) -> str:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        prompt_dir = os.path.join(root_dir, "prompts")
        primary_path = os.path.join(prompt_dir, "error_handler.md")
        fallback_path = os.path.join(prompt_dir, "error_handler.example.md")

        if os.path.isfile(primary_path):
            with open(primary_path, encoding="utf-8") as f:
                return f.read()
        elif os.path.isfile(fallback_path):
            with open(fallback_path, encoding="utf-8") as f:
                return f.read()
        else:
            raise FileNotFoundError(
                "Neither prompts/error_handler.md nor prompts/error_handler.example.md found."
            )

    def _load_prompt_template(self):
        prompt_template = PromptTemplate(
            template=self.prompt,
            input_variables=[
                "current_error",
                # "data",
            ],
        )
        return prompt_template
