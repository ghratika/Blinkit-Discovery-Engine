"""
App Store Collector — src/collectors/appstore_collector.py

Collects App Store reviews for Blinkit, Instamart, and Zepto using
Apple's public RSS feed API (no library, no API key, always free).

iTunes RSS endpoint (returns JSON directly):
  https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/sortby=mostrecent/json

Outputs: data/raw/appstore_raw.json
"""

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ── Configuration ─────────────────────────────────────────────────────────────
APPS = {
    "Blinkit": {"app_id": "1459055296"},
}
PAGES_PER_APP = 10          # each page has 50 reviews → up to 500 per app
MONTHS_BACK = 6
COUNTRY = "in"
RAW_OUTPUT_PATH = Path("data/raw/appstore_raw.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BlinkitDiscoveryBot/1.0)"
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_cutoff_date() -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(days=MONTHS_BACK * 30)


def fetch_reviews_page(app_id: str, page: int) -> list[dict]:
    """Fetch one page of reviews from Apple RSS (JSON) endpoint."""
    url = (
        f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/"
        f"page={page}/id={app_id}/sortby=mostrecent/json"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("feed", {}).get("entry", [])
        # First entry is the app metadata, not a review
        if entries and "im:name" in entries[0]:
            entries = entries[1:]
        return entries
    except Exception as e:
        print(f"  [App Store] Error fetching page {page} for app {app_id}: {e}")
        return []


def parse_entry(entry: dict, platform: str, app_id: str) -> dict | None:
    """Convert an iTunes RSS entry dict to our unified schema."""
    try:
        text = entry.get("content", {}).get("label", "").strip()
        rating_str = entry.get("im:rating", {}).get("label", "")
        rating = float(rating_str) if rating_str.isdigit() else None
        updated = entry.get("updated", {}).get("label", "")
        # Parse ISO 8601 date from Apple
        try:
            posted_at = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except Exception:
            posted_at = datetime.now(tz=timezone.utc)

        if not text or len(text.split()) < 5:
            return None

        return {
            "source": "App Store",
            "platform": platform,
            "text": text,
            "rating": rating,
            "timestamp": posted_at.isoformat(),
            "url": f"https://apps.apple.com/{COUNTRY}/app/id{app_id}",
        }
    except Exception:
        return None


def collect_reviews() -> list[dict]:
    cutoff = get_cutoff_date()
    records = []

    for platform, meta in APPS.items():
        app_id = meta["app_id"]
        app_records = []
        print(f"[App Store] Fetching reviews for {platform} (id={app_id})...")
        for page in range(1, PAGES_PER_APP + 1):
            entries = fetch_reviews_page(app_id, page)
            if not entries:
                break   # no more pages

            for entry in entries:
                record = parse_entry(entry, platform, app_id)
                if record is None:
                    continue
                # Date filter
                try:
                    posted_at = datetime.fromisoformat(record["timestamp"])
                    if posted_at < cutoff:
                        continue
                except Exception:
                    pass
                app_records.append(record)

            time.sleep(0.5)   # polite delay between pages

        print(f"[App Store] {platform}: {len(app_records)} reviews collected")
        records.extend(app_records)

    return records


# ── Entry Point ───────────────────────────────────────────────────────────────

def run() -> None:
    print("[App Store] Starting collection via iTunes RSS API...")
    records = collect_reviews()

    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"[App Store] Collected {len(records)} records -> {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    run()
