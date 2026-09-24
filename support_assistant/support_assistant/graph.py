"""
LangGraph orchestration for the Zepto support assistant.

Graph shape:

    classify_intent --(policy_question)--> retrieve_and_answer --> END
                    \\-(general_question)--> direct_answer --> END

Every generation step branches on the MOCK_LLM environment variable:
  - MOCK_LLM unset, or MOCK_LLM=1  -> deterministic, offline mock logic
                                      (this is the required, graded baseline)
  - MOCK_LLM=0                     -> optional real-LLM extension (Groq, or
                                      any genuinely-free-tier LLM API)

The routing logic itself (classify_intent's conditional edge) does NOT depend
on MOCK_LLM — only the generation step *inside* each node does.
"""

import os
from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from ingest import retrieve_top_k
from prompts import build_direct_prompt, build_rag_prompt
from schemas import AskResponse

POLICY_KEYWORDS = [
    "delivery",
    "return",
    "refund",
    "membership",
    "tracking",
    "cancel",
    "gift card",
    "support hours",
]


def is_mock_mode() -> bool:
    """MOCK_LLM unset or '1' -> mock (graded baseline). '0' -> real LLM."""
    return os.environ.get("MOCK_LLM", "1") != "0"


class GraphState(TypedDict):
    query: str
    intent: str
    retrieved_chunks: List[dict]
    answer: str
    sources: List[str]
    confidence: float


# ---------------------------------------------------------------------------
# Node 1: classify_intent
# ---------------------------------------------------------------------------
def classify_intent(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        # Mock mode (graded baseline): keyword heuristic, no LLM call.
        lowered = query.lower()
        if any(keyword in lowered for keyword in POLICY_KEYWORDS):
            intent = "policy_question"
        else:
            intent = "general_question"
    else:
        # Optional MOCK_LLM=0 extension: ask the real LLM to classify.
        intent = _llm_classify_intent(query)

    return {**state, "intent": intent}


def _llm_classify_intent(query: str) -> str:
    """Optional real-LLM classification path (MOCK_LLM=0 only)."""
    from llm_client import call_llm

    classification_prompt = (
        "Classify the following customer question as exactly one word: "
        "'policy_question' if it concerns Zepto's delivery, returns, refunds, "
        "membership, order tracking, cancellation, gift cards, or support "
        "hours policies, otherwise 'general_question'.\n\n"
        f"Question: {query}\nAnswer with exactly one word:"
    )
    raw = call_llm(classification_prompt).strip().lower()
    return "policy_question" if "policy_question" in raw else "general_question"


# ---------------------------------------------------------------------------
# Node 2: retrieve_and_answer  (policy_question branch)
# ---------------------------------------------------------------------------
def retrieve_and_answer(state: GraphState) -> GraphState:
    query = state["query"]

    # Retrieval always runs for real in both modes: local embeddings +
    # ChromaDB need no API key and no network call to any LLM provider.
    retrieved = retrieve_top_k(query, k=3)
    sources = [chunk["id"] for chunk in retrieved]

    if is_mock_mode():
        # Mock mode (graded baseline): canned templated answer, no LLM call.
        if retrieved:
            top_chunk_snippet = retrieved[0]["text"][:200]
        else:
            top_chunk_snippet = ""
        answer = f"Based on the retrieved context: {top_chunk_snippet}"
        confidence = 1.0
    else:
        # Optional MOCK_LLM=0 extension: real LLM grounded in retrieved chunks.
        context = "\n\n".join(f"[{c['id']}] {c['text']}" for c in retrieved)
        prompt = build_rag_prompt(context=context, question=query)
        answer, confidence = _llm_generate_validated(prompt, sources)

    return {
        **state,
        "retrieved_chunks": retrieved,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Node 3: direct_answer  (general_question branch)
# ---------------------------------------------------------------------------
def direct_answer(state: GraphState) -> GraphState:
    query = state["query"]

    if is_mock_mode():
        # Mock mode (graded baseline): fixed canned string, no LLM call.
        answer = "I can only answer questions about Zepto policies right now."
        confidence = 1.0
    else:
        # Optional MOCK_LLM=0 extension: prompt the LLM directly, no retrieval.
        prompt = build_direct_prompt(question=query)
        answer, confidence = _llm_generate_validated(prompt, sources=[])

    return {
        **state,
        "retrieved_chunks": [],
        "answer": answer,
        "sources": [],
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Optional MOCK_LLM=0 helper: validated real-LLM generation with retries
# ---------------------------------------------------------------------------
def _llm_generate_validated(prompt: str, sources: List[str], max_retries: int = 2):
    """
    Call the real LLM and validate its output against AskResponse.
    Retries up to `max_retries` additional times with a corrective
    instruction before giving up and returning a clearly marked error.

    Only ever invoked on the optional MOCK_LLM=0 path.
    """
    from llm_client import call_llm

    corrective_suffix = ""
    for attempt in range(max_retries + 1):
        raw_answer = call_llm(prompt + corrective_suffix).strip()
        try:
            # The LLM is asked for prose; we build the structured object
            # ourselves and validate the pieces we control against the schema.
            validated = AskResponse(answer=raw_answer, sources=sources, confidence=0.8)
            return validated.answer, validated.confidence
        except ValidationError:
            corrective_suffix = (
                "\n\nYour previous answer did not fit the required output "
                "format. Respond again as a single plain-English sentence "
                "with no extra formatting."
            )
            continue

    return (
        "ERROR: the LLM's output could not be validated against the required "
        "schema after multiple attempts.",
        0.0,
    )


# ---------------------------------------------------------------------------
# Conditional routing edge
# ---------------------------------------------------------------------------
def route_from_intent(state: GraphState) -> str:
    """Routing does not depend on MOCK_LLM — only intent does."""
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve_and_answer", retrieve_and_answer)
    graph.add_node("direct_answer", direct_answer)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_from_intent,
        {
            "retrieve_and_answer": "retrieve_and_answer",
            "direct_answer": "direct_answer",
        },
    )
    graph.add_edge("retrieve_and_answer", END)
    graph.add_edge("direct_answer", END)

    return graph.compile()


def run_query(query: str) -> AskResponse:
    app = build_graph()
    initial_state: GraphState = {
        "query": query,
        "intent": "",
        "retrieved_chunks": [],
        "answer": "",
        "sources": [],
        "confidence": 0.0,
    }
    final_state = app.invoke(initial_state)
    return AskResponse(
        answer=final_state["answer"],
        sources=final_state["sources"],
        confidence=final_state["confidence"],
    )
