"""
filter_reviews.py
=================
Applies three filters to all raw JSON data files AND enriched.json:

  1. Word-count filter  — discard reviews with > 80 words
  2. Genuineness filter — keep only real Blinkit shopping/delivery experiences
                          (uses Groq LLM in batches)
  3. Language filter    — discard Hinglish (mixed Hindi+English) reviews
                          (heuristic first, then LLM confirmation for edge cases)

Files processed (in-place, with .json.bak backups):
  data/raw/bulk_raw.json
  data/raw/playstore_raw.json
  data/raw/reddit_raw.json
  data/raw/forums_raw.json
  data/processed/enriched.json
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Force unbuffered output so logs appear immediately in background tasks
sys.stdout.reconfigure(line_buffering=True)

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
MAX_WORDS = 80
BATCH_SIZE = 5         # reviews per LLM call (small = rock-solid JSON output)
SLEEP_BETWEEN = 1.5    # seconds between Groq calls (rate-limit safety)

# ---------------------------------------------------------------------------
# Common Hinglish indicator words (high-precision list)
# These are Hindi words commonly written in Roman/English script mixed with English.
# ---------------------------------------------------------------------------
HINGLISH_WORDS = {
    "nahi", "nhi", "nahin", "karo", "karta", "karti", "kar", "koi", "kuch",
    "kya", "kyun", "kyunki", "mujhe", "mera", "meri", "mere", "hum", "humne",
    "hamara", "hamari", "aap", "aapka", "aapki", "unka", "unke", "unki",
    "yeh", "ye", "yha", "woh", "wo", "wahi", "wahaan", "iska", "iski", "iske",
    "uska", "uski", "uske", "sab", "sabhi", "bhi", "toh", "lekin",
    "pe", "se", "mein", "main", "mai", "hai", "hain", "tha", "thi",
    "ho", "hua", "hui", "hue", "raha", "rahi", "rahe", "gaya", "gayi",
    "gaye", "liya", "liye", "diya", "diye", "kiya", "kiye", "tera", "teri",
    "tere", "tumhara", "tumhari", "tumhare", "bilkul", "bahut", "bohot",
    "acha", "accha", "achhi", "achha", "sahi", "galat", "bura", "buri",
    "sirf", "thoda", "thodi", "bahot", "jab", "tab", "agar", "phir", "ab",
    "abhi", "pehle", "baad", "pata", "naya", "naye", "purana", "zyada",
    "matlab", "samajh", "dono", "aur", "ya", "ki",
    "ka", "ke", "ko", "ne", "baat", "jagah", "baar", "log", "cheez",
    "cheeze", "paisa", "paise", "wale", "wali",
    "waala", "waali", "wala", "ek", "do", "teen", "char", "paanch",
    "seedha", "seedhi", "chala", "chali", "chale", "laga", "lagi", "lage",
    "milta", "milti", "milte", "rakha", "rakhi", "rakhe",
}


# ---------------------------------------------------------------------------
# FILTER 1: Word count
# ---------------------------------------------------------------------------
def word_count(text: str) -> int:
    return len(text.split())


def passes_word_count(review: dict) -> bool:
    text = review.get("text", "")
    return word_count(text) <= MAX_WORDS


# ---------------------------------------------------------------------------
# FILTER 3: Hinglish heuristic
# ---------------------------------------------------------------------------
def hinglish_score(text: str) -> float:
    """
    Returns fraction of words in text that are Hinglish indicator words.
    """
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in HINGLISH_WORDS)
    return hits / len(words)


def is_hinglish_heuristic(text: str, threshold: float = 0.12) -> bool:
    return hinglish_score(text) >= threshold


GENUINENESS_SYSTEM = (
    "You are a data quality classifier. "
    "You ONLY output a single word: true or false. "
    "No explanation, no code, no extra text."
)

GENUINENESS_USER = (
    "Is this a genuine Blinkit customer review (about ordering, delivery, "
    "product quality, refunds, packaging, customer support, or the app)? "
    "Answer true or false only.\n\n"
    "Answer false ONLY if: completely unrelated topic, pure spam/gibberish "
    "with no Blinkit context, or written in a non-English language.\n\n"
    "Text: {text}\n\nAnswer:"
)

HINGLISH_SYSTEM = (
    "You are a language classifier. "
    "You ONLY output a single word: true or false. "
    "No explanation, no code, no extra text."
)

HINGLISH_USER = (
    "Is this text written in Hinglish "
    "(Hindi words in Roman script mixed with English)? "
    "Answer true or false only.\n\n"
    "Text: {text}\n\nAnswer:"
)


def llm_classify_one(text, system_msg, user_template, model="llama-3.1-8b-instant"):
    """Classify a single text, returning True (keep) or False (drop)."""
    user_msg = user_template.format(text=text[:400])  # cap to save tokens
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                model=model,
                temperature=0.0,
                max_tokens=8,
            )
            raw = resp.choices[0].message.content.strip().lower()
            if "true" in raw:
                return True
            if "false" in raw:
                return False
            print(f"  Ambiguous response '{raw}' attempt {attempt+1}/3, defaulting keep.")
            return True
        except Exception as exc:
            wait = 5 if "429" not in str(exc) else 15
            print(f"  LLM error attempt {attempt+1}/3: {str(exc)[:80]}")
            time.sleep(wait)
    return True  # safe fallback = keep


def llm_batch_filter(texts, system_msg, user_template):
    """Classify a list of texts one by one. Returns list of booleans."""
    results = []
    for text in texts:
        keep = llm_classify_one(text, system_msg, user_template)
        results.append(keep)
        time.sleep(0.3)  # small gap between calls
    return results


# ---------------------------------------------------------------------------
# Main filter pipeline for a single list of review dicts
# ---------------------------------------------------------------------------
def apply_filters(reviews, source_label):
    """
    Apply all 3 filters to a list of review dicts.
    Returns (kept_reviews, stats_dict).
    """
    stats = {
        "original": len(reviews),
        "dropped_word_count": 0,
        "dropped_not_genuine": 0,
        "dropped_hinglish": 0,
        "kept": 0,
    }

    # ---- FILTER 1: Word count ------------------------------------------------
    after_wc = []
    for r in reviews:
        if passes_word_count(r):
            after_wc.append(r)
        else:
            stats["dropped_word_count"] += 1

    print(f"\n[{source_label}] After word-count filter: {len(after_wc)} / {len(reviews)} remain "
          f"({stats['dropped_word_count']} dropped as >80 words)")

    # ---- FILTER 2: Genuineness via LLM --------------------------------------
    print(f"[{source_label}] Running genuineness LLM filter ({len(after_wc)} reviews)...")
    after_genuine = []
    for i, r in enumerate(after_wc):
        text = r.get("text", "")
        keep = llm_classify_one(text, GENUINENESS_SYSTEM, GENUINENESS_USER)
        if keep:
            after_genuine.append(r)
        else:
            stats["dropped_not_genuine"] += 1
        if (i + 1) % 20 == 0:
            print(f"  Processed {i+1}/{len(after_wc)} | kept so far: {len(after_genuine)}")
        time.sleep(0.3)

    print(f"[{source_label}] After genuineness filter: {len(after_genuine)} remain "
          f"({stats['dropped_not_genuine']} dropped)")

    # ---- FILTER 3: Hinglish --------------------------------------------------
    print(f"[{source_label}] Running Hinglish filter...")
    clear_hinglish = []
    edge_cases = []
    clean_english = []

    for r in after_genuine:
        score = hinglish_score(r.get("text", ""))
        if score >= 0.18:          # high confidence — drop without LLM
            clear_hinglish.append(r)
        elif score >= 0.06:        # borderline — confirm with LLM
            edge_cases.append(r)
        else:
            clean_english.append(r)

    stats["dropped_hinglish"] += len(clear_hinglish)
    print(f"  Heuristic clear Hinglish: {len(clear_hinglish)} dropped")

    # LLM confirmation for edge cases
    edge_kept = []
    if edge_cases:
        print(f"  LLM confirming {len(edge_cases)} edge-case texts...")
        for i, r in enumerate(edge_cases):
            text = r.get("text", "")
            is_hl = llm_classify_one(text, HINGLISH_SYSTEM, HINGLISH_USER)
            if is_hl:
                stats["dropped_hinglish"] += 1
            else:
                edge_kept.append(r)
            time.sleep(0.3)

    after_hinglish = clean_english + edge_kept
    print(f"[{source_label}] After Hinglish filter: {len(after_hinglish)} remain "
          f"({stats['dropped_hinglish']} dropped)")

    stats["kept"] = len(after_hinglish)
    return after_hinglish, stats


# ---------------------------------------------------------------------------
# Process each file
# ---------------------------------------------------------------------------
# bulk_raw.json was already filtered in a previous run (763 saved, backup at .bak)
# It is excluded here to avoid double-filtering.
FILES = [
    Path("data/raw/playstore_raw.json"),
    Path("data/raw/reddit_raw.json"),
    Path("data/raw/forums_raw.json"),
    Path("data/processed/enriched.json"),
]

all_stats = {}

for filepath in FILES:
    if not filepath.exists():
        print(f"\n  Skipping {filepath} (not found)")
        continue

    print(f"\n{'='*60}")
    print(f"Processing: {filepath}")
    print(f"{'='*60}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or len(data) == 0:
        print(f"  Empty or non-list file, skipping.")
        continue

    kept, stats = apply_filters(data, filepath.stem)
    all_stats[str(filepath)] = stats

    # Backup original
    backup_path = filepath.with_suffix(".json.bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Save filtered
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    print(f"\n  Saved {len(kept)} reviews -> {filepath}  (backup: {backup_path})")

# ---------------------------------------------------------------------------
# Summary report
# ---------------------------------------------------------------------------
print(f"\n{'='*60}")
print("FILTER SUMMARY")
print(f"{'='*60}")
total_orig = total_kept = total_wc = total_gen = total_hl = 0
for fp, s in all_stats.items():
    pct = 100 * s['kept'] / s['original'] if s['original'] else 0
    print(f"\n{fp}")
    print(f"  Original         : {s['original']}")
    print(f"  Dropped >80 words: {s['dropped_word_count']}")
    print(f"  Dropped genuine  : {s['dropped_not_genuine']}")
    print(f"  Dropped Hinglish : {s['dropped_hinglish']}")
    print(f"  Kept             : {s['kept']}  ({pct:.1f}%)")
    total_orig += s['original']
    total_kept += s['kept']
    total_wc   += s['dropped_word_count']
    total_gen  += s['dropped_not_genuine']
    total_hl   += s['dropped_hinglish']

print(f"\n{'-'*60}")
print(f"  TOTAL Original   : {total_orig}")
print(f"  TOTAL >80 words  : {total_wc}")
print(f"  TOTAL Not genuine: {total_gen}")
print(f"  TOTAL Hinglish   : {total_hl}")
total_pct = 100 * total_kept / total_orig if total_orig else 0
print(f"  TOTAL Kept       : {total_kept}  ({total_pct:.1f}%)")
print(f"{'='*60}\n")
