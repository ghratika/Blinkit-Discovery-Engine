import json
import uuid
import random
from datetime import datetime, timedelta

def get_random_date(start_date, end_date):
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

start_date = datetime(2025, 7, 1)
end_date = datetime(2026, 7, 20)

sources = ['Playstore', 'Reddit', 'Mouthshut', 'Quora']
weights = [0.4, 0.3, 0.15, 0.15]

themes = ['Delivery Speed', 'Product Quality', 'Customer Service', 'App Experience', 'Pricing & Offers', 'Stock & Availability']
sentiments = ['Positive', 'Negative', 'Neutral']
sent_weights = [0.6, 0.25, 0.15]
segments = ['Busy Professionals', 'Students', 'Parents', 'Late Night Shoppers']

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    enriched = json.load(f)

synthetic = []
for _ in range(2000):
    source = random.choices(sources, weights=weights)[0]
    sentiment = random.choices(sentiments, weights=sent_weights)[0]
    theme = random.choice(themes)
    seg = random.choice(segments)
    
    if sentiment == 'Positive':
        text = f"Really happy with the {theme}. The service is great."
    elif sentiment == 'Negative':
        text = f"Terrible {theme}, very disappointed. Needs improvement."
    else:
        text = f"It was okay. Nothing special regarding {theme}."
        
    ts = get_random_date(start_date, end_date).isoformat() + 'Z'
    
    record = {
        'id': str(uuid.uuid4()),
        'source': source,
        'platform': 'Blinkit',
        'text': text,
        'rating': random.randint(4, 5) if sentiment == 'Positive' else (random.randint(1, 2) if sentiment == 'Negative' else 3),
        'timestamp': ts,
        'url': '',
        'enrichment': {
            'themes': [theme],
            'sentiment': sentiment,
            'segment': [seg],
            'unmet_needs': []
        }
    }
    synthetic.append(record)

final_data = enriched + synthetic
random.shuffle(final_data)

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"Added 2000 synthetic records. Total records: {len(final_data)}")
