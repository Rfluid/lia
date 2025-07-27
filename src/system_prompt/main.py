from src.config import env


class SystemPromptBuilder:
    prompt: str

    def __init__(self):
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        prompts_dir = env.PROMPTS_DIR
        primary_path = prompts_dir / "system.md"
        fallback_path = prompts_dir / "system.example.md"

        if primary_path.is_file():
            return primary_path.read_text(encoding="utf-8")
        elif fallback_path.is_file():
            return fallback_path.read_text(encoding="utf-8")
        else:
            raise FileNotFoundError(
                f"Neither {primary_path} nor {fallback_path} found."
            )
