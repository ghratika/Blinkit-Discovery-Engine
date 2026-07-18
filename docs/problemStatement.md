# PROBLEM STATEMENT
## Part 1: AI-Powered Discovery Engine
**Product**: Blinkit | **Role**: Product Manager, Growth Team

---

## 1. CONTEXT

Blinkit has moved from a "reactive delivery app" to a habitual, weekly-planning
surface for millions of users. Retention is no longer the primary risk —
category concentration is. Users open the app, land on their reorder shelf,
repurchase the same 15-20 SKUs, and leave. The catalog breadth (pet supplies,
baby care, personal care, electronics accessories, stationery, etc.) exists,
but discovery of it inside an existing user's habit loop is weak.

This is a growth problem, not an acquisition problem: the users already trust
Blinkit with their wallet. The gap is behavioral, not access-based.

---

## 2. BUSINESS GOAL (NORTH STAR FOR THIS INITIATIVE)

Increase the % of Monthly Active Customers (MAC) who purchase from at least
one new category every month.

"New category" = a category the user has not purchased from in the trailing
90 days (rolling), to distinguish genuine exploration from routine variety
within an already-adopted category.

---

## 3. WHY THIS MATTERS

- **Basket value**: Cross-category buyers historically show higher AOV and
  higher LTV than single-category repeat buyers.
- **Defensibility**: A user who only buys milk and eggs from Blinkit can be
  poached by any 10-minute competitor. A user who buys groceries + pet food
  + baby care has higher switching cost.
- **Inventory economics**: Broader demand distribution improves dark-store SKU
  utilization and justifies inventory investment beyond top-moving grocery
  lines.

---

## 4. THE PROBLEM, STATED PRECISELY

Shopping behavior on Blinkit is highly habitual and narrow. Users default to
a repeat-purchase pattern (reorder / search-by-memory) rather than a
browse/explore pattern. Even when adjacent categories are relevant to their
life stage (e.g., a grocery buyer who owns a pet, or has a newborn), they
don't discover or trust Blinkit as the place to buy those items.

Before designing any intervention (nudges, merchandising, bundling,
personalization, etc.), we need to understand why — grounded in real user
language, not assumptions. That's the job of Part 1.

---

## 5. OBJECTIVE OF PART 1

Build an AI-powered discovery engine that ingests unstructured, publicly
available user feedback (app store reviews, Reddit, forums, social
conversations) about Blinkit and comparable quick-commerce apps, and
systematically surfaces the behavioral and structural reasons category
exploration doesn't happen today.

This engine's output becomes the evidence base for the Part 2 solution — it
is explicitly a research/insight system, not the growth feature itself.

---

## 6. RESEARCH QUESTIONS THE ENGINE MUST ANSWER

1. Why do users repeatedly buy from the same categories?
2. What prevents users from exploring new categories on the app?
3. How do users currently discover new products — search, homepage, word of
   mouth, ads?
4. What role do habit and routine play in shopping behavior (e.g., fixed
   weekly lists)?
5. What information/trust signals do users need before trying an unfamiliar
   category (reviews, brand trust, quality concerns, return policy)?
6. What frustrations recur across reviews/discussions (stockouts, quality,
   wrong substitutions, pricing vs. quick-commerce vs. D2C/Amazon)?
7. Which user segments show higher exploration tendency (new parents, pet
   owners, festive/seasonal buyers, urban single-person households)?
8. What unmet needs or category gaps come up consistently in conversations?

---

## 7. SCOPE

**In scope for Part 1:**
- Data collection design (sources, sampling, filtering for Blinkit + close
  competitors for comparative signal)
- NLP/LLM pipeline for theme extraction, sentiment, and segment tagging
- Insight synthesis with supporting evidence (quotes/patterns, frequency,
  source)
- A validation methodology proving the insights are reliable, not
  hallucinated or cherry-picked
- A demo frontend to interact with and showcase the engine's output

**Out of scope for Part 1 (reserved for Part 2):**
- The actual growth intervention/feature design
- Metrics framework, experiment design, RICE/prioritization
- UI/UX or PRD for the solution

---

## 8. CANDIDATE DATA SOURCES

- **Play Store & App Store reviews** (Blinkit, Instamart, Zepto)
  -> Direct product complaints/praise, feature requests
