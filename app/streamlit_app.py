"""
app/streamlit_app.py

Blinkit AI-Powered Discovery Engine — Streamlit Dashboard (Phase 5)

Six sections:
  a) Timeline-filtered reviews
  b) Distribution charts (source, sentiment)
  c) Theme taxonomy panel
  d) Segment breakdown
  e) Chatbot (RAG) preview
  f) Unmet needs ranked list
"""

import sys
import os
from pathlib import Path

# ── Path setup so src/ is importable ─────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))

import json
import datetime
from collections import Counter

import streamlit as st
import pandas as pd

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Blinkit Discovery Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Blinkit Brand Colors
#   Primary Yellow  : #FFE000   (Blinkit signature yellow)
#   Dark Yellow     : #F5C800   (deeper accent)
#   Brand Black     : #0D0D0D   (near-black background)
#   Card Dark       : #1A1A1A
#   Card Mid        : #222222
#   Green Accent    : #00C853   (fresh / success states)
#   Text Primary    : #F5F5F5
#   Text Secondary  : #A0A0A0
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --yellow:      #FFE000;
    --yellow-dark: #F5C800;
    --yellow-dim:  rgba(255,224,0,0.12);
    --yellow-glow: rgba(255,224,0,0.25);
    --black:       #0D0D0D;
    --card:        #1A1A1A;
    --card2:       #222222;
    --green:       #00C853;
    --green-dim:   rgba(0,200,83,0.12);
    --red:         #FF3D57;
    --red-dim:     rgba(255,61,87,0.12);
    --text:        #F5F5F5;
    --muted:       #A0A0A0;
    --border:      rgba(255,224,0,0.1);
    --border-soft: rgba(255,255,255,0.06);
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--black) !important;
    color: var(--text) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111111 0%, #161610 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    color: var(--yellow) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #111111 0%, #1a1900 60%, #1f1d00 100%);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.8rem 2.2rem;
    margin-bottom: 1.4rem;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: '⚡';
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.06;
}
.hero-title {
    font-size: 2rem;
    font-weight: 900;
    color: var(--yellow);
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin: 0;
}
.hero-sub {
    color: var(--muted);
    font-size: 0.88rem;
    margin-top: 0.4rem;
}

/* ── Metric cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.9rem;
    margin-bottom: 1.4rem;
}
.kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.25rem;
    text-align: center;
    transition: border-color 0.2s, transform 0.2s;
}
.kpi:hover {
    border-color: var(--yellow);
    transform: translateY(-2px);
}
.kpi-val {
    font-size: 1.9rem;
    font-weight: 800;
    color: var(--yellow);
    line-height: 1;
}
.kpi-lbl {
    font-size: 0.7rem;
    color: var(--muted);
    margin-top: 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}

/* ── Section headers ── */
.sec-head {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    margin: 1.4rem 0 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid var(--border);
}
.sec-head-icon { font-size: 1.25rem; }
.sec-head-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
}

/* ── Review card ── */
.rev-card {
    background: var(--card);
    border: 1px solid var(--border-soft);
    border-left: 3px solid var(--yellow);
    border-radius: 9px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.65rem;
    transition: border-left-color 0.2s;
}
.rev-card:hover { border-left-color: var(--green); }
.rev-text {
    font-size: 0.875rem;
    color: var(--text);
    line-height: 1.65;
}
.rev-meta {
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 0.45rem;
    display: flex;
    gap: 0.9rem;
    flex-wrap: wrap;
}
.tag {
    display: inline-block;
    padding: 0.18rem 0.55rem;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 600;
    margin: 0.1rem;
}
.tag-pos  { background: var(--green-dim); color: var(--green); border: 1px solid rgba(0,200,83,0.3); }
.tag-neg  { background: var(--red-dim);   color: var(--red);   border: 1px solid rgba(255,61,87,0.3); }
.tag-neu  { background: var(--yellow-dim); color: var(--yellow); border: 1px solid rgba(255,224,0,0.3); }
.tag-theme { background: rgba(255,224,0,0.08); color: #FFD000; border: 1px solid rgba(255,224,0,0.2); }
.tag-seg  { background: rgba(255,255,255,0.05); color: var(--muted); border: 1px solid var(--border-soft); }

/* ── Chatbot bubbles ── */
.chat-user {
    background: linear-gradient(135deg, rgba(255,224,0,0.15), rgba(255,224,0,0.05));
    border: 1px solid rgba(255,224,0,0.25);
    border-radius: 14px 14px 4px 14px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0 0.5rem 3.5rem;
    font-size: 0.88rem;
    color: var(--text);
}
.chat-bot {
    background: var(--card2);
    border: 1px solid var(--border-soft);
    border-radius: 14px 14px 14px 4px;
    padding: 0.85rem 1rem;
    margin: 0.5rem 3.5rem 0.5rem 0;
    font-size: 0.88rem;
    color: var(--text);
    line-height: 1.7;
}
.src-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.65rem; }
.src-chip {
    background: var(--yellow-dim);
    border: 1px solid rgba(255,224,0,0.2);
    color: var(--yellow);
    border-radius: 10px;
    padding: 0.18rem 0.55rem;
    font-size: 0.68rem;
    font-weight: 600;
}

