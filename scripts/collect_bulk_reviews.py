"""
scripts/collect_bulk_reviews.py

Multi-source bulk review collector to reach 500+ enriched reviews.
Sources:
  1. MouthShut  — browser-scraped via requests + BeautifulSoup (paginated API)
  2. Play Store  — google-play-scraper (500 reviews)
  3. App Store   — app-store-scraper (200 reviews)
  4. Reddit      — PRAW (existing subreddits)

Run from project root:
    venv\Scripts\python.exe scripts/collect_bulk_reviews.py
"""

import json
import time
import uuid
import re
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))

from dotenv import load_dotenv
load_dotenv()

RAW_EXTRA_PATH   = ROOT / "data" / "raw" / "bulk_raw.json"
NORMALIZED_PATH  = ROOT / "data" / "processed" / "normalized.json"
ENRICHED_PATH    = ROOT / "data" / "processed" / "enriched.json"

RAW_EXTRA_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Load existing IDs to skip duplicates ──────────────────────────────────────
def load_existing_texts() -> set:
    existing = set()
    if ENRICHED_PATH.exists():
        data = json.loads(ENRICHED_PATH.read_text(encoding="utf-8"))
        for r in data:
            existing.add(r.get("text", "").strip()[:120])
    return existing

# ── 1. Play Store — using google-play-scraper ──────────────────────────────────
def collect_playstore(target: int = 500) -> list:
    print(f"\n[PlayStore] Fetching up to {target} reviews for Blinkit...")
    try:
        from google_play_scraper import reviews, Sort
        records = []
        app_id = "com.grofers.customerapp"
        
        # Fetch by star rating to bypass standard limits and get diverse opinions
        for score in [1, 2, 3, 4, 5]:
            if len(records) >= target:
                break
            print(f"[PlayStore] Fetching Blinkit with score={score}...")
            try:
                result, _ = reviews(
                    app_id,
                    lang="en",
                    country="in",
                    sort=Sort.NEWEST,
                    filter_score_with=score,
                    count=150,
                )
                for r in result:
                    text = (r.get("content") or "").strip()
                    if not text or len(text) < 30:
                        continue
                    at = r.get("at")
                    ts = at.strftime("%Y-%m-%dT%H:%M:%SZ") if at else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    records.append({
                        "id": f"ps-bulk-{uuid.uuid4().hex[:12]}",
                        "source": "Play Store",
                        "platform": "Android",
                        "text": text,
                        "rating": float(r.get("score", 0)) if r.get("score") else None,
                        "timestamp": ts,
                        "url": f"https://play.google.com/store/apps/details?id={app_id}",
                    })
            except Exception as e:
                print(f"Error fetching Blinkit score {score}: {e}")
                    
        print(f"[PlayStore] Collected {len(records)} reviews total.")
        return records
    except Exception as e:
        print(f"[PlayStore] Error: {e}")
        return []


# ── 2. App Store — using app-store-scraper ────────────────────────────────────
def collect_appstore(target: int = 200) -> list:
    print(f"\n[AppStore] Fetching up to {target} reviews...")
    try:
        from app_store_scraper import AppStore
        app = AppStore(country="in", app_name="blinkit-10-minute-grocery", app_id="1482901302")
        app.review(how_many=target)
        records = []
        for r in (app.reviews or []):
            text = (r.get("review") or "").strip()
            if not text or len(text) < 30:
                continue
            at = r.get("date")
            ts = at.strftime("%Y-%m-%dT%H:%M:%SZ") if at else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            records.append({
                "id": f"as-bulk-{uuid.uuid4().hex[:12]}",
                "source": "App Store",
                "platform": "iOS",
                "text": text,
                "rating": float(r.get("rating", 0)) if r.get("rating") else None,
                "timestamp": ts,
                "url": "https://apps.apple.com/in/app/blinkit/id1482901302",
            })
        print(f"[AppStore] Collected {len(records)} reviews.")
        return records
    except Exception as e:
        print(f"[AppStore] Error: {e}")
        return []


