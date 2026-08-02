"""
Play Store Collector — src/collectors/playstore_collector.py

Collects app reviews for Blinkit from the Google Play Store 
using the Apify API (automation-lab/google-play-scraper).
This bypasses GitHub Actions IP blocks for free.

Outputs: data/raw/playstore_raw.json
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from apify_client import ApifyClient

# ── Configuration ─────────────────────────────────────────────────────────────
APPS = {
    "Blinkit": "com.grofers.customerapp",
}
MAX_ITEMS = 500           # fetch up to 500 reviews per run
MONTHS_BACK = 6
RAW_OUTPUT_PATH = Path("data/raw/playstore_raw.json")

# ── Entry Point ───────────────────────────────────────────────────────────────

def run() -> None:
    print("[Play Store] Starting collection via Apify...")
    load_dotenv()
    
    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        print("[Play Store] Error: APIFY_API_TOKEN not found in environment.")
        sys.exit(1)
        
    client = ApifyClient(api_token)
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=MONTHS_BACK * 30)
    
    all_records = []
    
    for platform, app_id in APPS.items():
        print(f"[Play Store] Triggering Apify automation-lab/google-play-scraper for {platform} ({app_id})...")
        
        run_input = {
            "appIds": [app_id],
            "mode": "reviews",
            "maxItems": MAX_ITEMS
        }
        
        try:
            actor_run = client.actor("automation-lab/google-play-scraper").call(run_input=run_input)
            dataset_id = actor_run["defaultDatasetId"] if isinstance(actor_run, dict) else getattr(actor_run, "default_dataset_id")
            
            count = 0
            for item in client.dataset(dataset_id).iterate_items():
                posted_at_str = item.get("date")
                if not posted_at_str:
                    continue
                    
                try:
                    posted_at = datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
                except ValueError:
                    posted_at = datetime.now(tz=timezone.utc)
                    
                if posted_at < cutoff:
                    continue
                    
                all_records.append({
                    "source": "Play Store",
                    "platform": platform,
                    "text": (item.get("text") or "").strip(),
                    "rating": item.get("score"),
                    "timestamp": posted_at.isoformat(),
                    "url": item.get("url") or f"https://play.google.com/store/apps/details?id={app_id}",
                })
                count += 1
                
            print(f"[Play Store] {platform}: {count} reviews fetched.")
            
        except Exception as e:
            print(f"[Play Store] Error fetching {platform} ({app_id}): {e}")

    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"[Play Store] Collected {len(all_records)} records -> {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    run()
