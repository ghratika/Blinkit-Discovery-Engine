"""
run_ingestion.py — Root-level pipeline runner for Phase 4.

Ingests enriched.json into both the ChromaDB vector store and the
SQLite metadata store.

Usage:
    python run_ingestion.py
    python run_ingestion.py --force   # Reingest from scratch
"""

import sys
from src.storage import vector_store, metadata_store


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  Blinkit Discovery Engine — Phase 4: Storage Ingestion")
    print("=" * 60)

    print("\n[1/2] Ingesting into ChromaDB vector store...")
    vector_store.ingest(force_reingest=force)

    print("\n[2/2] Ingesting into SQLite metadata store...")
    metadata_store.ingest()

    print("\nPhase 4 complete.")
    print("   - Vector index: data/chroma_db/")
    print("   - SQLite DB:    data/processed/reviews.db")


if __name__ == "__main__":
    main()
