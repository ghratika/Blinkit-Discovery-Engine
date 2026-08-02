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


import time

def run_synthesis(client: Groq, question_key: str, prompt_text: str) -> str:
    print(f"Running synthesis for {question_key}...")
    retries = 5
    for attempt in range(retries):
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
            error_str = str(e)
            if "429" in error_str and attempt < retries - 1:
                wait = 10 * (attempt + 1)
                print(f"Rate limit hit. Waiting {wait}s before retrying...")
                time.sleep(wait)
            else:
                print(f"Error running synthesis for {question_key}: {e}")
                return f"Error: {e}"
    return "Error: Max retries exceeded"


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

    # 2. Run LLM Synthesis
    client = get_client()
    results = {}
    
    unique_themes = list(set(all_themes))
    unique_needs = list(set(all_unmet_needs))

    for question_key, prompt_text in SYNTHESIS_PROMPTS.items():
        if "data" in prompt_text:
            formatted_prompt = prompt_text.format(data=json.dumps(exploration_data, ensure_ascii=False)[:3000]) # Cap text
        elif "unmet_needs" in prompt_text:
            formatted_prompt = prompt_text.format(unmet_needs=json.dumps(unique_needs, ensure_ascii=False))
        else:
            # Send all themes to questions asking for themes
            formatted_prompt = prompt_text.format(themes=json.dumps(unique_themes, ensure_ascii=False))
        
        answer = run_synthesis(client, question_key, formatted_prompt)
        results[question_key] = answer

    # 3. Save Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    print(f"Synthesis complete! Results saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
