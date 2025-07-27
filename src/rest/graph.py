import logging

from fastapi import APIRouter, HTTPException

from src.agent.graph import (
    render_mermaid,
)  # already instanced Workflow()

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/mermaid",
    summary="Return a mermaid string rendering of the compiled workflow graph",
)
async def get_workflow_graph_string():
    try:
        compiled_str = render_mermaid()
        return compiled_str
    except Exception as e:
        logger.error("Error rendering workflow graph: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=e) from e


# @router.get(
#     "/mermaid-png",
#     summary="Return a PNG rendering of the compiled workflow graph",
#     responses={200: {"content": {"image/png": {}}}},
#     response_class=Response,
# )
# async def get_workflow_graph():
#     """
#     Returns the compiled state-graph of the agent as a PNG image.
#     """
#     try:
#         png_bytes = render_mermaid_png()
#         return Response(content=png_bytes, media_type="image/png")
#     except Exception as e:
#         logger.error("Error rendering workflow graph: %s", e, exc_info=True)
#         raise HTTPException(status_code=500, detail=e)
