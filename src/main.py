import logging
from textwrap import dedent

from fastapi import APIRouter, FastAPI

from src.config.env import main
from src.rest.graph import router as graph_router
from src.rest.messages import router as messages_router
from src.rest.threads import router as threads_router
from src.rest.vectorstore import router as vectorstore_router

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # or DEBUG
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.info(f"Initializing {__name__} for environment {main.ENV}...")

# --- Metadata taken from README ------------------------------------------------

app = FastAPI(
    title="Lia Interactive Agent",
    version="0.1.1",  # bump automatically from pyproject/version if you wish
    summary="Lean Interactive Agent – a lightweight assistant that reasons over your data using RAG.",
    description=dedent(
        """
        **Lia** (*Lean Interactive Agent*) is an AI agent focused on **Retrieval Augmented Generation (RAG)**.
        It provides intelligent and context-aware responses by leveraging information from your
        defined knowledge base.

        ### Why “Lia”?
        - Lightweight Interactive Assistant
        - Learned Information Assistant
        - Language-Integrated Assistant
        - Logical Insight Agent

        ---

        Full installation and more in the [README](github.com/Rfluid/lia).
        """
    ),
    contact={
        "name": "Ruy Vieira",
        "email": "ruy.vieiraneto@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Tag metadata (shows up as sections in the docs) ---------------------------
tags_metadata = [
    {
        "name": "Messages",
        "description": "Send inputs to the agent.",
    },
    {
        "name": "Threads",
        "description": "Handle thread data.",
    },
    {
        "name": "Graph",
        "description": "Inspect graph details.",
    },
    {
        "name": "Vectorstore",
        "description": "Handle vectorstore data.",
    },
]
app.openapi_tags = tags_metadata

# --- Routes --------------------------------------------------------------------
#
# Agent
agent_router = APIRouter(prefix="/agent")

agent_router.include_router(messages_router, prefix="/messages", tags=["Messages"])
agent_router.include_router(threads_router, prefix="/threads", tags=["Threads"])
agent_router.include_router(graph_router, prefix="/graph", tags=["Graph"])

app.include_router(agent_router)

# Other routes
app.include_router(vectorstore_router, prefix="/vectorstore", tags=["Vectorstore"])
