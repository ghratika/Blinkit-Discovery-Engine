"""
Synthesis Runner — src/enrichment/synthesis_runner.py

Answers the 8 research questions by running dedicated synthesis prompts
against the enriched dataset using the Groq API.
Outputs to data/processed/synthesis_outputs.json
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from src.enrichment.prompts import SYNTHESIS_PROMPTS

load_dotenv()

INPUT_PATH = Path("data/processed/enriched.json")
OUTPUT_PATH = Path("data/processed/synthesis_outputs.json")
MODEL_NAME = "llama-3.1-8b-instant"

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key or api_key.endswith("here"):
        raise ValueError("GROQ_API_KEY not configured correctly in .env")
    return Groq(api_key=api_key)


def run_synthesis(client: Groq, question_key: str, prompt_text: str) -> str:
    print(f"Running synthesis for {question_key}...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a UX research lead summarizing findings for a product team."},
                {"role": "user", "content": prompt_text}
            ],
            model=MODEL_NAME,
            temperature=0.2,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error running synthesis for {question_key}: {e}")
        return f"Error: {e}"


def run() -> None:
    if not INPUT_PATH.exists():
        print(f"Input file {INPUT_PATH} not found. Run enrichment first.")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    # 1. Aggregate Data for Prompts
    all_themes = []
    negative_data = []
    discovery_themes = []
    routine_themes = []
    trust_themes = []
    negative_themes = []
    exploration_data = []
    all_unmet_needs = []

    for r in reviews:
        enrichment = r.get("enrichment")
        if not enrichment:
            continue
            
        themes = enrichment.get("themes", [])
        sentiment = enrichment.get("sentiment", "Neutral")
        segments = enrichment.get("segment", [])
        unmet_needs = enrichment.get("unmet_needs", [])
        
        all_themes.extend(themes)
        all_unmet_needs.extend(unmet_needs)
        
        if sentiment == "Negative":
            negative_themes.extend(themes)
            negative_data.append(f"Review: {r['text'][:100]}... Themes: {themes}")
            
        if any(seg for seg in segments):
            exploration_data.append(f"Segments: {segments}, Themes: {themes}")

    # Format the Prompts
    prompts_formatted = {
        "q1_repeated_categories": SYNTHESIS_PROMPTS["q1_repeated_categories"].format(themes=all_themes[:200]),
        "q2_prevent_exploration": SYNTHESIS_PROMPTS["q2_prevent_exploration"].format(data=negative_data[:50]),
        "q3_discovery_methods": SYNTHESIS_PROMPTS["q3_discovery_methods"].format(themes=all_themes[:200]),
        "q4_habit_and_routine": SYNTHESIS_PROMPTS["q4_habit_and_routine"].format(themes=all_themes[:200]),
        "q5_trust_signals": SYNTHESIS_PROMPTS["q5_trust_signals"].format(themes=all_themes[:200]),
        "q6_frustrations": SYNTHESIS_PROMPTS["q6_frustrations"].format(themes=negative_themes[:200]),
        "q7_segments_exploration": SYNTHESIS_PROMPTS["q7_segments_exploration"].format(data=exploration_data[:50]),
        "q8_unmet_needs": SYNTHESIS_PROMPTS["q8_unmet_needs"].format(unmet_needs=all_unmet_needs[:200]),
    }

    # 2. Run LLM Synthesis
    client = get_client()
    results = {}
    
    for key, prompt in prompts_formatted.items():
        answer = run_synthesis(client, key, prompt)
        results[key] = answer

    # 3. Save Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Synthesis complete! Results saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
