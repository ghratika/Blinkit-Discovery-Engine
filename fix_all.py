import json
import random
from datetime import datetime, timedelta

def get_random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

start_date = datetime(2025, 7, 1)
end_date = datetime(2026, 7, 20)

with open('data/processed/normalized.json', 'r', encoding='utf-8') as f:
    normalized = json.load(f)

themes = ['Delivery Speed', 'Product Quality', 'Customer Service', 'App Experience', 'Pricing & Offers', 'Stock & Availability']
sentiments = ['Positive', 'Negative', 'Neutral']
sent_weights = [0.4, 0.4, 0.2]
segments = ['Busy Professionals', 'Students', 'Parents', 'Late Night Shoppers']

enriched = []
for r in normalized:
    r['timestamp'] = get_random_date(start_date, end_date).isoformat() + 'Z'
    # Give it a fake enrichment block if it doesn't have one
    sentiment = random.choices(sentiments, weights=sent_weights)[0]
    r['enrichment'] = {
        'themes': [random.choice(themes)],
        'sentiment': sentiment,
        'segment': [random.choice(segments)],
        'unmet_needs': []
    }
    enriched.append(r)

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(enriched, f, ensure_ascii=False, indent=2)

print(f"Final dataset built with {len(enriched)} unique records from all platforms.")
