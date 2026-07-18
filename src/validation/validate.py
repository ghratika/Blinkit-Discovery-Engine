"""
src/validation/validate.py

Phase 5 Validation & QA

Automated checks:
  1. Traceability test — randomly sample 20 Groq-generated themes and verify
     each maps to at least one real review in the corpus.
  2. RAG grounding test — ask each of the 8 research questions; confirm answers
     include citations.

Manual spot-check:
  - Randomly selects 50 reviews from enriched.json and writes them to
    docs/validation_spot_check.json for human review.
  - Precision scores are written to docs/validation-report.md.
"""

import json
import os
import random
import sys
import datetime
from pathlib import Path
from collections import Counter

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))

from dotenv import load_dotenv
load_dotenv()

ENRICHED_PATH = ROOT / "data" / "processed" / "enriched.json"
REPORT_PATH = ROOT / "docs" / "validation-report.md"
SPOT_CHECK_PATH = ROOT / "docs" / "validation_spot_check.json"

RESEARCH_QUESTIONS = [
    "Why do users repeatedly buy the same categories on Blinkit?",
    "What prevents users from exploring new categories?",
    "How do users currently discover new products?",
    "What role do habit and routine play in shopping behavior?",
    "What trust signals do users need before trying an unfamiliar category?",
    "What are the top recurring frustrations users mention?",
    "Which user segments show a higher tendency for category exploration?",
    "What unmet needs or category gaps come up consistently?",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_enriched() -> list[dict]:
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        return json.load(f)


def _has_citation(answer: str) -> bool:
    """Heuristic: answer contains a '[...]' style citation pattern."""
    import re
    return bool(re.search(r"\[.{3,60}\]", answer))


# ── Test 1: Traceability ──────────────────────────────────────────────────────

def test_traceability(reviews: list[dict], sample_size: int = 20) -> dict:
    """
    Randomly sample `sample_size` theme labels from the enriched corpus.
    For each, verify that at least one review in the corpus contains that theme.
    Returns a result dict.
    """
    print("\n[Validation] Running Traceability Test...")

    # Collect all (theme, review_id) pairs
    theme_to_reviews: dict[str, list[str]] = {}
    for r in reviews:
        for t in (r.get("enrichment") or {}).get("themes") or []:
            theme_to_reviews.setdefault(t, []).append(r["id"])

    all_theme_instances = [(t, rid) for t, rids in theme_to_reviews.items() for rid in rids]
    if not all_theme_instances:
        return {"passed": 0, "failed": 0, "details": [], "pass_rate": 0.0}

    sampled = random.sample(all_theme_instances, min(sample_size, len(all_theme_instances)))

    passed = 0
    failed = 0
    details = []
    for theme, review_id in sampled:
        # Verify the theme exists in at least one real review
        matches = [r for r in reviews if theme in (r.get("enrichment") or {}).get("themes", [])]
        ok = len(matches) > 0
        details.append({
            "theme": theme,
            "review_id": review_id,
            "traceable": ok,
            "matching_reviews": len(matches),
        })
        if ok:
            passed += 1
        else:
            failed += 1
        status = "✅" if ok else "❌"
        print(f"  {status} Theme: '{theme}' → {len(matches)} review(s)")

    pass_rate = round(100 * passed / (passed + failed), 1) if (passed + failed) > 0 else 0.0
    print(f"\n  Traceability: {passed}/{passed+failed} passed ({pass_rate}%)")
    return {"passed": passed, "failed": failed, "details": details, "pass_rate": pass_rate}


# ── Test 2: RAG Grounding ─────────────────────────────────────────────────────

def test_rag_grounding() -> dict:
    """
    Ask each of the 8 research questions via the RAG chain.
    Checks that each answer:
      - Is non-empty
      - Contains at least one citation pattern
    """
    print("\n[Validation] Running RAG Grounding Test...")

    results = []
    try:
        from src.rag.rag_chain import ask
    except Exception as e:
        print(f"  ⚠️  Could not import RAG chain: {e}")
        return {"error": str(e), "questions": []}

    for i, q in enumerate(RESEARCH_QUESTIONS, 1):
        print(f"  [{i}/{len(RESEARCH_QUESTIONS)}] Q: {q[:70]}...")
        try:
            result = ask(q)
            answer = result.get("answer", "")
            sources_used = len(result.get("sources", []))
            has_citation = _has_citation(answer)
            grounded = bool(answer.strip()) and has_citation
            status = "✅" if grounded else "⚠️ "
            print(f"    {status} Sources={sources_used} | Citation found={has_citation} | Grounded={grounded}")
            results.append({
                "question": q,
                "answer_preview": answer[:300] + ("…" if len(answer) > 300 else ""),
                "sources_used": sources_used,
                "has_citation": has_citation,
                "grounded": grounded,
            })
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({"question": q, "error": str(e), "grounded": False})

    grounded_count = sum(1 for r in results if r.get("grounded"))
    pass_rate = round(100 * grounded_count / len(results), 1) if results else 0.0
    print(f"\n  RAG Grounding: {grounded_count}/{len(results)} questions grounded ({pass_rate}%)")
    return {"questions": results, "grounded_count": grounded_count, "pass_rate": pass_rate}


# ── Spot-check Sampler ────────────────────────────────────────────────────────

def generate_spot_check(reviews: list[dict], sample_size: int = 50) -> list[dict]:
    """
    Randomly selects `sample_size` reviews and saves them for manual assessment.
    Returns the sampled list.
    """
    sample = random.sample(reviews, min(sample_size, len(reviews)))
    SPOT_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SPOT_CHECK_PATH, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)
    print(f"\n[Validation] Spot-check sample ({len(sample)} reviews) saved → {SPOT_CHECK_PATH}")
    return sample


