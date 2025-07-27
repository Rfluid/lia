from langchain_core.runnables.graph import MermaidDrawMethod

from src.agent import workflow


def render_mermaid_png() -> bytes:
    # This runs **inside the worker process**
    graph = workflow.compiled_graph.get_graph()
    return graph.draw_mermaid_png(draw_method=MermaidDrawMethod.PYPPETEER)


def render_mermaid() -> str:
    # This runs **inside the worker process**
    graph = workflow.compiled_graph.get_graph()
    draw = graph.draw_mermaid()
    return draw
