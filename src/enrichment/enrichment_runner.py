"""
Batch Enrichment Runner — src/enrichment/enrichment_runner.py

Processes normalized reviews using the Groq API in batches to append
metadata (themes, sentiment, segments, unmet needs).
"""

import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from src.enrichment.prompts import ENRICHMENT_SYSTEM_PROMPT, ENRICHMENT_USER_PROMPT_TEMPLATE

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
INPUT_PATH = Path("data/processed/normalized.json")
OUTPUT_PATH = Path("data/processed/enriched.json")
BATCH_SIZE = 10
DELAY_BETWEEN_BATCHES = 2  # seconds
MAX_TARGET_REVIEWS = 550
MAX_RETRIES = 5
MODEL_NAME = "llama-3.1-8b-instant"

# ── Groq Setup ────────────────────────────────────────────────────────────────
def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key.endswith("here"):
        raise ValueError("GROQ_API_KEY not configured correctly in .env")
    return Groq(api_key=api_key)


# ── Enrichment Logic ──────────────────────────────────────────────────────────

def extract_json(response_text: str) -> dict:
    """Attempts to parse JSON from the LLM response, even if wrapped in markdown."""
    match = re.search(r'\{.*\}', response_text.strip(), re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON from response: {response_text}") from e


def enrich_review(client: Groq, review_text: str) -> dict:
    prompt = ENRICHMENT_USER_PROMPT_TEMPLATE.format(review_text=review_text)
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": ENRICHMENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model=MODEL_NAME,
                temperature=0.0,
                max_tokens=256,
            )
            response_text = chat_completion.choices[0].message.content
            return extract_json(response_text)
            
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many requests" in error_str:
                if attempt < MAX_RETRIES:
                    wait_time = 5 * (2 ** attempt)
                    print(f"  [Rate Limit] 429 hit. Waiting {wait_time}s before retry {attempt+1}/{MAX_RETRIES}...")
                    time.sleep(wait_time)
                else:
                    return {"error": "Rate limit max retries exceeded"}
            else:
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                else:
                    return {"error": str(e)}
                    
    return {"error": "Unknown error"}


# ── Main Runner ───────────────────────────────────────────────────────────────

def run() -> None:
    if not INPUT_PATH.exists():
        print(f"[Enrichment] Input file {INPUT_PATH} not found. Run Phase 2 first.")
        return

    client = get_client()

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    enriched_reviews = []
    processed_ids = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            try:
                enriched_reviews = json.load(f)
                processed_ids = {r["id"] for r in enriched_reviews}
                print(f"[Enrichment] Resuming from {len(enriched_reviews)} previously enriched records.")
            except json.JSONDecodeError:
                print("[Enrichment] Corrupt output file found. Starting fresh.")
                
    reviews_to_process = [r for r in reviews if r["id"] not in processed_ids]
    print(f"[Enrichment] {len(reviews_to_process)} reviews queued for processing out of {len(reviews)} total.")

    if not reviews_to_process:
        print("[Enrichment] All reviews already processed.")
        return

    processed_count = 0
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    for review in reviews_to_process:
        if len(enriched_reviews) >= 600:
            print("[Enrichment] Reached target of 600 reviews. Stopping early.")
            break
            
        result = enrich_review(client, review["text"])
        if "error" in result:
            review["enrichment_error"] = result["error"]
            review["enrichment"] = None
        else:
            review["enrichment"] = result
            
        enriched_reviews.append(review)
        processed_count += 1
        
        # Checkpoint save
        if processed_count % 10 == 0:
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(enriched_reviews, f, ensure_ascii=False, indent=2)
            print(f"  [Checkpoint] Saved {len(enriched_reviews)} records to {OUTPUT_PATH}")

        # Sleep to respect 30 RPM limit on free tier
        time.sleep(2.1)

    # Final save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched_reviews, f, ensure_ascii=False, indent=2)
    print(f"[Enrichment] Complete! Final dataset saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
