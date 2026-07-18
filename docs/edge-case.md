# Edge Cases & Corner Cases: Blinkit AI-Powered Discovery Engine

This document outlines the potential edge cases, corner cases, and failure modes for the Blinkit Discovery Engine, along with proposed mitigation strategies for each layer of the architecture.

---

## 1. Data Collection & Normalization Edge Cases

| Edge Case | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Source UI/API Changes** | Scrapers (e.g., `google-play-scraper`, BeautifulSoup) break, resulting in zero data collected. | Use robust try-except blocks. Log scraper failures explicitly. Rely on multiple independent sources so if one fails, others still provide data. |
| **Hinglish / Mixed Language Reviews** | `langdetect` might misclassify Hinglish (Hindi written in English script) or the LLM might struggle to parse the sentiment. | Since this is common for Blinkit, prompt the Groq LLM specifically to expect and translate/handle Hinglish in the system prompt. |
| **Spam or Bot Reviews** | Keyword-stuffed or generic 5-star/1-star reviews ("nice app", "worst app") skew the theme frequencies. | Implement a minimum word count (e.g., > 10 words) during the normalization phase to filter out low-value reviews. |
| **Empty Strings Post-PII Stripping** | If a review was solely an email address or phone number, stripping it leaves an empty string. | Drop reviews where `length(text.strip()) == 0` during the cleaning phase before sending to Groq. |
| **No Reviews in Selected Timeframe** | A specific source or competitor app might have zero reviews in a highly constrained date filter. | Handle empty dataframes gracefully in the pipeline to prevent downstream crashes. |

---

## 2. LLM Enrichment Layer (Groq API) Edge Cases

| Edge Case | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Invalid JSON Output** | The LLM returns malformed JSON or includes conversational text (e.g., "Here is your JSON: {...}"), breaking the parser. | Use robust JSON parsing (e.g., `json.loads` with regex to extract the block). If parsing fails, retry the prompt once. If it still fails, log and skip the review. |
| **Hallucinated or Bizarre Segment Tags** | Since segments are inferred freely, the LLM might generate overly specific or nonsensical tags (e.g., "angry guy who likes cheese"). | Implement a post-processing clustering script to map semantically similar tags to canonical buckets. Drop tags with only a single occurrence across the corpus. |
| **Sarcasm and Irony** | Reviews like "Great job Blinkit, delivering expired milk again!" are tagged as Positive due to "Great job". | Include examples of quick-commerce sarcasm in the prompt's few-shot examples to train the LLM on this specific pattern. |
| **Conflicting Sentiments in One Review** | "Zepto is fast but Blinkit has better quality." - LLM struggles to assign a single sentiment. | Prompt the LLM to assign sentiment specifically *relative to the target platform* being analyzed in that row. |
| **Hard Rate Limits (429 Errors)** | Even with batches of 10 and exponential backoff, Groq's daily or hourly free-tier limits might be exhausted. | Catch persistent 429s and pause the entire enrichment queue. Save the current state to disk so the run can be resumed the next day. |

---

## 3. Storage & RAG (Retrieval Augmented Generation) Edge Cases

| Edge Case | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Low Relevance Retrieval** | A highly specific user query returns reviews that are completely irrelevant (low cosine similarity). | Implement a similarity threshold score. If no documents pass the threshold, instruct the RAG chain to explicitly state: "No relevant reviews found for this query." |
| **Context Window Exceeded** | Retrieving too many long reviews for a RAG prompt exceeds the LLM's context window. | Cap the `top-k` retrieval to 5-7 reviews. Truncate exceptionally long reviews during the vector embedding phase. |
| **ChromaDB Initialization Failure** | On Hugging Face Spaces (or local), SQLite/ChromaDB locks or fails to initialize if multiple threads access it. | Ensure ChromaDB is instantiated as a singleton in the Streamlit app, or use thread-safe read-only modes where appropriate. |

---

## 4. Frontend & Deployment Edge Cases (Streamlit on Hugging Face Spaces)

| Edge Case | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Cold Starts (Spaces Sleeping)** | Free Hugging Face Spaces go to sleep after ~48 hours of inactivity. The next user experiences a 2-3 minute loading screen. | Document this expected behavior in the README. Consider setting up a cron job (via GitHub Actions) to ping the Space daily to keep it awake. |
| **Empty Chart States** | A user filters to a highly specific segment (e.g., "Expat") with only 1 review, causing pie charts or timeline graphs to look broken or throw errors. | Add conditional rendering: `if len(filtered_df) == 0: st.warning("Not enough data for this segment.")` instead of attempting to draw the chart. |
| **Concurrent User Rate Limiting** | Multiple reviewers testing the RAG Chatbot simultaneously exhaust the Groq API rate limit. | Add a `@st.cache_data` wrapper around common chatbot queries. Add an explicit error message in the chat UI if a `429` is hit, asking the user to wait a moment. |
