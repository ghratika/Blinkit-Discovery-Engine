import json
import re

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} reviews.")

kw = [r'\bblinkit\b', r'\bgrocery\b', r'\bdelivery\b', r'\border\b', r'\bapp\b', r'\bminutes\b', r'\bcart\b', r'\brefund\b', r'\bitems\b', r'\bzomato\b', r'\bswiggy\b', r'\binstamart\b', r'\bzepto\b', r'\bgrofers\b']
patterns = [re.compile(p, re.IGNORECASE) for p in kw]

valid_reviews = []
invalid_count = 0

for r in data:
    source = r.get('source', '').lower()
    text = r.get('text', '')
    
    # Play Store / App Store / MouthShut are always valid
    if 'play' in source or 'mouth' in source or 'app store' in source:
        valid_reviews.append(r)
        continue
        
    # Reddit and others must have at least one keyword as a full word
    is_valid = False
    for p in patterns:
        if p.search(text):
            is_valid = True
            break
            
    if is_valid:
        valid_reviews.append(r)
    else:
        invalid_count += 1

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(valid_reviews, f, ensure_ascii=False, indent=2)

print(f"Done! Cleaned dataset saved with {len(valid_reviews)} reviews. Removed {invalid_count} garbage entries.")
