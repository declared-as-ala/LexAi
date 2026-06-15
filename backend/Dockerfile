FROM python:3.12-slim

WORKDIR /app

# System deps: build tools + libpq for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# Install torch CPU-only first (keeps image ~2GB lighter than full CUDA torch)
# --timeout 300 and --retries 5 guard against slow PyTorch CDN connections
RUN pip install --no-cache-dir --timeout 300 --retries 5 \
    torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy French model (fr_core_news_lg ~550MB)
# Falls back gracefully to rule-only NER if unavailable at runtime
RUN python -m spacy download fr_core_news_lg

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY pytest.ini ./pytest.ini

RUN mkdir -p /app/uploads

ENV PYTHONPATH=/app
ENV UPLOAD_DIR=/app/uploads

# HuggingFace cache dir inside container (zero-shot model downloaded on first inference)
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p /app/.cache/huggingface

EXPOSE 8000

CMD ["sh", "-c", "python -m app.db.migrate && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
