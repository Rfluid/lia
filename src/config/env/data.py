import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
PROMPTS_DIR = Path(os.getenv("PROMPTS_DIR", "prompts"))
