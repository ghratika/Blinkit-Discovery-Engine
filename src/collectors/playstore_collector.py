"""
Play Store Collector — src/collectors/playstore_collector.py

Collects app reviews for Blinkit, Instamart, and Zepto from the
Google Play Store using the google-play-scraper library (free).

Outputs: data/raw/playstore_raw.json
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from google_play_scraper import reviews, Sort  # pip: google-play-scraper

# ── Configuration ─────────────────────────────────────────────────────────────
APPS = {
    "Blinkit": "com.grofers.customerapp",
}
REVIEWS_PER_APP = 500           # fetch up to 500 reviews per run
MONTHS_BACK = 6
RAW_OUTPUT_PATH = Path("data/raw/playstore_raw.json")

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_cutoff_date():
    return datetime.now(tz=timezone.utc) - timedelta(days=MONTHS_BACK * 30)


def collect_reviews() -> list[dict]:
    cutoff = get_cutoff_date()
    records = []

    for platform, app_id in APPS.items():
        try:
            result, _ = reviews(
                app_id,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=REVIEWS_PER_APP,
            )

            for r in result:
                posted_at = r.get("at")
                if posted_at is None:
                    continue
                # google-play-scraper returns naive datetimes — treat as UTC
                if posted_at.replace(tzinfo=timezone.utc) < cutoff:
                    continue

                records.append({
                    "source": "Play Store",
                    "platform": platform,
                    "text": (r.get("content") or "").strip(),
                    "rating": r.get("score"),
                    "timestamp": posted_at.replace(tzinfo=timezone.utc).isoformat(),
                    "url": f"https://play.google.com/store/apps/details?id={app_id}",
                })

            print(f"[Play Store] {platform}: {len(result)} reviews fetched")
        except Exception as e:
            print(f"[Play Store] Error fetching {platform} ({app_id}): {e}")

    return records


# ── Entry Point ───────────────────────────────────────────────────────────────

def run() -> None:
    print("[Play Store] Starting collection...")
    records = collect_reviews()

    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"[Play Store] Collected {len(records)} records -> {RAW_OUTPUT_PATH}")


if __name__ == "__main__":
    run()
