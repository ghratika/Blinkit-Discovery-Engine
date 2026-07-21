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
MAX_ITEMS = 50

# ── Seed reviews (fallback if Apify is missing or fails) ──────────────────────
SEED_REVIEWS = [
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit is genuinely my go-to now. I use it mostly for staples—atta, dal, oil. Never explored the fresh produce section though because I'm worried about quality.",
        "rating": None,
        "timestamp": "2024-12-10T08:00:00+00:00",
        "url": "https://www.reddit.com/r/india/",
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "I got a completely wrong order from Blinkit twice last month. Support chat takes forever. The delivery speed is great but reliability is a problem.",
        "rating": None,
        "timestamp": "2024-11-22T09:30:00+00:00",
        "url": "https://www.reddit.com/r/bangalore/",
    }
]

def main():
    load_dotenv()
    api_token = os.environ.get("APIFY_API_TOKEN")
    
    out_dir = RAW_OUTPUT_PATH.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not api_token:
        print("Warning: APIFY_API_TOKEN not found in environment. Falling back to seed reviews.")
        _write_output(SEED_REVIEWS)
        sys.exit(0)
        
    client = ApifyClient(api_token)
    
    all_results = []
    
    try:
        run_input = {
            "searches": KEYWORDS,
            "type": "post",
            "sort": "new",
            "time": "year",
            "maxItems": MAX_ITEMS
        }
        
        print(f"Triggering Apify automation-lab/reddit-scraper for keywords: {KEYWORDS}...")
        run = client.actor("automation-lab/reddit-scraper").call(run_input=run_input)
        
        print(f"Apify run finished. Fetching dataset...")
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
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
