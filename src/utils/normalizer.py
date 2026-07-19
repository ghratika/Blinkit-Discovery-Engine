"""
Normalizer — src/utils/normalizer.py

Reads all raw JSON files from data/raw/, normalizes them into the
Unified Review JSON Schema, and applies:
  - PII stripping (emails, phone numbers)
  - Deduplication by content hash
  - English-language filtering (langdetect)
  - Minimum word count filtering (>= 5 words)

Outputs: data/processed/normalized.json
"""

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from langdetect import detect, LangDetectException

# ── Configuration ─────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
OUTPUT_PATH = Path("data/processed/normalized.json")
MIN_WORD_COUNT = 10   # updated to 10 to filter out spam or generic reviews

# ── PII Stripping ─────────────────────────────────────────────────────────────
_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_PATTERN = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}")
_USERNAME_PATTERN = re.compile(r"u/\w+")   # Reddit usernames


def strip_pii(text: str) -> str:
    text = _EMAIL_PATTERN.sub("[EMAIL]", text)
    text = _PHONE_PATTERN.sub("[PHONE]", text)
    text = _USERNAME_PATTERN.sub("[USER]", text)
    return text.strip()


# ── Language Detection ────────────────────────────────────────────────────────

# Language codes that are acceptable for Blinkit reviews.
# Hinglish (mixed Hindi+English) frequently gets misclassified by langdetect
# as 'hi', 'mr', 'te', 'ta', 'ur', 'af', 'tl' — all acceptable for our corpus.
_ACCEPTED_LANGS = {"en", "hi", "mr", "te", "ta", "kn", "gu", "ur", "af", "tl", "nl"}


def is_english(text: str) -> bool:
    """Returns True if text is in an accepted language (English or Indian language)."""
    try:
        lang = detect(text)
        return lang in _ACCEPTED_LANGS
    except LangDetectException:
        return True   # on detection failure, keep the review


# ── Deduplication ─────────────────────────────────────────────────────────────

def content_hash(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_record(raw: dict) -> dict | None:
    """
    Converts a raw source record into the Unified Review JSON Schema.
    Returns None if the record should be skipped.
    """
    text = strip_pii(raw.get("text") or "")

    # Filter: empty or too short
    if not text.strip() or len(text.split()) < MIN_WORD_COUNT:
        return None

    # Filter: non-English / non-Hinglish
    if not is_english(text):
        return None

    # Normalize timestamp to ISO 8601 UTC string
    ts = raw.get("timestamp")
    if ts is None:
        ts = datetime.now(tz=timezone.utc).isoformat()

    return {
        "id": str(uuid.uuid4()),
        "source": raw.get("source", "Unknown"),
        "platform": raw.get("platform", "Unknown"),
        "text": text,
        "rating": raw.get("rating"),
        "timestamp": ts,
        "url": raw.get("url", ""),
        "enrichment": None,   # filled in by Phase 3
    }


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def run() -> None:
    print("[Normalizer] Starting normalization pipeline...")

    raw_records: list[dict] = []

    # Load all raw JSON files
    raw_files = list(RAW_DIR.glob("*_raw.json"))
    if not raw_files:
        print(f"[Normalizer] No raw files found in {RAW_DIR}. Run collectors first.")
        return

    for path in raw_files:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        print(f"[Normalizer] Loaded {len(data)} records from {path.name}")
        raw_records.extend(data)

    print(f"[Normalizer] Total raw records: {len(raw_records)}")

    # Normalize, deduplicate, and filter
    seen_hashes: set[str] = set()
    normalized: list[dict] = []

    for raw in raw_records:
        record = normalize_record(raw)
        if record is None:
            continue

        h = content_hash(record["text"])
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        normalized.append(record)

    print(f"[Normalizer] After normalization + dedup + filter: {len(normalized)} records")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"[Normalizer] Saved -> {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
