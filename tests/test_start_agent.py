import logging
import uuid

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from src.agent import start

# Configura o logger para ser bem detalhado
logger = logging.getLogger(__name__)


async def test_start_real_workflow():
    logger.info("🧪 Starting workflow test with function `start()`")

    # Configuração básica do agente
    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    logger.debug(f"⚙️ Configuration sent to workflow: {config}")

    # Fase 1: input inicial com nome
    initial_input = HumanMessage(content="Hello! My name is Ruy!")
    logger.debug(f"📝 Input sent to Workflow (Phase 1): {initial_input}")

    try:
        first_response = await start(input=[initial_input], config=config)
        logger.info("✅ Phase 1 finished successfully.")
        logger.debug(f"📦 Phase 1 Result: {first_response['messages'][-1]}")
    except Exception as e:
        logger.error("❌ Error during Phase 1", exc_info=True)
        raise AssertionError(f"An unexpected error occurred in Phase 1: {e}") from e

    assert first_response["messages"][-1] is not None, (
        "Expected a non-null result in Phase 1."
    )

    # Fase 2: pergunta sobre o nome
    follow_up_input = HumanMessage(content="What is my name?")
    logger.debug(f"📝 Input sent to Workflow (Phase 2): {follow_up_input}")

    try:
        second_response = await start(input=[follow_up_input], config=config)
        logger.info("✅ Phase 2 finished successfully.")
        logger.debug(f"📦 Phase 2 Result: {second_response['messages'][-1]}")
    except Exception as e:
        logger.error("❌ Error during Phase 2", exc_info=True)
        raise AssertionError(f"An unexpected error occurred in Phase 2: {e}") from e

    assert second_response["messages"][-1] is not None, (
        "Expected a non-null result in Phase 2."
    )

    # Verifica se o nome "Ruy" aparece em alguma string do dicionário de resposta
    response_texts = str(second_response["messages"][-1]).lower()
    assert "ruy" in response_texts, (
        "Expected the name 'Ruy' to appear in the second response."
    )

    logger.info("🎉 All test phases finished successfully.")
