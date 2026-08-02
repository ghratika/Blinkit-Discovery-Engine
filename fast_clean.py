import json

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} reviews.")

kw = ['blinkit', 'grocery', 'delivery', 'order', 'app', 'minutes', 'cart', 'refund', 'items', 'zomato', 'swiggy', 'instamart', 'zepto']

valid_reviews = []
invalid_count = 0

for r in data:
    source = r.get('source', '').lower()
    text_lower = r.get('text', '').lower()
    
    # Play Store / App Store / MouthShut are always valid
    if 'play' in source or 'mouth' in source or 'app store' in source:
        valid_reviews.append(r)
        continue
        
    # Reddit and others must have at least one keyword
    is_valid = False
    for k in kw:
        if k in text_lower:
            is_valid = True
            break
            
    if is_valid:
        valid_reviews.append(r)
    else:
        print(f"Dropping: {r.get('text', '')[:50]}...")
        invalid_count += 1

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(valid_reviews, f, ensure_ascii=False, indent=2)

print(f"Done! Cleaned dataset saved with {len(valid_reviews)} reviews. Removed {invalid_count} garbage entries.")
