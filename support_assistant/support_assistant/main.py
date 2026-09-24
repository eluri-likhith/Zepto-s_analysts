"""
FastAPI wrapper around the LangGraph-orchestrated Zepto support assistant.

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 7860

Example:
    curl -X POST http://localhost:7860/ask \\
        -H "Content-Type: application/json" \\
        -d '{"query": "Is delivery free on small orders?"}'
"""

from fastapi import FastAPI

from graph import run_query
from ingest import build_or_load_collection
from schemas import AskRequest, AskResponse

app = FastAPI(
    title="Zepto Support Assistant",
    description="A small RAG service over Zepto's policy corpus, orchestrated with LangGraph.",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event() -> None:
    """Build/refresh the ChromaDB collection once when the server starts."""
    build_or_load_collection()


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "zepto-support-assistant"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return run_query(request.query)
