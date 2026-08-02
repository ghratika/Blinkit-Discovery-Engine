import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} reviews.")

prompt_template = """You are an expert data cleaner. I will give you a JSON array of texts. 
For each text, determine if it is a genuine user review/experience about a quick-commerce delivery app (like Blinkit, Swiggy, Zomato, Zepto) or grocery delivery.
Return a JSON array of booleans (true/false) EXACTLY matching the length of the input array.
Set to false if it's a general quote, news headline, traffic update, survey response, political discussion, or spam.

Input:
{texts}

Output strictly a JSON array of booleans, e.g. [true, false, true]:
"""

batch_size = 15
valid_reviews = []
invalid_count = 0

for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    texts = [r.get('text', '') for r in batch]
    
    prompt = prompt_template.format(texts=json.dumps(texts, ensure_ascii=False))
    
    retries = 3
    while retries > 0:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                max_tokens=256,
            )
            response = chat_completion.choices[0].message.content
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end != -1:
                results = json.loads(response[start:end])
                if len(results) == len(batch):
                    for idx, is_valid in enumerate(results):
                        if is_valid:
                            batch[idx]['enrichment']['is_valid_review'] = True
                            valid_reviews.append(batch[idx])
                        else:
                            invalid_count += 1
                    break
            print(f"Failed to parse array properly, retrying...")
        except Exception as e:
            print(f"API Error: {e}")
            time.sleep(5)
        retries -= 1
        
    print(f"Processed {min(i+batch_size, len(data))}/{len(data)}. Invalid so far: {invalid_count}")
    time.sleep(2)

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(valid_reviews, f, ensure_ascii=False, indent=2)

print(f"Done! Cleaned dataset saved with {len(valid_reviews)} reviews. Removed {invalid_count} garbage entries.")