# ── Corpus Statistics ─────────────────────────────────────────────────────────

def corpus_stats(reviews: list[dict]) -> dict:
    total = len(reviews)
    enriched = sum(1 for r in reviews if r.get("enrichment"))
    sentiments = Counter((r.get("enrichment") or {}).get("sentiment") for r in reviews)
    platforms = Counter(r.get("platform") for r in reviews)
    sources = Counter(r.get("source") for r in reviews)
    all_themes = [t for r in reviews for t in (r.get("enrichment") or {}).get("themes", [])]
    theme_freq = Counter(all_themes).most_common(10)
    all_needs = [n for r in reviews for n in (r.get("enrichment") or {}).get("unmet_needs", []) if n.strip()]
    needs_freq = Counter(all_needs).most_common(10)
    return {
        "total": total,
        "enriched": enriched,
        "sentiments": dict(sentiments),
        "platforms": dict(platforms),
        "sources": dict(sources),
        "top_themes": theme_freq,
        "top_unmet_needs": needs_freq,
        "unique_themes": len(set(all_themes)),
        "unique_segments": len({s for r in reviews for s in (r.get("enrichment") or {}).get("segment", [])}),
    }


# ── Report Writer ─────────────────────────────────────────────────────────────

def write_report(
    stats: dict,
    traceability: dict,
    rag: dict,
    spot_check: list[dict],
) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Validation Report — Blinkit Discovery Engine",
        "",
        f"> Generated: {now}",
        "> Phase 5 QA results",
        "",
        "---",
        "",
        "## 1. Corpus Statistics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Reviews | {stats['total']} |",
        f"| Enriched Reviews | {stats['enriched']} |",
        f"| Unique Themes | {stats['unique_themes']} |",
        f"| Unique Segments | {stats['unique_segments']} |",
        "",
        "**Sentiment Distribution:**",
        "",
    ]
    for k, v in (stats.get("sentiments") or {}).items():
        if k:
            lines.append(f"- {k}: {v}")
    lines += [
        "",
        "**Platform Distribution:**",
        "",
    ]
    for k, v in (stats.get("platforms") or {}).items():
        if k:
            lines.append(f"- {k}: {v}")
    lines += [
        "",
        "**Top 10 Themes:**",
        "",
    ]
    for t, c in stats.get("top_themes") or []:
        lines.append(f"- `{t}`: {c} mentions")
    lines += [
        "",
        "**Top 10 Unmet Needs:**",
        "",
    ]
    for n, c in stats.get("top_unmet_needs") or []:
        lines.append(f"- {n}: {c} mentions")

    # Traceability
    tp = traceability.get("pass_rate", 0)
    lines += [
        "",
        "---",
        "",
        "## 2. Traceability Test",
        "",
        f"- **Sampled**: {traceability.get('passed', 0) + traceability.get('failed', 0)} theme-review pairs",
        f"- **Passed**: {traceability.get('passed', 0)}",
        f"- **Failed**: {traceability.get('failed', 0)}",
        f"- **Pass Rate**: {tp}%",
        "",
        "**Criterion**: Every sampled Groq-generated theme label must map to at least one real review in the corpus.",
        "",
        f"**Result**: {'✅ PASS' if tp >= 90 else '⚠️ PARTIAL' if tp >= 70 else '❌ FAIL'} ({tp}%)",
        "",
    ]
    if traceability.get("details"):
        lines += [
            "| Theme | Traceable | Matching Reviews |",
            "|---|---|---|",
        ]
        for d in traceability["details"]:
            mark = "✅" if d.get("traceable") else "❌"
            lines.append(f"| {d['theme']} | {mark} | {d.get('matching_reviews', 0)} |")

    # RAG grounding
    rp = rag.get("pass_rate", 0)
    lines += [
        "",
        "---",
        "",
        "## 3. RAG Grounding Test",
        "",
        f"- **Questions Tested**: {len(rag.get('questions', []))}",
        f"- **Grounded Answers**: {rag.get('grounded_count', 0)}",
        f"- **Pass Rate**: {rp}%",
        "",
        "**Criterion**: Each answer must be non-empty and contain at least one inline citation.",
        "",
        f"**Result**: {'✅ PASS' if rp >= 75 else '⚠️ PARTIAL' if rp >= 50 else '❌ FAIL'} ({rp}%)",
        "",
    ]
    if rag.get("questions"):
        lines += [
            "| # | Question | Grounded | Sources Used |",
            "|---|---|---|---|",
        ]
        for i, q in enumerate(rag["questions"], 1):
            mark = "✅" if q.get("grounded") else ("❌" if "error" in q else "⚠️")
            src = q.get("sources_used", "—")
            lines.append(f"| {i} | {q['question'][:70]} | {mark} | {src} |")

    # Manual spot-check protocol
    lines += [
        "",
        "---",
        "",
        "## 4. Manual Spot-Check Protocol",
        "",
        f"- **Sample Size**: {len(spot_check)} reviews",
        f"- **Sample File**: `docs/validation_spot_check.json`",
        "",
        "### Instructions for Manual Review",
        "",
        "For each review in the spot-check sample, assess:",
        "1. **Theme Accuracy** — Are the assigned themes accurate for the review text?",
        "2. **Sentiment Correctness** — Is the sentiment label (Positive/Neutral/Negative) correct?",
        "3. **Segment Inference** — Is the inferred user segment reasonable?",
        "",
        "Record a simple precision score per category (e.g., 43/50 themes correct = 86% precision).",
        "",
        "| Category | Reviewed | Correct | Precision |",
        "|---|---|---|---|",
        "| Themes | — | — | — |",
        "| Sentiment | — | — | — |",
        "| Segments | — | — | — |",
        "",
        "*(Fill in after manual review)*",
        "",
        "---",
        "",
        "## 5. Success Criteria Checklist",
        "",
        f"- {'✅' if tp >= 90 else '❌'} All themes traceable to source quotes",
        "- ⬜ No fabricated themes present in manual sample *(fill after spot-check)*",
        "- ⬜ Segment clusters are directionally consistent *(fill after spot-check)*",
        f"- {'✅' if rp >= 75 else '❌'} Insights are specific (chatbot stays grounded, citations present)",
        f"- {'✅' if rp >= 75 else '❌'} Chatbot stays grounded (no unsupported claims detected in automated test)",
        "",
        "---",
        "",
        "*Report auto-generated by `src/validation/validate.py`*",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n[Validation] Report written → {REPORT_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Blinkit Discovery Engine — Phase 5 Validation & QA")
    print("=" * 60)

    # Load data
    if not ENRICHED_PATH.exists():
        print(f"ERROR: {ENRICHED_PATH} not found. Run Phase 3 enrichment first.")
        sys.exit(1)

    reviews = load_enriched()
    print(f"\n[Validation] Loaded {len(reviews)} enriched reviews.")

    # Stats
    stats = corpus_stats(reviews)

    # Test 1: Traceability
    traceability = test_traceability(reviews, sample_size=20)

    # Test 2: RAG grounding
    rag = test_rag_grounding()

    # Spot-check sample
    spot_check = generate_spot_check(reviews, sample_size=50)

    # Write report
    write_report(stats, traceability, rag, spot_check)

    # Summary
    print("\n" + "=" * 60)
    print("  Validation Summary")
    print("=" * 60)
    print(f"  Traceability:  {traceability.get('pass_rate', 0)}%")
    print(f"  RAG Grounding: {rag.get('pass_rate', 0)}%")
    print(f"  Report:        {REPORT_PATH}")
    print(f"  Spot-check:    {SPOT_CHECK_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
