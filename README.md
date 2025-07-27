# Lia Agent

**Lia** stands for **"Lean Interactive Agent"**. It is a versatile AI agent designed for **Retrieval Augmented Generation (RAG)**, enabling it to provide informed and contextually rich responses by leveraging an external knowledge base. Depending on your specific use case, Lia can also stand for:

- **Lightweight Interactive Assistant**
- **Learned Information Assistant**
- **Language-Integrated Assistant**
- **Logical Insight Agent**

...and more, adapting to your application's needs.

## Features

- **Retrieval Augmented Generation (RAG)**: Integrates with a vector database (Milvus) to provide contextually rich and informed responses.
- **Dynamic Tool Selection**: Intelligently decides whether to perform RAG retrieval or generate a direct response based on user input.
- **Conversational AI**: Designed for human-like interaction, adapting its tone and understanding context.
- **Error Handling**: Includes robust error handling to manage unexpected issues during agent execution.
- **Streamlit Frontend**: Provides an interactive web UI for chat interaction and monitoring.
- **FastAPI Backend**: A robust Python backend for handling agent logic and API endpoints.
- **Docker Support**: Simplifies deployment and development with Docker and Docker Compose.
- **PostgreSQL Checkpointing**: Utilizes PostgreSQL for persistent chat history and thread state management.

## Installation

### Prerequisites

- **Python 3.12**: The primary development language.
- **Docker**: (Recommended for containerized setup) Ensures consistent environments.

### Create a Virtual Environment

```bash
python3 -m venv venv
```

### Activate the Virtual Environment

```bash
# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### Install Dependencies

Install the necessary Python dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Usage

Before running the application, ensure you have set up your `.env` file and, optionally, customized the prompt files in the `prompts/` directory as described below.

### Running Locally (without Docker)

You can run the backend and frontend separately for local development and testing without Docker.

1.  **Start the Backend Server (FastAPI)**
    This command starts the FastAPI backend server using Uvicorn. The server will typically be available at `http://127.0.0.1:8000`. It includes live reload for development.

    ```bash
    make run
    # Or directly with uvicorn:
    # uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Start the Frontend UI (Streamlit)**
    This command launches the Streamlit UI, which will connect to the backend API. The UI is usually accessible at `http://localhost:8501`.

    ```bash
    streamlit run frontend.py
    ```

### Running with Docker Compose

Docker Compose provides an easy way to spin up all services (Lia agent, PostgreSQL, Milvus, Etcd, Minio) in a containerized environment.

1.  **Build the Docker Image**
    First, build the Docker image for the Lia application. This step only needs to be done once, or whenever your `Dockerfile` or application dependencies change.

    ```bash
    docker build -t lia:latest .
    ```

2.  **Run in Production Mode**
    This command starts the backend (on port `8000`) and frontend (on port `8501`) containers along with their dependencies for a production-like environment.

    ```bash
    make prod
    # Or directly:
    # docker compose up
    ```

3.  **Run in Development Mode (with Live Reload)**
    For development with live code changes, use the dedicated development Docker Compose file (`docker-compose.dev.yml`). This mounts your local project directory into the container, allowing for hot reloading of changes.

    ```bash
    make dev
    # Or directly:
    # docker-compose -f docker-compose.dev.yml up -d --build
    ```

4.  **Stop the Containers**
    To stop and remove the running Docker containers for either production or development environments:

    ```bash
    make prod-down # For production containers
    # Or:
    make dev-down # For development containers
    # Or a general command to stop all services defined in docker-compose.yml:
    # docker compose down --remove-orphans
    ```

    > **Note:** When running with Docker, ensure your `.env` file contains paths appropriate for the containerized environment (e.g., `DATA_DIR=/app/data`, `PROMPTS_DIR=/app/prompts`).

## Environment Variables

This project relies on environment variables for configuration. Copy the `example.env` file to create your `.env` file in the root directory, and then modify it with your specific settings:

```bash
cp example.env .env
```

## Required Files

Lia uses Markdown files in the `prompts/` directory to configure the behavior of its Large Language Models (LLMs). These files define the agent's role, tool selection logic, and error handling instructions.

### `prompts/` Directory

This directory stores the Markdown-based prompt templates used by the LLMs. You can customize these files to refine Lia's behavior.

- **`prompts/system.md`** (or `prompts/system.example.md`):
    - **Purpose**: This file contains the core system instructions for Lia. It defines Lia's overarching role, core principles (e.g., human-like interaction, RAG focus, conversational flow), personality guidelines, and example behaviors. This prompt serves as the foundational context for the agent's reasoning.
    - **Customization**: You can modify this file to change Lia's persona, interaction style, and general guidelines.

- **`prompts/evaluate_tools.md`** (or `prompts/evaluate_tools.example.md`):
    - **Purpose**: This prompt guides the LLM in deciding which tool to use next. It provides rules for when to use `rag` (to search the vector database) or `generate_response` (to reply directly to the user). It also includes guidelines for refining RAG queries and preventing redundant tool calls.
    - **Customization**: Adjust this file to fine-tune how Lia determines when to search for information and when to provide a direct answer.

- **`prompts/error_handler.md`** (or `prompts/error_handler.example.md`):
    - **Purpose**: This prompt is used when an error occurs during the agent's execution. It provides instructions to the LLM on how to acknowledge the error, inform the user, and attempt to recover or provide helpful next steps.
    - **Customization**: Modify this prompt to define how Lia handles and communicates errors to the user.

## Project Structure

- `src/`: Contains the core source code of the application, including agent logic, LLM integrations, and API endpoints.
- `tests/`: Holds unit and integration tests for the application components.
- `data/`: Intended for persistent data, such as documents to be ingested into the vector store.
- `prompts/`: Stores customizable Markdown prompt templates for LLMs, influencing agent behavior.
- `frontend.py`: The main entry point for the Streamlit web user interface.
- `requirements.txt`: Lists all Python dependencies required for the project.
- `Makefile`: Provides convenient shortcuts for common development and deployment tasks (e.g., `make run`, `make dev`, `make prod`).
- `.env`: The environment configuration file, holding sensitive information and settings.
- `README.md`: This project documentation.
- `.dockerignore`: Specifies files and directories to exclude when building Docker images.
- `docker-compose.yml`: Docker Compose configuration for production deployment.
- `docker-compose.dev.yml`: Docker Compose configuration for development deployment with live reload.
- `Dockerfile`: Defines how the application's Docker image is built.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for discussion.

## License

This project is licensed under the MIT License. See the [LICENSE](https://opensource.org/licenses/MIT) file for details.

## Contact

For any inquiries, please contact the maintainers at:
[ruy.vieiraneto@gmail.com](mailto:ruy.vieiraneto@gmail.com)
