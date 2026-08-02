import json
import os
import time
from groq import Groq
from dotenv import load_dotenv
from src.enrichment.prompts import SYNTHESIS_PROMPTS

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    reviews = json.load(f)

with open('data/processed/synthesis_outputs.json', 'r', encoding='utf-8') as f:
    synthesis = json.load(f)

if "Error" in synthesis.get("q7_segments_exploration", ""):
    print("Fixing q7...")
    exploration_data = []
    for r in reviews:
        enrichment = r.get("enrichment")
        if not enrichment: continue
        themes = enrichment.get("themes", [])
        segments = enrichment.get("segment", [])
        if any(seg for seg in segments):
            exploration_data.append(f"Segments: {segments}, Themes: {themes}")

    prompt_text = SYNTHESIS_PROMPTS["q7_segments_exploration"]
    formatted_prompt = prompt_text.format(data=json.dumps(exploration_data, ensure_ascii=False)[:3000])
    
    retries = 3
    while retries > 0:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a UX research lead summarizing findings for a product team."},
                    {"role": "user", "content": formatted_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.2,
                max_tokens=1024,
            )
            synthesis["q7_segments_exploration"] = chat_completion.choices[0].message.content
            print("Fixed q7 successfully.")
            break
        except Exception as e:
            print(f"Rate limit: {e}")
            time.sleep(15)
            retries -= 1

    with open('data/processed/synthesis_outputs.json', 'w', encoding='utf-8') as f:
        json.dump(synthesis, f, ensure_ascii=False, indent=2)
