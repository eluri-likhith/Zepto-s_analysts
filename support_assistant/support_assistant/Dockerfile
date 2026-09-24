FROM python:3.11-slim

WORKDIR /app

# System deps needed by chromadb / sentence-transformers wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Graded baseline: MOCK_LLM defaults to 1 (offline mock) unless overridden
# at `docker run` time with -e MOCK_LLM=0 (optional extension).
ENV MOCK_LLM=1
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
