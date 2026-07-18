"""
run_collection.py — Root-level pipeline runner for Phase 2.

Orchestrates all collectors sequentially, then runs the normalizer.

Usage:
    python run_collection.py
"""

from src.collectors import reddit_collector, playstore_collector, appstore_collector, forums_collector
from src.utils import normalizer


def main():
    print("=" * 60)
    print("  Blinkit Discovery Engine — Phase 2: Data Collection")
    print("=" * 60)

    print("\n[1/5] Reddit...")
    reddit_collector.run()

    print("\n[2/5] Play Store...")
    playstore_collector.run()

    print("\n[3/5] App Store...")
    appstore_collector.run()

    print("\n[4/5] Forums & Quora...")
    forums_collector.run()

    print("\n[5/5] Normalizing all raw data...")
    normalizer.run()

    print("\nPhase 2 complete. Normalized data is at data/processed/normalized.json")


if __name__ == "__main__":
    main()
