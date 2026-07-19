"""
Vector Store — src/storage/vector_store.py

Ingests enriched reviews into ChromaDB using local sentence-transformer
embeddings (all-MiniLM-L6-v2). No API cost. Persists to data/chroma_db/.
"""

import json
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

# ── Configuration ─────────────────────────────────────────────────────────────
ENRICHED_PATH = Path("data/processed/enriched.json")
CHROMA_DB_PATH = Path("data/chroma_db")
COLLECTION_NAME = "blinkit_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INGEST_BATCH_SIZE = 50

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# ── Lazy Singletons ───────────────────────────────────────────────────────────
_client: Optional[chromadb.PersistentClient] = None
_model: Optional[SentenceTransformer] = None
_collection = None


def _get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if HAS_STREAMLIT:
        @st.cache_resource
        def cached_client():
            CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        return cached_client()
    else:
        if _client is None:
            CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
        return _client


def _get_embedding_model() -> SentenceTransformer:
    global _model
    if HAS_STREAMLIT:
        @st.cache_resource
        def cached_model():
            print(f"[VectorStore] Loading embedding model '{EMBEDDING_MODEL}'...")
            return SentenceTransformer(EMBEDDING_MODEL)
        return cached_model()
    else:
        if _model is None:
            print(f"[VectorStore] Loading embedding model '{EMBEDDING_MODEL}'...")
            _model = SentenceTransformer(EMBEDDING_MODEL)
        return _model


def get_collection():
    """Returns (or creates) the ChromaDB collection."""
    global _collection
    if HAS_STREAMLIT:
        @st.cache_resource
        def cached_collection():
            client = _get_chroma_client()
            return client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return cached_collection()
    else:
        if _collection is None:
            client = _get_chroma_client()
            _collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return _collection


# ── Metadata Builder ──────────────────────────────────────────────────────────

def _build_metadata(review: dict) -> dict:
    """
    Converts a review record to a flat ChromaDB metadata dict.
    ChromaDB metadata values must be str, int, or float (no lists/None).
    """
    enrichment = review.get("enrichment") or {}
    themes = enrichment.get("themes") or []
    segments = enrichment.get("segment") or []
    unmet = enrichment.get("unmet_needs") or []

    return {
        "source": review.get("source", "Unknown"),
        "platform": review.get("platform", "Unknown"),
        "rating": float(review["rating"]) if review.get("rating") is not None else -1.0,
        "timestamp": review.get("timestamp", ""),
        "url": review.get("url", ""),
        "sentiment": enrichment.get("sentiment", "Unknown"),
        "themes": ", ".join(themes),
        "segment": ", ".join(segments),
        "unmet_needs": ", ".join(unmet),
    }


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest(force_reingest: bool = False) -> None:
    """
    Reads enriched.json and indexes all records into ChromaDB.

    Args:
        force_reingest: If True, deletes and recreates the collection first.
    """
    if not ENRICHED_PATH.exists():
        print(f"[VectorStore] {ENRICHED_PATH} not found. Run Phase 3 first.")
        return

    client = _get_chroma_client()
    model = _get_embedding_model()

    if force_reingest:
        print("[VectorStore] Force reingest: deleting existing collection...")
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        global _collection
        _collection = None

    collection = get_collection()
    existing_count = collection.count()
    print(f"[VectorStore] Collection has {existing_count} existing records.")

    with open(ENRICHED_PATH, encoding="utf-8") as f:
        reviews = json.load(f)

    # Filter out records without enrichment or with errors
    valid = [r for r in reviews if r.get("enrichment") and not r.get("enrichment_error")]
    print(f"[VectorStore] {len(valid)} valid enriched reviews to index.")

    # Skip already-indexed IDs
    existing_ids: set[str] = set()
    if existing_count > 0:
        result = collection.get(include=[])
        existing_ids = set(result["ids"])

    to_index = [r for r in valid if r["id"] not in existing_ids]
    print(f"[VectorStore] {len(to_index)} new reviews to embed and index.")

    if not to_index:
        print("[VectorStore] Nothing new to index.")
        return

    # Batch embed and insert
    for i in range(0, len(to_index), INGEST_BATCH_SIZE):
        batch = to_index[i : i + INGEST_BATCH_SIZE]
        texts = [r["text"] for r in batch]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids=[r["id"] for r in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[_build_metadata(r) for r in batch],
        )
        print(f"[VectorStore] Indexed {min(i + INGEST_BATCH_SIZE, len(to_index))}/{len(to_index)} records...")

    print(f"[VectorStore] Ingestion complete. Total records: {collection.count()}")


# ── Query Interface ───────────────────────────────────────────────────────────

def query(
    query_text: str,
    top_k: int = 5,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Semantic search against the ChromaDB collection.

    Returns a list of result dicts with 'text', 'metadata', and 'distance'.
    """
    model = _get_embedding_model()
    collection = get_collection()

    query_embedding = model.encode([query_text]).tolist()

    kwargs: dict = {
        "query_embeddings": query_embedding,
        "n_results": min(top_k, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})

    return output


if __name__ == "__main__":
    ingest()