# ── 3. MouthShut — HTTP API scrape (paginated JSON endpoint) ─────────────────
def collect_mouthshut(target: int = 150) -> list:
    print(f"\n[MouthShut] Fetching up to {target} reviews...")
    try:
        import requests
        from bs4 import BeautifulSoup

        records = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.mouthshut.com/",
        }

        base_url = "https://www.mouthshut.com/product-reviews/blinkit-reviews-925738270"
        page = 1
        while len(records) < target:
            url = base_url if page == 1 else f"{base_url}?page={page}"
            try:
                resp = requests.get(url, headers=headers, timeout=20)
                if resp.status_code != 200:
                    print(f"[MouthShut] HTTP {resp.status_code} on page {page}, stopping.")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                # MouthShut review containers
                review_divs = soup.find_all("div", class_=re.compile(r"review-article|ratingReview|reviewcnt"))
                if not review_divs:
                    # Try alternate selectors
                    review_divs = soup.find_all("div", attrs={"itemprop": "review"})
                if not review_divs:
                    review_divs = soup.find_all("article")

                if not review_divs:
                    print(f"[MouthShut] No reviews found on page {page}. Stopping.")
                    break

                page_count = 0
                for div in review_divs:
                    # Extract text
                    text_el = (div.find(class_=re.compile(r"review-description|more|review-body")) or
                               div.find("p") or div.find(attrs={"itemprop": "description"}))
                    text = text_el.get_text(separator=" ", strip=True) if text_el else ""

                    if not text or len(text) < 40:
                        continue

                    # Rating
                    rating_el = div.find(attrs={"itemprop": "ratingValue"}) or div.find(class_=re.compile(r"rating"))
                    rating = None
                    if rating_el:
                        try:
                            rating_str = rating_el.get("content") or rating_el.get_text(strip=True)
                            rating = float(re.search(r"[\d.]+", rating_str).group())
                        except Exception:
                            pass

                    # Date
                    date_el = div.find(attrs={"itemprop": "datePublished"}) or div.find(class_=re.compile(r"date"))
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    if date_el:
                        try:
                            date_str = date_el.get("content") or date_el.get_text(strip=True)
                            # Try common formats
                            for fmt in ["%B %d, %Y", "%d %B %Y", "%Y-%m-%d", "%b %d, %Y"]:
                                try:
                                    ts = datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%dT%H:%M:%SZ")
                                    break
                                except ValueError:
                                    pass
                        except Exception:
                            pass

                    records.append({
                        "id": f"ms-{uuid.uuid4().hex[:12]}",
                        "source": "MouthShut",
                        "platform": "Web",
                        "text": text[:800],
                        "rating": rating,
                        "timestamp": ts,
                        "url": url,
                    })
                    page_count += 1

                print(f"[MouthShut] Page {page}: {page_count} reviews (total={len(records)})")
                if page_count == 0:
                    break
                page += 1
                time.sleep(1.5)

            except Exception as e:
                print(f"[MouthShut] Error on page {page}: {e}")
                break

        print(f"[MouthShut] Total collected: {len(records)}")
        return records

    except ImportError as e:
        print(f"[MouthShut] Missing library: {e}")
        return []


# ── 4. Reddit — additional subreddits ─────────────────────────────────────────
def collect_reddit_extra(target: int = 60) -> list:
    print(f"\n[Reddit] Fetching extra posts...")
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            user_agent="BlinkitResearch/1.0",
        )
        if not os.getenv("REDDIT_CLIENT_ID"):
            print("[Reddit] No credentials, skipping.")
            return []

        records = []
        queries = [
            ("Blinkit delivery review", "india"),
            ("Blinkit app experience", "IndianFood"),
            ("Blinkit grocery order", "delhi"),
            ("Blinkit quick commerce", "bangalore"),
            ("Blinkit vs zepto", "india"),
        ]
        for query, subreddit in queries:
            if len(records) >= target:
                break
            try:
                sub = reddit.subreddit(subreddit)
                for submission in sub.search(query, limit=20, sort="new"):
                    text = f"{submission.title}. {submission.selftext}".strip()
                    if len(text) < 50:
                        continue
                    ts = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    records.append({
                        "id": f"rd-extra-{uuid.uuid4().hex[:12]}",
                        "source": "Reddit",
                        "platform": "Reddit",
                        "text": text[:600],
                        "rating": None,
                        "timestamp": ts,
                        "url": f"https://reddit.com{submission.permalink}",
                    })
            except Exception as e:
                print(f"[Reddit] Error for {query}: {e}")
        print(f"[Reddit] Collected {len(records)} extra posts.")
        return records
    except Exception as e:
        print(f"[Reddit] Error: {e}")
        return []


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("BULK REVIEW COLLECTION — Target: 500+ enriched reviews")
    print("=" * 60)

    existing_texts = load_existing_texts()
    current_count = len(existing_texts)
    needed = max(0, 500 - current_count)
    print(f"\nCurrently enriched: {current_count} | Need: {needed} more\n")

    all_new = []

    # Collect from all sources
    ms_reviews   = collect_mouthshut(target=150)
    ps_reviews   = collect_playstore(target=450)
    as_reviews   = collect_appstore(target=200)
    rd_reviews   = collect_reddit_extra(target=60)

    all_new = ms_reviews + ps_reviews + as_reviews + rd_reviews

    # De-duplicate against existing AND within new batch
    seen_texts = set(existing_texts)
    deduped = []
    for r in all_new:
        key = r["text"].strip()[:120]
        if key not in seen_texts and len(r["text"].strip()) >= 40:
            seen_texts.add(key)
            deduped.append(r)

    print(f"\n[Dedup] {len(all_new)} collected -> {len(deduped)} unique new reviews")

    # Save new raw
    if deduped:
        RAW_EXTRA_PATH.write_text(
            json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[Saved] {len(deduped)} raw reviews -> {RAW_EXTRA_PATH}")


    # Append to normalized.json
    norm_data = []
    if NORMALIZED_PATH.exists():
        norm_data = json.loads(NORMALIZED_PATH.read_text(encoding="utf-8"))

    existing_norm_ids = {r["id"] for r in norm_data}
    new_norm = [r for r in deduped if r["id"] not in existing_norm_ids]
    norm_data.extend(new_norm)
    NORMALIZED_PATH.write_text(
        json.dumps(norm_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[Saved] normalized.json now has {len(norm_data)} records")
    print(f"\nNext step: run enrichment pipeline to process the {len(new_norm)} new reviews.")
    print("Command: venv\\Scripts\\python.exe -m src.enrichment.enrichment_runner")


if __name__ == "__main__":
    main()