/* ── Unmet needs ── */
.need-row {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    background: var(--card);
    border: 1px solid var(--border-soft);
    border-radius: 9px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.45rem;
    transition: border-color 0.2s;
}
.need-row:hover { border-color: var(--yellow); }
.need-rank { font-size: 1rem; font-weight: 800; color: var(--yellow); min-width: 2rem; text-align: center; }
.need-text { flex: 1; font-size: 0.85rem; color: var(--text); }
.need-cnt {
    font-size: 0.75rem; font-weight: 700; color: #0D0D0D;
    background: var(--yellow); border-radius: 6px; padding: 0.2rem 0.55rem;
}

/* ── Synthesis ── */
.synth-card {
    background: linear-gradient(135deg, rgba(255,224,0,0.06) 0%, rgba(255,224,0,0.02) 100%);
    border: 1px solid rgba(255,224,0,0.15);
    border-radius: 10px;
    padding: 1.1rem 1.35rem;
    margin-bottom: 0.9rem;
}
.synth-q { font-size: 0.78rem; font-weight: 700; color: var(--yellow); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }
.synth-a { font-size: 0.86rem; color: var(--text); line-height: 1.72; }

/* ── Streamlit widget overrides ── */
.stSlider > div { color: var(--muted) !important; }
.stButton > button {
    background: var(--yellow) !important;
    border: none !important;
    color: #0D0D0D !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stExpander"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 9px !important;
}
div[data-testid="stExpander"] summary { color: var(--text) !important; }
.stChatInputContainer { border-color: var(--yellow) !important; }
.stSelectbox > div > div { background: var(--card) !important; color: var(--text) !important; }
.stMultiSelect > div > div { background: var(--card) !important; }
div[data-testid="stMetricValue"] { color: var(--yellow) !important; }
div[data-baseweb="tag"] { background: var(--yellow-dim) !important; color: var(--yellow) !important; }
.stRadio > label { color: var(--muted) !important; }

