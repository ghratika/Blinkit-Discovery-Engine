import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

ENRICHED_PATH = Path("data/processed/enriched.json")

BATCH_THEME_PROMPT = """You are analyzing a batch of user reviews. For each review, extract a list of 1-3 short theme labels.
Examples of good themes: "Category Trust", "Delivery Delay", "Quality Issue", "Habit Loop".
DO NOT force themes if they don't apply. Extract exactly what the review is talking about.

Return ONLY a JSON dictionary where the keys are the Review IDs provided below, and the values are a list of extracted theme strings.

Reviews to process:
{batch_text}

Return ONLY valid JSON. No explanation."""

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key)

def extract_json(response_text: str) -> dict:
    match = re.search(r'\{.*\}', response_text.strip(), re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return json.loads(response_text.strip())

def process_batch(batch: list, client: Groq):
    batch_text_lines = []
    for idx, r in batch:
        text = r.get("text", "").replace("\n", " ").strip()
        batch_text_lines.append(f"Review ID {idx}: {text}")
        
    prompt = BATCH_THEME_PROMPT.format(batch_text="\n".join(batch_text_lines))
    
    for attempt in range(5):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            response = chat_completion.choices[0].message.content
            data = extract_json(response)
            
            for idx, r in batch:
                if not r.get("enrichment"):
                    r["enrichment"] = {}
                extracted = data.get(str(idx), data.get(idx, []))
                r["enrichment"]["themes"] = extracted if isinstance(extracted, list) else []
                
            return batch
        except Exception as e:
            if "429" in str(e):
                time.sleep(5 * (attempt + 1))
            else:
                print(f"Error processing batch: {e}")
                time.sleep(2)
                
    for idx, r in batch:
        if not r.get("enrichment"):
            r["enrichment"] = {}
        r["enrichment"]["themes"] = []
    return batch

def main():
    if not ENRICHED_PATH.exists():
        print("No enriched data found.")
        return
        
    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        reviews = json.load(f)
        
    client = get_client()
    print(f"Updating themes for {len(reviews)} reviews using batches...")
    
    batch_size = 10
    batches = []
    for i in range(0, len(reviews), batch_size):
        batch_slice = [(idx, reviews[idx]) for idx in range(i, min(i + batch_size, len(reviews)))]
        batches.append(batch_slice)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_batch, b, client): b for b in batches}
        processed_count = 0
        for future in as_completed(futures):
            b = future.result()
            processed_count += len(b)
            print(f"Processed {processed_count}/{len(reviews)} reviews")
                
    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2)
        
    print("Done. Wrote updated themes to enriched.json")

if __name__ == "__main__":
    main()
