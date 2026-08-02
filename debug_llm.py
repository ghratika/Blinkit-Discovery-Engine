import os, sys
sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

GENUINENESS_SYSTEM = (
    "You are a data quality classifier. "
    "You ONLY output a single JSON boolean: true or false. "
    "No explanation, no code, no extra text."
)

GENUINENESS_USER = (
    "Is the following text a genuine first-hand customer experience about ordering, "
    "delivery, product quality, refunds, packaging, customer support, or the app experience "
    "on Blinkit (an Indian grocery delivery app)?\n\n"
    "Answer true only for real personal experiences. "
    "Answer false for: vague one-word reviews, Hinglish text, spam, gibberish, "
    "unrelated topics, news, surveys, or general questions.\n\n"
    "Text: {text}\n\nAnswer (true or false):"
)

test_cases = [
    ("good", False),
    ("accha he good lakin kuc area me bilnkit app kam nahi karta", False),  # Hinglish
    ("If an order is placed by mistake, they do not even cancel it", True),
    ("ok", False),
    ("expensive then other online apps", True),
    ("Which credit card should I get?", False),
    ("Delivery was fast but the vegetables were wilted and smelled bad", True),
]

print(f"Testing with gemma2-9b-it (per-review, system message):\n")
for text, expected in test_cases:
    user_msg = GENUINENESS_USER.format(text=text[:500])
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": GENUINENESS_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        model="gemma2-9b-it",
        temperature=0.0,
        max_tokens=8,
    )
    raw = resp.choices[0].message.content.strip().lower()
    result = "true" in raw
    status = "OK" if result == expected else "WRONG"
    print(f"  [{status}] expected={expected} got='{raw}' | {text[:60]}")
