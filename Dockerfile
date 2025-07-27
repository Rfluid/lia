FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
# libpq5 = PostgreSQL client library required by psycopg
# build-essential = includes gcc, g++, make, and more
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
        build-essential \
        gcc \
        g++ \
        clang \
        git \
        python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn uvicorn python-dotenv

# Copy application code (excluding sensitive runtime data)
COPY prompts/ prompts/
COPY src/ src/
COPY tests/ tests/
COPY frontend.py .
COPY pytest.ini .

COPY /scripts/entrypoint.sh .

EXPOSE 8000 8501

CMD ["./entrypoint.sh"]
