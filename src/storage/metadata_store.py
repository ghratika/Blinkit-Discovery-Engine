"""
Metadata Store — src/storage/metadata_store.py

SQLite-backed store for full enriched review records.
Supports structured filtering (by source, platform, sentiment, date range)
used by the Streamlit dashboard.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ── Configuration ─────────────────────────────────────────────────────────────
ENRICHED_PATH = Path("data/processed/enriched.json")
DB_PATH = Path("data/processed/reviews.db")
TABLE_NAME = "reviews"

# ── Schema ────────────────────────────────────────────────────────────────────
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id          TEXT PRIMARY KEY,
    source      TEXT,
    platform    TEXT,
    text        TEXT,
    rating      REAL,
    timestamp   TEXT,
    url         TEXT,
    sentiment   TEXT,
    themes      TEXT,    -- JSON list stored as string
    segment     TEXT,    -- JSON list stored as string
    unmet_needs TEXT     -- JSON list stored as string
);
"""

# ── Connection Manager ────────────────────────────────────────────────────────

@contextmanager
def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── Initialization ────────────────────────────────────────────────────────────

def init_db() -> None:
    with _get_conn() as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    print(f"[MetadataStore] Database initialized at {DB_PATH}")


# ── Ingestion ─────────────────────────────────────────────────────────────────

def ingest() -> None:
    """Load enriched.json into SQLite, skipping already-existing IDs."""
    if not ENRICHED_PATH.exists():
        print(f"[MetadataStore] {ENRICHED_PATH} not found. Run Phase 3 first.")
        return

    init_db()

    with open(ENRICHED_PATH, encoding="utf-8") as f:
        reviews = json.load(f)

    with _get_conn() as conn:
        inserted = 0
        skipped = 0
        for r in reviews:
            enrichment = r.get("enrichment") or {}
            try:
                conn.execute(
                    f"""
                    INSERT OR IGNORE INTO {TABLE_NAME}
                        (id, source, platform, text, rating, timestamp, url,
                         sentiment, themes, segment, unmet_needs)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r.get("id"),
                        r.get("source"),
                        r.get("platform"),
                        r.get("text"),
                        r.get("rating"),
                        r.get("timestamp"),
                        r.get("url"),
                        enrichment.get("sentiment"),
                        json.dumps(enrichment.get("themes") or []),
                        json.dumps(enrichment.get("segment") or []),
                        json.dumps(enrichment.get("unmet_needs") or []),
                    ),
                )
                if conn.execute("SELECT changes()").fetchone()[0]:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"[MetadataStore] Error inserting record {r.get('id')}: {e}")

        conn.commit()
    print(f"[MetadataStore] Ingestion done. Inserted={inserted}, Skipped={skipped}")


# ── Query Helpers ─────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for field in ("themes", "segment", "unmet_needs"):
        try:
            d[field] = json.loads(d[field]) if d[field] else []
        except (json.JSONDecodeError, TypeError):
            d[field] = []
    return d


def get_all_reviews(
    platform: Optional[str] = None,
    source: Optional[str] = None,
    sentiment: Optional[str] = None,
    days_back: Optional[int] = None,
    limit: int = 500,
) -> list[dict]:
    """Fetch reviews with optional filters. Returns list of dicts."""
    clauses = []
    params: list = []

    if platform:
        clauses.append("platform = ?")
        params.append(platform)
    if source:
        clauses.append("source = ?")
        params.append(source)
    if sentiment:
        clauses.append("sentiment = ?")
        params.append(sentiment)
    if days_back:
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days_back)).isoformat()
        clauses.append("timestamp >= ?")
        params.append(cutoff)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM {TABLE_NAME} {where} ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_theme_frequency(days_back: Optional[int] = None) -> dict[str, int]:
    """Returns a {theme: count} dict across all reviews (optionally filtered by recency)."""
    reviews = get_all_reviews(days_back=days_back, limit=10000)
    freq: dict[str, int] = {}
    for r in reviews:
        for theme in r.get("themes") or []:
            freq[theme] = freq.get(theme, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_sentiment_distribution(days_back: Optional[int] = None) -> dict[str, int]:
    """Returns {Positive: N, Neutral: N, Negative: N}."""
    reviews = get_all_reviews(days_back=days_back, limit=10000)
    dist: dict[str, int] = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in reviews:
        s = r.get("sentiment")
        if s in dist:
            dist[s] += 1
    return dist


def get_source_distribution(days_back: Optional[int] = None) -> dict[str, int]:
    """Returns {source: count}."""
    reviews = get_all_reviews(days_back=days_back, limit=10000)
    dist: dict[str, int] = {}
    for r in reviews:
        src = r.get("source", "Unknown")
        dist[src] = dist.get(src, 0) + 1
    return dist


def get_all_unmet_needs(limit: int = 500) -> list[dict]:
    """
    Returns a ranked list of unmet needs with occurrence counts.
    [{"need": "...", "count": N}, ...]
    """
    reviews = get_all_reviews(limit=10000)
    needs_count: dict[str, int] = {}
    for r in reviews:
        for need in r.get("unmet_needs") or []:
            if need.strip():
                needs_count[need.strip()] = needs_count.get(need.strip(), 0) + 1
    ranked = sorted(needs_count.items(), key=lambda x: x[1], reverse=True)
    return [{"need": n, "count": c} for n, c in ranked[:limit]]


def get_segment_theme_breakdown() -> dict[str, dict[str, int]]:
    """
    Returns {segment: {theme: count}} for building the segment breakdown panel.
    """
    reviews = get_all_reviews(limit=10000)
    breakdown: dict[str, dict[str, int]] = {}
    for r in reviews:
        themes = r.get("themes") or []
        for seg in r.get("segment") or []:
            if seg not in breakdown:
                breakdown[seg] = {}
            for t in themes:
                breakdown[seg][t] = breakdown[seg].get(t, 0) + 1
    return breakdown


def get_reviews_by_theme(theme: str, limit: int = 20) -> list[dict]:
    """Fetch reviews where the themes field contains the given theme (SQLite LIKE)."""
    sql = f"SELECT * FROM {TABLE_NAME} WHERE themes LIKE ? ORDER BY timestamp DESC LIMIT ?"
    with _get_conn() as conn:
        rows = conn.execute(sql, [f"%{theme}%", limit]).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_review_count() -> int:
    with _get_conn() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]


if __name__ == "__main__":
    ingest()
