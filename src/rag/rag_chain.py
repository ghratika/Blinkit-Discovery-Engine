"""
RAG Chain — src/rag/rag_chain.py

LangChain RAG pipeline using:
  - ChromaDB (vector store) as the retriever
  - Groq API via langchain-groq as the LLM
  - Strict system prompt forcing grounded, cited answers

Workaround for Windows App Control blocking uuid_utils._uuid_utils.dll:
  We inject a pure-Python stub for uuid_utils BEFORE any langchain import
  so that the DLL is never loaded.
"""

import os
import sys
import uuid as _stdlib_uuid
import types

# ── uuid_utils shim (prevents DLL load on restricted Windows machines) ─────────
# langchain-core >= 1.0 imports uuid_utils for uuid7 generation.
# On machines where App Control blocks the native _uuid_utils.dll we inject
# a pure-Python fallback that satisfies the import.
def _install_uuid_utils_shim():
    if "uuid_utils" in sys.modules:
        return  # already loaded (possibly successfully)
    try:
        import uuid_utils  # noqa: F401  – try native first
    except (ImportError, OSError):
        # Build a minimal stub that satisfies langchain_core.utils.uuid
        def _uuid7():
            return _stdlib_uuid.uuid4()  # uuid4 is a safe fallback

        shim = types.ModuleType("uuid_utils")
        shim.uuid7 = _uuid7
        shim.uuid4 = _stdlib_uuid.uuid4
        shim.UUID = _stdlib_uuid.UUID

        # Also satisfy uuid_utils.compat
        compat = types.ModuleType("uuid_utils.compat")
        compat.uuid7 = _uuid7
        compat.uuid4 = _stdlib_uuid.uuid4

        sys.modules["uuid_utils"] = shim
        sys.modules["uuid_utils.compat"] = compat

_install_uuid_utils_shim()

# ── Now safe to import langchain ───────────────────────────────────────────────
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

from src.storage.vector_store import query as vector_query

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
MODEL_NAME = "llama-3.1-8b-instant"
TOP_K = 7
SIMILARITY_THRESHOLD = 1.5  # ChromaDB cosine distance; lower = more similar

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a research assistant analyzing Blinkit user reviews.

Rules you MUST follow:
1. Answer the user's question based ONLY on the provided review excerpts below.
2. For EVERY claim or insight, cite the review source in this format: [Source, Blinkit, Month-Year].
   Example: "Users mention trust issues with fresh produce [Play Store, Blinkit, 2025-03]."
3. If the retrieved reviews do not contain enough information to answer the question confidently, say:
   "The available data doesn't cover this topic sufficiently."
4. Do NOT fabricate data, statistics, or reviews that are not present in the provided context.
5. Be specific and actionable — avoid vague statements like "users want a better experience."

Retrieved Review Excerpts:
{context}
"""

USER_PROMPT = "{question}"

# ── Context Builder ───────────────────────────────────────────────────────────

def _build_context(results: list[dict]) -> str:
    """Formats retrieved vector results into a readable context block."""
    if not results:
        return "No relevant reviews found."

    parts = []
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        source = meta.get("source", "Unknown")
        timestamp = meta.get("timestamp", "")
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            month_year = dt.strftime("%Y-%m")
        except Exception:
            month_year = timestamp[:7] if len(timestamp) >= 7 else "Unknown"

        similarity = r.get("distance", 0)
        parts.append(
            f"[{i}] Source: {source} | Platform: Blinkit | Date: {month_year} | "
            f"Similarity: {similarity:.2f}\n"
            f"Review: {r['text'][:500] + ('...' if len(r['text']) > 500 else '')}\n"
        )

    return "\n".join(parts)


# ── LLM Builder ───────────────────────────────────────────────────────────────

def _get_llm() -> ChatGroq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key.endswith("here"):
        raise ValueError("GROQ_API_KEY not configured correctly in .env")
    return ChatGroq(
        model=MODEL_NAME,
        temperature=0.1,
        api_key=api_key,
    )


# ── Main Query Function ───────────────────────────────────────────────────────

def ask(question: str, platform_filter: str | None = None) -> dict:
    """
    Runs the full RAG pipeline: retrieve -> build context -> LLM generation.

    Args:
        question: The user's free-text question.
        platform_filter: Optional platform filter (only Blinkit is used in this engine).

    Returns:
        A dict with:
            - "answer": The LLM-generated, cited answer string.
            - "sources": List of source metadata dicts for the retrieved reviews.
            - "context_used": The raw context block sent to the LLM.
    """
    # 1. Retrieve relevant reviews from vector store
    where_filter = None
    if platform_filter:
        where_filter = {"platform": {"$eq": platform_filter}}

    results = vector_query(question, top_k=TOP_K, where=where_filter)

    # Filter by similarity threshold (guard against completely irrelevant results)
    relevant = [r for r in results if r.get("distance", 9) <= SIMILARITY_THRESHOLD]
    
    if not relevant:
        return {
            "answer": "No relevant reviews found for this query.",
            "sources": [],
            "context_used": "",
        }

    context = _build_context(relevant)

    # 2. Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    # 3. Build LangChain chain
    llm = _get_llm()
    chain = (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )

    # 4. Invoke
    answer = chain.invoke({"context": context, "question": question})

    return {
        "answer": answer,
        "sources": [r["metadata"] for r in relevant],
        "context_used": context,
    }


# ── CLI Test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_questions = [
        "Why do Blinkit users keep buying the same categories?",
        "What stops Blinkit users from trying new categories?",
        "What do users say about trust before buying something new on Blinkit?",
    ]
    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = ask(q)
        print(f"A: {result['answer']}")
        print(f"   Sources used: {len(result['sources'])}")
