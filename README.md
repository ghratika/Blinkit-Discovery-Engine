---
title: Blinkit Discovery Engine
emoji: ⚡
colorFrom: yellow
colorTo: gray
sdk: streamlit
sdk_version: "1.48.0"
app_file: app/streamlit_app.py
pinned: false
license: mit
short_description: AI analysis of Blinkit user category exploration
---

# ⚡ Blinkit AI-Powered Discovery Engine

An AI-powered research dashboard that ingests unstructured user feedback about **Blinkit** and systematically surfaces the behavioral and structural reasons **category exploration doesn't happen today**.

> **Stack**: 100% free — Groq API · ChromaDB · LangChain · Streamlit · SQLite

---

## 🖥️ Dashboard Sections

| Section | Description |
|---|---|
| 📊 **Overview** | High-level KPIs + top-themes bar chart + monthly volume trend |
| 📅 **Timeline Reviews** | Date-filtered browser with keyword search and pagination |
| 🥧 **Distributions** | Sentiment / Source donut charts + monthly trend + sentiment-over-time |
| 🏷️ **Theme Taxonomy** | Expandable themes with % frequency, trend direction, and review snippets |
| 👥 **Segment Breakdown** | Stacked theme bars + sentiment chart per user persona |
| 💬 **AI Chatbot** | RAG-powered Q&A strictly grounded in real user reviews with citations |
| 🎯 **Unmet Needs** | Ranked list + horizontal bar chart of all category gaps |
| 📝 **Research Synthesis** | AI answers to 8 core behavioural research questions |

---

## 🔑 Environment Variable

Set your Groq API key in the Space **Secrets** (Settings → Variables and secrets):

```
GROQ_API_KEY = your_groq_api_key_here
```

Get a free key at: https://console.groq.com/

---

## 📐 Architecture

```
User Feedback (Reddit · Play Store · Quora)
       ↓  [Collectors + Normalizer]
data/processed/normalized.json
       ↓  [Groq Enrichment — themes · sentiment · segments · unmet_needs]
data/processed/enriched.json
       ↓  [ChromaDB + SQLite Ingestion]
ChromaDB vector index  +  SQLite metadata store
       ↓  [Streamlit Dashboard]
Interactive 8-section dashboard + RAG Chatbot
```

---

## 📚 Documentation

- [Problem Statement](docs/problemStatement.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Validation Report](docs/validation-report.md)

---

## 💤 Cold Starts (Spaces Sleeping)

This application is deployed on a **Free Tier Hugging Face Space**. Free spaces automatically go to sleep after ~48 hours of inactivity.
If you visit the app after a period of inactivity, you may experience a **2-3 minute loading screen** while the container wakes up and reinstalls dependencies. This is expected behavior. 
A GitHub Action cron job has been configured to ping the space daily to minimize the chances of this happening.

---

*Part 1 of the Blinkit Discovery Engine. 100% free-of-cost tools.*
