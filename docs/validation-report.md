# Validation Report — Blinkit Discovery Engine

> Generated: 2026-07-19 (auto-generated template — run `python src/validation/validate.py` for live results)
> Phase 5 QA

---

## 1. Corpus Statistics

| Metric | Value |
|---|---|
| Total Reviews | ~50 (enriched.json) |
| Enriched Reviews | ~50 |
| Unique Themes | ~12 |
| Unique Segments | ~10 |

**Sentiment Distribution:**

- Positive: ~15%
- Neutral: ~35%
- Negative: ~50%

**Platform Distribution:**

- Blinkit: ~60%
- Instamart: ~20%
- Zepto: ~20%

**Top 10 Themes (from corpus):**

- `Category Trust`: ~24 mentions
- `Stockout Frustration`: ~23 mentions
- `Convenience`: ~5 mentions
- `Habit Loop`: ~3 mentions
- `Financial Burden`: ~3 mentions
- `Speed`: ~2 mentions
- `Reliability`: ~2 mentions
- `Payment Frustration`: ~2 mentions
- `Hidden Charges`: ~2 mentions
- `Return Policy`: ~1 mention

**Top 10 Unmet Needs (from corpus):**

- Ability to inspect fresh produce before purchase
- Better return process
- Faster customer support
- More organic and diet product options
- Lower fees or more transparent pricing
- Relevant product recommendations
- More curated discovery experience
- Consistent stock availability
- Easy Returns
- Reliable order fulfillment

---

## 2. Traceability Test

> **Run `python src/validation/validate.py` to populate with live results.**

- **Sampled**: 20 theme-review pairs
- **Passed**: —
- **Failed**: —
- **Pass Rate**: —%

**Criterion**: Every sampled Groq-generated theme label must map to at least one real review in the corpus.

**Result**: *(Run validation script)*

---

## 3. RAG Grounding Test

> **Run `python src/validation/validate.py` to populate with live results.**

- **Questions Tested**: 8
- **Grounded Answers**: —
- **Pass Rate**: —%

**Criterion**: Each answer must be non-empty and contain at least one inline citation.

**Result**: *(Run validation script)*

| # | Question | Grounded | Sources Used |
|---|---|---|---|
| 1 | Why do users repeatedly buy the same categories? | — | — |
| 2 | What prevents users from exploring new categories? | — | — |
| 3 | How do users currently discover new products? | — | — |
| 4 | What role do habit and routine play? | — | — |
| 5 | What trust signals do users need before new categories? | — | — |
| 6 | What are the top recurring frustrations? | — | — |
| 7 | Which segments show higher exploration tendency? | — | — |
| 8 | What unmet needs come up consistently? | — | — |

---

## 4. Manual Spot-Check Protocol

- **Sample Size**: 50 reviews
- **Sample File**: `docs/validation_spot_check.json`

### Instructions for Manual Review

For each review in the spot-check sample, assess:
1. **Theme Accuracy** — Are the assigned themes accurate for the review text?
2. **Sentiment Correctness** — Is the sentiment label (Positive/Neutral/Negative) correct?
3. **Segment Inference** — Is the inferred user segment reasonable?

| Category | Reviewed | Correct | Precision |
|---|---|---|---|
| Themes | — | — | — |
| Sentiment | — | — | — |
| Segments | — | — | — |

*(Fill in after manual review)*

---

## 5. Success Criteria Checklist

- ⬜ All themes traceable to source quotes *(run validation script)*
- ⬜ No fabricated themes present in manual sample *(fill after spot-check)*
- ⬜ Segment clusters are directionally consistent *(fill after spot-check)*
- ⬜ Insights are specific (chatbot stays grounded, citations present) *(run validation script)*
- ⬜ Chatbot stays grounded (no unsupported claims detected) *(run validation script)*

---

## 6. How to Run Full Validation

```bash
# Activate virtual environment
venv\Scripts\activate

# Run automated validation (requires GROQ_API_KEY in .env)
python src/validation/validate.py
```

This will:
1. Run the traceability test (20 random theme samples)
2. Run the RAG grounding test (8 research questions)
3. Generate a 50-review spot-check sample at `docs/validation_spot_check.json`
4. Overwrite this file with live results

---

*Template — auto-populated by `src/validation/validate.py`*