- **Reddit** (r/india, r/bangalore, quick-commerce specific threads)
  -> Unfiltered, comparative, habit-related discussion
- **Twitter/X**
  -> Real-time frustration spikes, viral complaints
- **Consumer forums / MouthShut / Quora**
  -> Longer-form reasoning, decision-making narratives
- **Blinkit's own app review replies**
  -> What the company already acknowledges as issues

---

## 9. PROPOSED AI-NATIVE STACK

*Note: The entire architecture will be built using free-of-cost tools and services.*

- **Collection**: n8n workflows / scraper agents -> normalize into a single
  JSON schema (source, text, rating, timestamp, product)
- **Enrichment**: Groq API for theme extraction, sentiment tagging,
  segment inference, and unmet-need clustering
- **Storage/Retrieval**: Vector DB (for RAG) so themes can be queried and
  re-validated against raw source text
- **Synthesis**: Groq-driven summarization with citation back to source
  snippets (no ungrounded claims)
- **Validation layer**: Human-in-the-loop spot-checks + inter-theme consistency
  checks (see below)
- **Frontend/Demo**: Python (Streamlit) app deployed on Hugging Face Spaces —
  chosen for fast build, free hosting, and an easy shareable link for a
  reviewer/interviewer

---

## 10. FRONTEND / DEMO INTERFACE (Python, Streamlit, Hugging Face Spaces)

**Purpose:** Give reviewers a way to interact with the discovery engine's
output directly, rather than only reading a static report.

**Planned sections:**

a) **Timeline-filtered top reviews**
   - Toggle/slider to view top reviews within a selected window:
     1, 2, 3, 4, 5, or 6 months or any date period
   - Reviews ranked by relevance/frequency of theme mentions within the
     selected window
   - Lets a reviewer see whether themes are recent or long-standing

b) **Distribution of reviews**
   - Source distribution: % split across Play Store, App Store, Reddit,
     Twitter/X, forums
   - Sentiment distribution: positive / neutral / negative split,
     viewable per timeline window
   - Category-mention distribution: which categories are mentioned most vs least

c) **Theme taxonomy panel**
   - List of extracted themes with frequency %, trend direction vs prior
     period, and top contributing source
   - Click-through to the underlying anonymized review snippets
     (traceability / validation proof)

d) **Segment breakdown**
   - Tags such as different categories with theme differences unique to each segment (maps to
     research question 7)

e) **Chatbot preview**
   - Pre-written suggested questions shown as clickable chips, e.g.:
       - "Why do users keep buying the same categories?"
       - "What stops users from trying new categories?"
       - "Which segment is most likely to explore new categories?"
       - "What do users say about trust before buying something new?"
   - Clicking a chip auto-sends that question to the chatbot and returns
     an answer generated from the analyzed review corpus (RAG-style,
     grounded in actual collected data, not the model's general
     knowledge)
   - A free-text input also available so a reviewer can ask any other
     question directly

f) **Top unmet needs / feature requests**
   - Running list of things users explicitly ask for that don't currently
     exist on the platform (maps to research question 8)

---

## 11. DELIVERABLES FOR PART 1

1. Documented workflow (collection -> cleaning -> analysis -> synthesis)
2. Theme taxonomy with frequency and source distribution
3. Insight report answering the 8 research questions, each backed by
   evidence
4. Validation methodology and results (precision/recall style spot-check,
   or equivalent)
5. Working demo frontend (Python/Streamlit, deployed on Hugging Face
   Spaces) covering sections 10(a) to 10(f) above

---

## 12. SUCCESS CRITERIA FOR THE DISCOVERY ENGINE ITSELF

The engine is considered "working," not just "run," if:
- Themes are traceable to source quotes (auditable, not black-box)
- Independent manual review of a sample of raw reviews surfaces the same
  top themes the engine reports (no major theme missed, no fabricated
  theme present)
- Segment-level differences are directionally consistent with independent
  proxies (e.g., review mentions of "puppy," "baby," "diet" cluster
  correctly under pet/baby/health-conscious segments)
- Insights are specific enough to be actionable for Part 2 (not generic
  statements like "users want better app experience")
- The chatbot's answers stay grounded in the collected review corpus
  (RAG-based retrieval) rather than generating unsupported claims

---

*This document defines the problem, scope, and demo interface for Part 1
only. The discovery engine build, sample outputs, and validation results
follow as separate artifacts.*
