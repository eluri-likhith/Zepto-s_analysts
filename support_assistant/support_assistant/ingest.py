"""
Ingestion stage of the RAG pipeline.

- Loads the 8 Zepto policy documents from docs/.
- Chunks each document (one chunk per document — they are short policy
  paragraphs, so per-document chunking is a reasonable, simple scheme).
- Embeds each chunk locally with sentence-transformers (all-MiniLM-L6-v2).
- Stores the embeddings + text + metadata in a persistent ChromaDB collection.

No API key and no network call to any LLM/embedding provider is required:
sentence-transformers downloads its model weights once from the public
HuggingFace hub the first time it runs, then everything is local.
"""

import glob
import os

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "zepto_policies"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def load_documents() -> list[dict]:
    """Load each docs/doc_XX.txt file as a single chunk."""
    chunks = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "doc_*.txt"))):
        doc_id = os.path.splitext(os.path.basename(path))[0]  # e.g. "doc_01"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        chunks.append({"id": doc_id, "text": text})
    return chunks


def build_or_load_collection() -> chromadb.api.models.Collection.Collection:
    """
    Create (or reopen) the ChromaDB collection and (re)populate it with the
    embedded corpus. Safe to call repeatedly — it recreates the collection
    each time to keep ingestion idempotent and the demo simple.
    """
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Idempotent: drop and recreate so re-running ingestion never duplicates.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    chunks = load_documents()
    embedder = get_embedder()
    embeddings = embedder.encode([c["text"] for c in chunks]).tolist()

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[{"source": c["id"]} for c in chunks],
    )
    return collection


def get_collection() -> chromadb.api.models.Collection.Collection:
    """Fetch the existing collection, building it if it doesn't exist yet."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        return build_or_load_collection()


def retrieve_top_k(query: str, k: int = 3) -> list[dict]:
    """
    Embed the query and retrieve the top-k most similar chunks from ChromaDB
    (cosine similarity, via Chroma's default HNSW index). This step always
    runs for real, in both MOCK_LLM=1 and MOCK_LLM=0 modes.
    """
    collection = get_collection()
    embedder = get_embedder()
    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(query_embeddings=query_embedding, n_results=k)

    retrieved = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for chunk_id, text, distance in zip(ids, docs, distances):
        retrieved.append({"id": chunk_id, "text": text, "distance": distance})
    return retrieved


if __name__ == "__main__":
    build_or_load_collection()
    print(f"Ingested corpus into ChromaDB collection '{COLLECTION_NAME}' at {CHROMA_DIR}")
