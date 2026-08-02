import json
import os
from groq import Groq
from dotenv import load_dotenv
from src.enrichment.prompts import ENRICHMENT_USER_PROMPT_TEMPLATE, ENRICHMENT_SYSTEM_PROMPT
from src.enrichment.enrichment_runner import extract_json

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

texts = [
    "Govt summons Russian envoy after 4 Indians die in merchant ship attack in Ukraine",
    "Blinkit delivered my groceries in 8 minutes, amazing service!"
]

for t in texts:
    prompt = ENRICHMENT_USER_PROMPT_TEMPLATE.format(review_text=t)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": ENRICHMENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.0,
        max_tokens=256,
    )
    result = extract_json(chat_completion.choices[0].message.content)
    print(f"Text: {t[:30]}... -> is_valid_review: {result.get('is_valid_review')}")
