import json
from pathlib import Path
from collections import Counter

ENRICHED_PATH = Path("data/processed/enriched.json")

def main():
    if not ENRICHED_PATH.exists():
        print("No enriched data found.")
        return
        
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)
        
    # Tally all segments
    segment_counts = Counter()
    for r in reviews:
        segments = (r.get("enrichment") or {}).get("segment") or []
        for s in segments:
            if s.strip():
                segment_counts[s.strip()] += 1
                
    print(f"Total unique segments before cleanup: {len(segment_counts)}")
    print("Segment Counts:", dict(segment_counts))
    
    # Identify segments to keep
    MIN_REVIEWS = 10
    valid_segments = {s for s, count in segment_counts.items() if count >= MIN_REVIEWS}
    print(f"Keeping {len(valid_segments)} segments with >= {MIN_REVIEWS} occurrences: {valid_segments}")
    
    # Filter reviews
    cleaned_count = 0
    for r in reviews:
        if "enrichment" in r and "segment" in r["enrichment"]:
            old_segments = r["enrichment"]["segment"]
            new_segments = [s.strip() for s in old_segments if s.strip() in valid_segments]
            if len(old_segments) != len(new_segments):
                cleaned_count += 1
            r["enrichment"]["segment"] = new_segments
            
    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2)
        
    print(f"Done. Removed rare segments from {cleaned_count} reviews.")

if __name__ == "__main__":
    main()
