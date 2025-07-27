from enum import Enum


class Steps(Enum):
    context_incrementer = "context_incrementer"

    context_builder = (
        "context_builder"  # Builds the context for the given chat interface.
    )

    evaluate_tools = "evaluate_tools"  # Decides if will search any sources or just generate the response and send back.

    rag = "rag"  # Enhances the response by searching other sources.
    generate_response = (
        "generate_response"  # Generates response for the given chat interface.
    )

    # Actions after response generation
    error_handler = "error_handler"  # Handles errors that may occur during the process.

    end = "end"  # We have this item only to be able to use on conditional edges.
