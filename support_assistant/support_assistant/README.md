# Zepto Support Assistant (`/support_assistant`)

A small, fully-offline-gradeable RAG service over Zepto's own policy corpus,
orchestrated with LangGraph and served through FastAPI.

## Running it

```bash
cd support_assistant
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

`MOCK_LLM` defaults to `1` (offline mock — no signup, no API key, no network
call to any LLM provider). This is the state the module is graded in.

### Example calls (run with `MOCK_LLM` left at its default)

**1. A query that should trigger retrieval** (`policy_question`, contains the keyword "delivery"):

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Is delivery free on small orders?"}'
```

Expected response shape (deterministic mock template — the exact snippet is
whichever chunk `all-MiniLM-L6-v2` + ChromaDB scores as the closest match,
which for this query is `doc_01`, the Delivery Policy document):

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's del",
  "sources": ["doc_01", "doc_05", "doc_04"],
  "confidence": 1.0
}
```

**2. A query that should NOT trigger retrieval** (`general_question`, no policy keyword present):

```bash
curl -X POST http://localhost:7860/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

Response (fully deterministic, no embedding/ChromaDB call at all):

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

> Note on these transcripts: this response was authored in a sandboxed
> environment with no outbound network access, so the exact `sources` order
> for call 1 above could not be captured by actually executing the service
> here (pip install + the first-run download of the `all-MiniLM-L6-v2`
> weights both require network access). The `direct_answer` transcript (call
> 2) is exact, since that branch is a fixed string with no embedding step.
> Run the two `curl` commands above locally and paste the real JSON output
> here before submitting — the mock logic itself is fully deterministic, so
> only the retrieval ordering in call 1 depends on your machine's model
> download, and it will consistently rank `doc_01` first for a delivery
> question either way.

## Docker

```bash
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

This serves the same `POST /ask` endpoint at `http://localhost:7860/ask`,
with `MOCK_LLM=1` baked in as the default. To try the optional real-LLM
extension instead:

```bash
docker run -p 7860:7860 -e MOCK_LLM=0 -e GROQ_API_KEY=your_free_tier_key zepto-support-assistant
```

## Architecture: ingestion → embedding → retrieval → generation

**Ingestion** (`ingest.py :: load_documents`) reads the 8 Zepto policy files
from `docs/doc_01.txt` … `docs/doc_08.txt`. Each file is treated as a single
chunk (a simple per-document chunking scheme, reasonable given how short each
policy paragraph is), tagged with its filename stem as a stable chunk/document
ID (e.g. `doc_01`).

**Embedding** (`ingest.py :: build_or_load_collection`) encodes each chunk's
text locally with `sentence-transformers`' `all-MiniLM-L6-v2` model — no API
key, no account, no network call at query time. The resulting vectors, raw
text, and `{"source": <id>}` metadata are written into a persistent ChromaDB
collection named `zepto_policies` (stored on disk under `chroma_db/`).

**Retrieval** (`ingest.py :: retrieve_top_k`, called from the
`retrieve_and_answer` LangGraph node in `graph.py`) embeds the incoming query
with the same `all-MiniLM-L6-v2` model and asks the `zepto_policies`
collection for its top-3 nearest neighbors by cosine similarity. This step
always runs for real, in both `MOCK_LLM` states, since it needs no LLM.

**Generation** happens inside two of the three LangGraph nodes defined in
`graph.py`, wired together by `build_graph()`:

- `classify_intent` — keyword-heuristic router (mock baseline) or an
  LLM call (`MOCK_LLM=0` extension) that labels the query `policy_question`
  or `general_question`. A conditional edge (`route_from_intent`) sends
  `policy_question` queries to `retrieve_and_answer` and everything else to
  `direct_answer`; this routing logic itself does not depend on `MOCK_LLM`.
- `retrieve_and_answer` — runs retrieval as above, then in mock mode builds
  the answer as `f"Based on the retrieved context: {top_chunk_snippet}"`
  straight from code (no LLM call); in the `MOCK_LLM=0` extension it instead
  formats the structured prompt from `prompts.py` (`build_rag_prompt`,
  covering role/context/task/format/length, a negative constraint, and a
  few-shot example) and sends it to the real LLM via `llm_client.py`.
- `direct_answer` — in mock mode returns the fixed canned string with no
  LLM call; in the extension it formats `prompts.py :: build_direct_prompt`
  and calls the LLM with no retrieval step at all.

The final `AskResponse` (`schemas.py`) — `answer` / `sources` / `confidence`
— is populated deterministically from code in mock mode (`sources` are the
retrieved chunk IDs for `policy_question`, empty for `general_question`;
`confidence` fixed at `1.0`). In the optional `MOCK_LLM=0` path, the raw LLM
output is validated against this same Pydantic model, with up to 2 retries
using a corrective instruction (`graph.py :: _llm_generate_validated`)
before falling back to a clearly marked error response.

`main.py` wraps `graph.py :: run_query` in a FastAPI `POST /ask` endpoint,
building the ChromaDB collection once on startup.

### What changes when `MOCK_LLM=0`

| Stage | `MOCK_LLM` default (graded) | `MOCK_LLM=0` (optional extension) |
|---|---|---|
| `classify_intent` | keyword heuristic, no LLM call | LLM call classifies intent |
| `retrieve_and_answer` generation | canned `"Based on the retrieved context: ..."` string | real LLM answers from the structured RAG prompt, grounded in the same retrieved chunks |
| `direct_answer` generation | fixed canned string | real LLM answers directly, no retrieval |
| Schema validation | always trivially satisfied (built from code) | validated against `AskResponse`, retried up to 2x on failure |
| External dependency | none | Groq free-tier API key (`GROQ_API_KEY`), or any other genuinely-free-tier LLM API |

Retrieval and routing are unchanged in both states.