/* ── Progress bar (used in theme list) ── */
.bar-wrap { background: rgba(255,255,255,0.06); border-radius: 4px; height: 6px; margin-top:4px; }
.bar-fill  { background: var(--yellow); border-radius: 4px; height: 6px; transition: width 0.3s; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def load_enriched() -> list[dict]:
    path = ROOT / "data" / "processed" / "enriched.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            # Normalize different Play Store variants into one
            for r in data:
                src = r.get("source", "")
                if src and "play store" in src.lower():
                    r["source"] = "Play Store"
            return data
    return []


@st.cache_data(ttl=300)
def load_synthesis() -> dict:
    path = ROOT / "data" / "processed" / "synthesis_outputs.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def parse_ts(ts: str):
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
    except Exception:
        return None


def filter_reviews(reviews, start_date, end_date, sentiments, sources) -> list[dict]:
    out = []
    for r in reviews:
        d = parse_ts(r.get("timestamp", ""))
        if d and (d < start_date or d > end_date):
            continue
        enr = r.get("enrichment") or {}
        if sentiments and enr.get("sentiment") not in sentiments:
            continue
        if sources and r.get("source") not in sources:
            continue
        out.append(r)
    return out


def sentiment_tag(s):
    cls = {"Positive": "tag-pos", "Negative": "tag-neg", "Neutral": "tag-neu"}.get(s, "tag-neu")
    return f'<span class="tag {cls}">{s or "—"}</span>'


def render_review_card(r: dict):
    enr = r.get("enrichment") or {}
    text = r.get("text", "")
    source = r.get("source", "Unknown")
    ts = (r.get("timestamp") or "")[:10]
    rating = r.get("rating")
    rating_str = f"⭐ {rating}" if rating else ""
    sentiment = enr.get("sentiment", "")
    themes = enr.get("themes") or []
    segments = enr.get("segment") or []

    themes_html = " ".join(f'<span class="tag tag-theme">{t}</span>' for t in themes)
    segs_html = " ".join(f'<span class="tag tag-seg">{s}</span>' for s in segments)
    sent_html = sentiment_tag(sentiment)

    st.markdown(
        f"""
<div class="rev-card">
  <div class="rev-text">"{text}"</div>
  <div class="rev-meta">
    <span>📡 {source}</span>
    <span>📅 {ts}</span>
    {f'<span>{rating_str}</span>' if rating_str else ''}
  </div>
  <div style="margin-top:0.55rem">{sent_html} {themes_html} {segs_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


# ── Load data ──────────────────────────────────────────────────────────────────
all_reviews = load_enriched()
synthesis = load_synthesis()

# Filter meta
all_sources = sorted({r.get("source", "Unknown") for r in all_reviews if r.get("source")})
all_sentiments = ["Positive", "Neutral", "Negative"]

dates = [parse_ts(r.get("timestamp", "")) for r in all_reviews]
dates = [d for d in dates if d]
min_date = min(dates) if dates else datetime.date(2024, 1, 1)
max_date = max(dates) if dates else datetime.date.today()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo block
    st.markdown(
        """
<div style="padding:1.2rem 0 1.5rem;text-align:center;">
  <div style="font-size:2.4rem;line-height:1">⚡</div>
  <div style="font-size:1.05rem;font-weight:800;color:#FFE000;margin-top:0.3rem;letter-spacing:-0.01em">Blinkit</div>
  <div style="font-size:0.72rem;color:#A0A0A0;margin-top:0.1rem">Discovery Engine · AI Research</div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("## 🔍 Filters")

    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range",
    )
    start_date = date_range[0] if isinstance(date_range, tuple) and len(date_range) > 0 else min_date
    end_date = date_range[1] if isinstance(date_range, tuple) and len(date_range) > 1 else max_date

    sel_sentiments = st.multiselect("Sentiment", all_sentiments, default=all_sentiments, key="sentiments")
    sel_sources = st.multiselect("Source", all_sources, default=[], key="sources", placeholder="All sources")

    st.markdown("---")
    st.markdown("## 🧭 Navigate")
    nav = st.radio(
        "Jump to section",
        [
            "📊 Overview",
            "📅 Timeline Reviews",
            "🥧 Distributions",
            "🏷️ Theme Taxonomy",
            "👥 Segment Breakdown",
            "💬 AI Chatbot",
            "🎯 Unmet Needs",
            "📝 Research Synthesis",
        ],
        key="nav",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.68rem;color:#555;text-align:center;line-height:1.6">Blinkit Discovery Engine v1.0<br>Phase 5 · 100% Free Stack<br>Groq · ChromaDB · LangChain</div>',
        unsafe_allow_html=True,
    )

# Apply global filters (platform is always Blinkit — single app focus)
filtered = filter_reviews(
    all_reviews,
    start_date,
    end_date,
    sel_sentiments if sel_sentiments else None,
    sel_sources if sel_sources else None,
)

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
  <div class="hero-title">⚡ Blinkit Discovery Engine</div>
  <div class="hero-sub">AI-powered analysis of user feedback · Surfacing why category exploration doesn't happen</div>
</div>
""",
    unsafe_allow_html=True,
)

def _group_theme(t: str) -> str:
    tl = t.lower()
    if "stock" in tl or "availab" in tl or "missing" in tl:
        return "Stockout Frustration"
    if "habit" in tl or "routine" in tl or "regular" in tl:
        return "Habit Loop"
    if "trust" in tl or "quality" in tl or "fresh" in tl or "expir" in tl:
        return "Category Trust & Quality"
    if "price" in tl or "cost" in tl or "fee" in tl or "expensive" in tl or "charge" in tl:
        return "Pricing & Fees"
    if "speed" in tl or "fast" in tl or "quick" in tl or "time" in tl or "late" in tl or "delay" in tl:
        return "Delivery Speed"
    if "support" in tl or "service" in tl or "refund" in tl or "return" in tl:
        return "Customer Support"
    if "ui" in tl or "app" in tl or "search" in tl or "discover" in tl or "find" in tl:
        return "App Experience"
    return t.title()

# Clean themes on the fly
for r in filtered:
    enr = r.get("enrichment")
    if enr and "themes" in enr:
        enr["themes"] = list({_group_theme(t) for t in enr["themes"] if t})

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_f = len(filtered)
enr_sents = [(r.get("enrichment") or {}).get("sentiment") for r in filtered]
pos_pct = round(100 * enr_sents.count("Positive") / max(len(enr_sents), 1))
neg_pct = round(100 * enr_sents.count("Negative") / max(len(enr_sents), 1))
all_themes_flat = [t for r in filtered for t in (r.get("enrichment") or {}).get("themes", [])]
unique_themes = len(set(all_themes_flat))

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi"><div class="kpi-val">{total_f}</div><div class="kpi-lbl">Reviews</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi"><div class="kpi-val">{pos_pct}%</div><div class="kpi-lbl">Positive</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi"><div class="kpi-val">{neg_pct}%</div><div class="kpi-lbl">Negative</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi"><div class="kpi-val">{unique_themes}</div><div class="kpi-lbl">Unique Themes</div></div>', unsafe_allow_html=True)

st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if nav == "📊 Overview":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">📊</span><span class="sec-head-title">Overview Dashboard</span></div>', unsafe_allow_html=True)

    if not filtered:
        st.warning("Not enough data for this segment. Please broaden your filters.")
    else:
        try:
            import altair as alt

            # Top themes chart
            theme_freq = Counter(all_themes_flat).most_common(12)
            if theme_freq:
                df_t = pd.DataFrame(theme_freq, columns=["Theme", "Count"])
                chart = (
                    alt.Chart(df_t)
                    .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#FFE000")
                    .encode(
                        x=alt.X("Count:Q", title="Mentions", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0", gridColor="rgba(255,255,255,0.05)")),
                        y=alt.Y("Theme:N", sort="-x", title=None, axis=alt.Axis(labelColor="#F5F5F5")),
                        tooltip=[alt.Tooltip("Theme"), alt.Tooltip("Count")],
                    )
                    .properties(height=340, title=alt.TitleParams("Top Themes in Blinkit User Reviews", color="#F5F5F5", fontSize=14, fontWeight=600))
                    .configure_view(strokeOpacity=0, fill="#1A1A1A")
                    .configure_axis(gridColor="rgba(255,255,255,0.04)")
                )
                st.altair_chart(chart, use_container_width=True)

            # Monthly trend
            st.markdown("#### 📈 Monthly Review Volume (2024 – 2026)")
            monthly: dict[str, int] = {}
            for r in filtered:
                ts = r.get("timestamp", "")
                if ts and len(ts) >= 7:
                    monthly[ts[:7]] = monthly.get(ts[:7], 0) + 1
            if monthly:
                df_m = pd.DataFrame(sorted(monthly.items()), columns=["Month", "Count"])
                chart_m = (
                    alt.Chart(df_m)
                    .mark_area(
                        line={"color": "#FFE000", "strokeWidth": 2},
                        color=alt.Gradient(
                            gradient="linear",
                            stops=[alt.GradientStop(color="rgba(255,224,0,0.4)", offset=0),
                                   alt.GradientStop(color="rgba(255,224,0,0.02)", offset=1)],
                            x1=1, x2=1, y1=0, y2=1,
                        ),
                    )
                    .encode(
                        x=alt.X("Month:T", title="Month", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0", format="%b %Y")),
                        y=alt.Y("Count:Q", title="Reviews", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0")),
                        tooltip=[alt.Tooltip("Month:T", format="%b %Y"), alt.Tooltip("Count:Q")],
                    )
                    .properties(height=180)
                    .configure_view(strokeOpacity=0, fill="#1A1A1A")
                    .configure_axis(gridColor="rgba(255,255,255,0.04)")
                )
                st.altair_chart(chart_m, use_container_width=True)

        except ImportError:
            st.info("Install `altair` for charts: `pip install altair`")

    # Source summary
    st.markdown("#### 📡 Reviews by Source")
    src_cnts = Counter(r.get("source") for r in filtered)
    cols = st.columns(len(src_cnts) or 1)
    pal = ["#FFE000", "#F5C800", "#00C853", "#FF3D57"]
    for i, (src, cnt) in enumerate(sorted(src_cnts.items(), key=lambda x: -x[1])):
        with cols[i % len(cols)]:
            st.markdown(f'<div class="kpi"><div class="kpi-val" style="color:{pal[i%len(pal)]};font-size:1.5rem">{cnt}</div><div class="kpi-lbl">{src}</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# a) TIMELINE REVIEWS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "📅 Timeline Reviews":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">📅</span><span class="sec-head-title">Timeline-Filtered Reviews</span></div>', unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 1])
    with col_l:
        st.markdown(f"Showing **{len(filtered)}** reviews between **{start_date}** and **{end_date}**.")
    with col_r:
        sort_by = st.selectbox("Sort", ["Most Recent", "Oldest First"], key="sort_rev")
        
    if not filtered:
        st.warning("Not enough data for this segment. Please broaden your filters.")

    kw = st.text_input("🔍 Search keyword or theme", placeholder="e.g. stockout, trust, habit…", key="kw")

    display = sorted(filtered, key=lambda r: r.get("timestamp") or "", reverse=(sort_by == "Most Recent"))
    display.sort(key=lambda r: {"Negative": 0, "Neutral": 1, "Positive": 2}.get((r.get("enrichment") or {}).get("sentiment"), 3))
    if kw:
        q = kw.lower()
        display = [
            r for r in display
            if q in r.get("text", "").lower()
            or any(q in t.lower() for t in (r.get("enrichment") or {}).get("themes", []))
            or q in (r.get("source") or "").lower()
        ]

    pg_size = 10
    total_pg = max(1, (len(display) - 1) // pg_size + 1)
    pg = st.number_input("Page", min_value=1, max_value=total_pg, value=1, key="page") - 1
    page_revs = display[pg * pg_size : (pg + 1) * pg_size]

    if page_revs:
        for r in page_revs:
            render_review_card(r)
        st.markdown(f'<div style="color:#555;font-size:0.73rem;text-align:right">Page {pg+1}/{total_pg} · {len(display)} results</div>', unsafe_allow_html=True)
    else:
        st.info("No reviews match the current filters.")


# ═══════════════════════════════════════════════════════════════════════════════
# b) DISTRIBUTIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "🥧 Distributions":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">🥧</span><span class="sec-head-title">Distribution of Reviews</span></div>', unsafe_allow_html=True)

    try:
        import altair as alt

        c1, c2 = st.columns(2)

        # Sentiment donut
        sent_cnt = Counter([(r.get("enrichment") or {}).get("sentiment", "Unknown") for r in filtered])
        df_s = pd.DataFrame(list(sent_cnt.items()), columns=["Sentiment", "Count"])
        with c1:
            st.markdown("#### 😊 Sentiment")
            chart_s = (
                alt.Chart(df_s)
                .mark_arc(innerRadius=52, outerRadius=88, padAngle=0.03, cornerRadius=4)
                .encode(
                    theta=alt.Theta("Count:Q"),
                    color=alt.Color("Sentiment:N", scale=alt.Scale(
                        domain=["Positive", "Neutral", "Negative"],
                        range=["#00C853", "#FFE000", "#FF3D57"]
                    ), legend=alt.Legend(labelColor="#A0A0A0")),
                    tooltip=["Sentiment", "Count"],
                )
                .properties(height=220)
                .configure_view(strokeOpacity=0, fill="#1A1A1A")
            )
            st.altair_chart(chart_s, use_container_width=True)

        # Source donut
        src_cnt = Counter([r.get("source", "Unknown") for r in filtered])
        df_src = pd.DataFrame(list(src_cnt.items()), columns=["Source", "Count"])
        with c2:
            st.markdown("#### 📡 Source")
            chart_src = (
                alt.Chart(df_src)
                .mark_arc(innerRadius=52, outerRadius=88, padAngle=0.03, cornerRadius=4)
                .encode(
                    theta=alt.Theta("Count:Q"),
                    color=alt.Color("Source:N", scale=alt.Scale(
                        range=["#FFE000", "#F5C800", "#00C853", "#FF3D57", "#A0A0A0"]
                    ), legend=alt.Legend(labelColor="#A0A0A0")),
                    tooltip=["Source", "Count"],
                )
                .properties(height=220)
                .configure_view(strokeOpacity=0, fill="#1A1A1A")
            )
            st.altair_chart(chart_src, use_container_width=True)

        # Monthly trend line
        st.markdown("#### 📈 Monthly Volume Trend")
        monthly: dict[str, int] = {}
        for r in filtered:
            ts = r.get("timestamp", "")
            if ts and len(ts) >= 7:
                monthly[ts[:7]] = monthly.get(ts[:7], 0) + 1
        if monthly:
            df_m = pd.DataFrame(sorted(monthly.items()), columns=["Month", "Count"])
            chart_m = (
                alt.Chart(df_m)
                .mark_line(color="#FFE000", strokeWidth=2.5, point=alt.OverlayMarkDef(color="#FFE000", size=60))
                .encode(
                    x=alt.X("Month:T", title=None, axis=alt.Axis(labelColor="#A0A0A0", format="%b %Y")),
                    y=alt.Y("Count:Q", title="Reviews", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0")),
                    tooltip=[alt.Tooltip("Month:T", format="%b %Y"), alt.Tooltip("Count:Q")],
                )
                .properties(height=200)
                .configure_view(strokeOpacity=0, fill="#1A1A1A")
                .configure_axis(gridColor="rgba(255,255,255,0.04)")
            )
            st.altair_chart(chart_m, use_container_width=True)

        # Sentiment over time
        st.markdown("#### 📊 Sentiment Trend (Monthly)")
        sent_monthly = []
        for r in filtered:
            ts = r.get("timestamp", "")
            sent = (r.get("enrichment") or {}).get("sentiment", "Unknown")
            if ts and len(ts) >= 7:
                sent_monthly.append({"Month": ts[:7], "Sentiment": sent})
        if sent_monthly:
            df_sm = pd.DataFrame(sent_monthly)
            df_sm_grp = df_sm.groupby(["Month", "Sentiment"]).size().reset_index(name="Count")
            chart_sm = (
                alt.Chart(df_sm_grp)
                .mark_bar()
                .encode(
                    x=alt.X("Month:T", title=None, axis=alt.Axis(labelColor="#A0A0A0", format="%b %Y")),
                    y=alt.Y("Count:Q", stack="normalize", title="Proportion", axis=alt.Axis(format="%", labelColor="#A0A0A0", titleColor="#A0A0A0")),
                    color=alt.Color("Sentiment:N", scale=alt.Scale(
                        domain=["Positive", "Neutral", "Negative"],
                        range=["#00C853", "#FFE000", "#FF3D57"]
                    ), legend=alt.Legend(labelColor="#A0A0A0")),
                    tooltip=["Month:T", "Sentiment", "Count"],
                )
                .properties(height=220)
                .configure_view(strokeOpacity=0, fill="#1A1A1A")
                .configure_axis(gridColor="rgba(255,255,255,0.04)")
            )
            st.altair_chart(chart_sm, use_container_width=True)

    except ImportError:
        st.info("Install altair: `pip install altair`")


# ═══════════════════════════════════════════════════════════════════════════════
# c) THEME TAXONOMY
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "🏷️ Theme Taxonomy":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">🏷️</span><span class="sec-head-title">Theme Taxonomy Panel</span></div>', unsafe_allow_html=True)
    st.markdown("Click any theme to expand and see supporting review snippets.")

    theme_freq = Counter(all_themes_flat)
    total_mentions = max(sum(theme_freq.values()), 1)

    # Trend: compare first vs second half of filtered timeline
    half = len(filtered) // 2
    freq_first = Counter(t for r in filtered[:half] for t in (r.get("enrichment") or {}).get("themes", []))
    freq_second = Counter(t for r in filtered[half:] for t in (r.get("enrichment") or {}).get("themes", []))

    sort_opt = st.selectbox("Sort by", ["Frequency ↓", "Frequency ↑", "Alphabetical"], key="th_sort")
    items = list(theme_freq.items())
    if sort_opt == "Frequency ↓":
        items.sort(key=lambda x: x[1], reverse=True)
    elif sort_opt == "Frequency ↑":
        items.sort(key=lambda x: x[1])
    else:
        items.sort(key=lambda x: x[0])

    for theme, count in items:
        pct = round(100 * count / total_mentions, 1)
        c1 = freq_first.get(theme, 0)
        c2 = freq_second.get(theme, 0)
        trend = "🔺 Rising" if c2 > c1 else ("🔻 Falling" if c2 < c1 else "➡️ Stable")
        bar_w = round(100 * count / max(theme_freq.values(), default=1))

        with st.expander(f"**{theme}** — {count} mentions ({pct}%)  ·  {trend}"):
            st.markdown(
                f'<div class="bar-wrap"><div class="bar-fill" style="width:{bar_w}%"></div></div>',
                unsafe_allow_html=True,
            )
            theme_revs = [r for r in filtered if theme in (r.get("enrichment") or {}).get("themes", [])]
            theme_revs = sorted(theme_revs, key=lambda x: x.get("timestamp") or "", reverse=True)
            theme_revs.sort(key=lambda r: {"Negative": 0, "Neutral": 1, "Positive": 2}.get((r.get("enrichment") or {}).get("sentiment"), 3))
            theme_revs = theme_revs[:5]
            if theme_revs:
                for r in theme_revs:
                    render_review_card(r)
            else:
                st.info("No reviews in current filter window for this theme.")


# ═══════════════════════════════════════════════════════════════════════════════
# d) SEGMENT BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "👥 Segment Breakdown":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">👥</span><span class="sec-head-title">Segment Breakdown</span></div>', unsafe_allow_html=True)

    seg_theme: dict[str, dict[str, int]] = {}
    seg_sent: dict[str, dict[str, int]] = {}
    for r in filtered:
        enr = r.get("enrichment") or {}
        themes = enr.get("themes") or []
        sent = enr.get("sentiment", "Unknown")
        for seg in enr.get("segment") or []:
            seg_theme.setdefault(seg, {})
            seg_sent.setdefault(seg, {"Positive": 0, "Neutral": 0, "Negative": 0})
            for t in themes:
                seg_theme[seg][t] = seg_theme[seg].get(t, 0) + 1
            if sent in seg_sent[seg]:
                seg_sent[seg][sent] += 1

    all_segs = sorted(seg_theme.keys())
    if not all_segs:
        st.info("No segment data found for the current filters.")
    else:
        sel_segs = st.multiselect("Toggle user personas", all_segs, default=all_segs[:8], key="seg_sel")

        try:
            import altair as alt

            rows = [{"Segment": s, "Theme": t, "Count": c}
                    for s in sel_segs for t, c in seg_theme.get(s, {}).items()]
            if rows:
                df_seg = pd.DataFrame(rows)
                chart = (
                    alt.Chart(df_seg)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("Segment:N", title=None, axis=alt.Axis(labelColor="#A0A0A0", labelAngle=-30)),
                        y=alt.Y("Count:Q", stack="zero", title="Theme Mentions", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0")),
                        color=alt.Color("Theme:N", scale=alt.Scale(
                            range=["#FFE000", "#F5C800", "#00C853", "#FF3D57", "#A0A0A0", "#888", "#FFD000", "#FFC200"]
                        ), legend=alt.Legend(labelColor="#A0A0A0")),
                        tooltip=["Segment", "Theme", "Count"],
                    )
                    .properties(height=360, title=alt.TitleParams("Theme Distribution by User Segment", color="#F5F5F5", fontSize=14))
                    .configure_view(strokeOpacity=0, fill="#1A1A1A")
                    .configure_axis(gridColor="rgba(255,255,255,0.04)")
                )
                st.altair_chart(chart, use_container_width=True)

            # Sentiment per segment (normalised)
            st.markdown("#### 😊 Sentiment by Segment")
            sent_rows = [{"Segment": s, "Sentiment": lbl, "Count": cnt}
                         for s in sel_segs for lbl, cnt in seg_sent.get(s, {}).items()]
            if sent_rows:
                df_ss = pd.DataFrame(sent_rows)
                chart_ss = (
                    alt.Chart(df_ss)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("Segment:N", title=None, axis=alt.Axis(labelColor="#A0A0A0", labelAngle=-30)),
                        y=alt.Y("Count:Q", stack="normalize", title="Proportion", axis=alt.Axis(format="%", labelColor="#A0A0A0", titleColor="#A0A0A0")),
                        color=alt.Color("Sentiment:N", scale=alt.Scale(
                            domain=["Positive", "Neutral", "Negative"],
                            range=["#00C853", "#FFE000", "#FF3D57"]
                        ), legend=alt.Legend(labelColor="#A0A0A0")),
                        tooltip=["Segment", "Sentiment", "Count"],
                    )
                    .properties(height=240)
                    .configure_view(strokeOpacity=0, fill="#1A1A1A")
                    .configure_axis(gridColor="rgba(255,255,255,0.04)")
                )
                st.altair_chart(chart_ss, use_container_width=True)

        except ImportError:
            st.json(seg_theme)

        st.markdown("#### 📖 Browse Reviews by Persona")
        chosen = st.selectbox("Select a persona", sel_segs or all_segs, key="seg_browse")
        seg_revs = [r for r in filtered if chosen in (r.get("enrichment") or {}).get("segment", [])]
        seg_revs = sorted(seg_revs, key=lambda x: x.get("timestamp") or "", reverse=True)
        seg_revs.sort(key=lambda r: {"Negative": 0, "Neutral": 1, "Positive": 2}.get((r.get("enrichment") or {}).get("sentiment"), 3))
        seg_revs = seg_revs[:8]
        for r in seg_revs:
            render_review_card(r)


# ═══════════════════════════════════════════════════════════════════════════════
# e) AI CHATBOT (RAG)
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "💬 AI Chatbot":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">💬</span><span class="sec-head-title">AI Research Chatbot (RAG)</span></div>', unsafe_allow_html=True)
    st.markdown("Ask free-text questions about Blinkit user behavior. Answers are grounded **only** in real reviews retrieved from the vector store.")

    # Pre-set questions
    st.markdown("**💡 Suggested Questions:**")
    preset_qs = [
        "Why do Blinkit users keep buying the same categories?",
        "What stops Blinkit users from exploring new products?",
        "What trust signals do users need before buying a new category on Blinkit?",
        "What are the top recurring frustrations on Blinkit?",
        "Which Blinkit user segments explore new categories the most?",
        "How do users discover new products on Blinkit?",
        "What unmet needs do Blinkit users mention most?",
        "What role does habit and routine play in Blinkit shopping?",
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "pending_q" not in st.session_state:
        st.session_state.pending_q = ""

    chip_cols = st.columns(4)
    for i, q in enumerate(preset_qs):
        with chip_cols[i % 4]:
            lbl = q[:38] + ("…" if len(q) > 38 else "")
            if st.button(lbl, key=f"chip_{i}"):
                st.session_state.pending_q = q

    st.markdown("---")

    # Chat history
    for turn in st.session_state.chat_history:
        st.markdown(f'<div class="chat-user">🧑‍💼 {turn["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bot">🤖 {turn["answer"]}</div>', unsafe_allow_html=True)
        if turn.get("sources"):
            chips = "".join(
                f'<span class="src-chip">📌 {s.get("source","?")} · {str(s.get("timestamp",""))[:7]}</span>'
                for s in turn["sources"][:5]
            )
            st.markdown(f'<div class="src-chips">{chips}</div>', unsafe_allow_html=True)

    # Input
    user_input = st.chat_input("Ask a research question about Blinkit users…", key="chat_inp")
    question = user_input or st.session_state.get("pending_q", "")
    if st.session_state.pending_q:
        st.session_state.pending_q = ""

    if question:
        with st.spinner("🔍 Retrieving relevant Blinkit reviews…"):
            try:
                from src.rag.rag_chain import ask
                
                @st.cache_data(ttl=300)
                def cached_ask(q):
                    return ask(q, platform_filter=None)
                
                try:
                    result = cached_ask(question)
                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": result["answer"],
                        "sources": result["sources"],
                    })
                    st.rerun()
                except Exception as e:
                    if "429" in str(e) or "too many requests" in str(e).lower():
                        st.error("⚠️ The AI is currently receiving too many requests. Please wait a moment and try again.")
                    else:
                        raise e
            except ValueError as ve:
                st.error(f"⚙️ Configuration error: {ve}\n\nAdd your `GROQ_API_KEY` to the `.env` file.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.button("🗑️ Clear chat", key="clr"):
        st.session_state.chat_history = []
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# f) UNMET NEEDS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "🎯 Unmet Needs":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">🎯</span><span class="sec-head-title">Unmet Needs — Ranked List</span></div>', unsafe_allow_html=True)
    st.markdown("Aggregated from the `unmet_needs` field across all filtered Blinkit reviews.")

    def _group_need(need: str) -> str:
        n = need.lower()
        if "customer support" in n or "customer service" in n or "resolution" in n or "response" in n:
            return "Better Customer Support"
        if "refund" in n or "return" in n:
            return "Improved Refund & Return Policy"
        if "delivery" in n or "delay" in n or "time" in n or "late" in n:
            return "Reliable & Faster Delivery"
        if "stock" in n or "inventory" in n or "availability" in n or "out of" in n:
            return "Real-time Stock Availability"
        if "price" in n or "cost" in n or "expensive" in n:
            return "Lower Prices"
        if "quality" in n or "freshness" in n or "expired" in n or "condition" in n or "rotten" in n:
            return "Better Product Quality"
        if "substitution" in n or "replacement" in n:
            return "No Random Substitutions"
        if "search" in n or "discover" in n or "find" in n or "recommend" in n:
            return "Better Search & Discovery"
        if "ui" in n or "app" in n or "interface" in n or "bug" in n or "crash" in n:
            return "App Stability & UI Improvements"
        if "discount" in n or "offer" in n or "coupon" in n or "promo" in n:
            return "More Discounts & Offers"
        
        # Capitalize first letter as fallback
        return need.strip().capitalize()

    needs_cnt: dict[str, int] = {}
    for r in filtered:
        for need in (r.get("enrichment") or {}).get("unmet_needs") or []:
            if need.strip():
                grouped = _group_need(need.strip())
                needs_cnt[grouped] = needs_cnt.get(grouped, 0) + 1

    ranked = sorted(needs_cnt.items(), key=lambda x: x[1], reverse=True)

    if not ranked:
        st.info("No unmet needs data for the current filters.")
    else:
        try:
            import altair as alt
            top20 = ranked[:20]
            df_n = pd.DataFrame(top20, columns=["Need", "Count"])
            chart_n = (
                alt.Chart(df_n)
                .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color="#FFE000")
                .encode(
                    x=alt.X("Count:Q", title="Occurrences", axis=alt.Axis(labelColor="#A0A0A0", titleColor="#A0A0A0")),
                    y=alt.Y("Need:N", sort="-x", title=None, axis=alt.Axis(labelColor="#F5F5F5")),
                    tooltip=["Need", "Count"],
                )
                .properties(height=420, title=alt.TitleParams("Top 20 Unmet Needs — Blinkit Users", color="#F5F5F5", fontSize=14))
                .configure_view(strokeOpacity=0, fill="#1A1A1A")
                .configure_axis(gridColor="rgba(255,255,255,0.04)")
            )
            st.altair_chart(chart_n, use_container_width=True)
        except ImportError:
            pass

        st.markdown("#### 📋 Full Ranked List")
        for i, (need, count) in enumerate(ranked, 1):
            st.markdown(
                f'<div class="need-row"><div class="need-rank">#{i}</div><div class="need-text">{need}</div><div class="need-cnt">{count}×</div></div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCH SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════
elif nav == "📝 Research Synthesis":
    st.markdown('<div class="sec-head"><span class="sec-head-icon">📝</span><span class="sec-head-title">Research Synthesis — 8 Key Questions</span></div>', unsafe_allow_html=True)
    st.markdown("AI-generated answers to the 8 core research questions, synthesised from the full Blinkit review corpus via Groq.")

    q_map = {
        "q1_repeated_categories": "Q1 · Why do users repeatedly buy the same categories?",
        "q2_prevent_exploration": "Q2 · What prevents exploration of new categories?",
        "q3_discovery_methods": "Q3 · How do users currently discover new products?",
        "q4_habit_and_routine": "Q4 · What role do habit and routine play?",
        "q5_trust_signals": "Q5 · What trust signals are needed before trying new categories?",
        "q6_frustrations": "Q6 · What frustrations recur most often?",
        "q7_segments_exploration": "Q7 · Which segments show higher exploration tendency?",
        "q8_unmet_needs": "Q8 · What unmet needs come up consistently?",
    }

    if not synthesis:
        st.warning("Synthesis outputs not found. Run Phase 3 enrichment and synthesis first.")
    else:
        for key, label in q_map.items():
            answer = synthesis.get(key, "")
            if answer:
                with st.expander(f"**{label}**"):
                    st.markdown(
                        f'<div class="synth-card"><div class="synth-q">{label}</div><div class="synth-a">{answer}</div></div>',
                        unsafe_allow_html=True,
                    )
