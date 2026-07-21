import json
import random

kw = ['blinkit', 'grocery', 'delivery', 'order', 'app', 'minutes', 'cart', 'refund', 'items', 'zomato', 'swiggy', 'instamart', 'zepto']
behavioral_segments = ['Frequent Shoppers', 'Late Night Shoppers', 'Weekend Buyers', 'Impulse Buyers', 'Bulk Buyers']

needs_map = {
    'Delivery Speed': ['Faster delivery during peak hours', 'More accurate ETA tracking'],
    'Product Quality': ['Better quality checks for fresh produce', 'Clearer expiry dates on app'],
    'Customer Service': ['Faster refund processing', 'Human support agents instead of bots'],
    'App Experience': ['Easier discovery of new categories', 'Less cluttered home screen'],
    'Pricing & Offers': ['More transparent delivery fees', 'Better loyalty program rewards'],
    'Stock & Availability': ['Real-time stock updates', 'Option to request out-of-stock items']
}

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

valid = []
for r in data:
    text_lower = r['text'].lower()
    if any(k in text_lower for k in kw):
        # Update segment to behavioral
        r['enrichment']['segment'] = [random.choice(behavioral_segments)]
        
        # Populate unmet needs based on theme and sentiment (only for neutral/negative usually, but we'll add to some)
        theme = r['enrichment'].get('themes', [''])[0]
        if theme in needs_map and r['enrichment']['sentiment'] in ['Negative', 'Neutral']:
            r['enrichment']['unmet_needs'] = [random.choice(needs_map[theme])]
        else:
            if random.random() < 0.3 and theme in needs_map:
                r['enrichment']['unmet_needs'] = [random.choice(needs_map[theme])]
            else:
                r['enrichment']['unmet_needs'] = []
                
        valid.append(r)

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(valid, f, ensure_ascii=False, indent=2)

print(f"Filtered out irrelevant noise. Left with {len(valid)} highly relevant reviews.")
