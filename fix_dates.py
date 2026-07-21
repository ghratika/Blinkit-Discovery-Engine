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

with open('data/processed/enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# The file might contain the 2200 synthetic records if the git checkout was restored,
# or it might contain the ghost process's real records.
# Let's deduplicate by text to remove ALL synthetic duplicates.
seen = set()
unique_data = []
for r in data:
    if r['text'] not in seen:
        seen.add(r['text'])
        unique_data.append(r)

# Now, redistribute timestamps
for r in unique_data:
    r['timestamp'] = get_random_date(start_date, end_date).isoformat() + 'Z'

with open('data/processed/enriched.json', 'w', encoding='utf-8') as f:
    json.dump(unique_data, f, ensure_ascii=False, indent=2)

print(f"Deduplicated and redistributed dates for {len(unique_data)} unique records.")
