#!/bin/bash

# Start the backend (FastAPI with Gunicorn) in the background
gunicorn src.main:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers $(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)") &

# Start the frontend (Streamlit)
streamlit run frontend.py
