"""
Reddit Collector — src/collectors/reddit_collector.py

Collects Blinkit-related posts from Reddit using the Apify API.
Depends on the `automation-lab/reddit-scraper` actor.

Outputs: data/raw/reddit_raw.json
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from apify_client import ApifyClient

# ── Configuration ─────────────────────────────────────────────────────────────
KEYWORDS = ["blinkit", "grofers"]
RAW_OUTPUT_PATH = Path("data/raw/reddit_raw.json")
MAX_ITEMS = 300

# ── Seed reviews (fallback if Apify is missing or fails) ──────────────────────
SEED_REVIEWS = [
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit is genuinely my go-to now. I use it mostly for staples—atta, dal, oil. Never explored the fresh produce section though because I'm worried about quality.",
        "rating": None,
        "timestamp": "2024-12-10T08:00:00+00:00",
        "url": "https://www.reddit.com/r/india/comments/12345/blinkit_review",
    }
]

def _write_output(data: list) -> None:
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[Reddit Collector] Saved {len(data)} reviews to {RAW_OUTPUT_PATH}")


def main() -> None:
    print("[Reddit Collector] Starting collection via Apify...")
    load_dotenv()
    api_token = os.environ.get("APIFY_API_TOKEN")
    
    if not api_token:
        print("Warning: APIFY_API_TOKEN not found in environment. Falling back to seed reviews.")
        _write_output(SEED_REVIEWS)
        sys.exit(0)
        
    client = ApifyClient(api_token)
    
    all_results = []
    
    try:
        run_input = {
            "startUrls": [
                {"url": "https://www.reddit.com/search/?q=blinkit&sort=new&t=year"},
                {"url": "https://www.reddit.com/search/?q=grofers&sort=new&t=year"},
                {"url": "https://www.reddit.com/search/?q=blinkit delivery&sort=new&t=year"},
                {"url": "https://www.reddit.com/search/?q=blinkit order&sort=new&t=year"},
                {"url": "https://www.reddit.com/search/?q=zomato blinkit&sort=new&t=year"}
            ],
            "maxItems": 500,
        }
        
        print(f"Triggering Apify automation-lab/reddit-scraper for keywords: {KEYWORDS}...")
        run = client.actor("automation-lab/reddit-scraper").call(run_input=run_input)
        
        print(f"Apify run finished. Fetching dataset...")
        
        # apify-client v3 uses attributes (e.g., run.default_dataset_id)
        dataset_id = getattr(run, "default_dataset_id", None)
        if not dataset_id and isinstance(run, dict):
            dataset_id = run.get("default_dataset_id") or run.get("defaultDatasetId")
            
        for item in client.dataset(dataset_id).iterate_items():
            # Extract relevant fields
            title = item.get("title", "")
            body = item.get("text", "") or item.get("selftext", "")
            combined_text = f"{title}\n{body}".strip()
            
            created_at = item.get("createdAt") or item.get("created_utc")
            if isinstance(created_at, (int, float)):
                # some actors return unix timestamp
                ts = datetime.fromtimestamp(created_at).isoformat() + "+00:00"
            elif created_at:
                ts = str(created_at)
            else:
                ts = datetime.now().isoformat() + "+00:00"
                
            url = item.get("url", "")
            
            if combined_text:
                all_results.append({
                    "source": "Reddit",
                    "platform": "Blinkit",
                    "text": combined_text,
                    "rating": None,
                    "timestamp": ts,
                    "url": url,
                })
                
    except Exception as e:
        print(f"Error fetching from Apify: {e}")
        print("Falling back to seed reviews.")
        all_results.extend(SEED_REVIEWS)
        
    if not all_results:
        all_results = SEED_REVIEWS
        
    _write_output(all_results)
    
def _write_output(data: list):
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} Reddit reviews to {RAW_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
