import json
from collections import Counter
from pathlib import Path

ENRICHED_PATH = Path("data/processed/enriched.json")

def cleanup_segments():
    if not ENRICHED_PATH.exists():
        print(f"File {ENRICHED_PATH} does not exist.")
        return

    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Count all segment occurrences
    segment_counts = Counter()
    for row in data:
        enrichment = row.get("enrichment")
        if enrichment and isinstance(enrichment.get("segment"), list):
            for seg in enrichment["segment"]:
                segment_counts[seg] += 1

    # Identify valid segments (count > 1)
    valid_segments = {seg for seg, count in segment_counts.items() if count > 1}
    removed_count = 0

    # Filter out invalid segments
    for row in data:
        enrichment = row.get("enrichment")
        if enrichment and isinstance(enrichment.get("segment"), list):
            original = enrichment["segment"]
            filtered = [seg for seg in original if seg in valid_segments]
            if len(original) != len(filtered):
                removed_count += (len(original) - len(filtered))
                enrichment["segment"] = filtered

    if removed_count > 0:
        with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully removed {removed_count} single-occurrence segments.")
    else:
        print("No single-occurrence segments found to remove.")

if __name__ == "__main__":
    cleanup_segments()
