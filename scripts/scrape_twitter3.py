import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from googlesearch import search

RAW_PATH = Path('data/raw/bulk_raw.json')

def run():
    print('[Twitter/Google] Fetching tweets for Blinkit...')
    queries = [
        'site:twitter.com/Blinkit "review"',
        'site:twitter.com "blinkit delivery"',
        'site:twitter.com "blinkit order worst"',
        'site:twitter.com "blinkit amazing fast"',
        'site:twitter.com "blinkit missing item"',
        'site:twitter.com "blinkit scam"',
        'site:twitter.com "blinkit groceries"',
        'site:twitter.com "blinkit customer care"'
    ]
    
    records = []
    if RAW_PATH.exists():
        records = json.loads(RAW_PATH.read_text('utf-8'))
        
    new_count = 0
    seen_texts = set(r['text'][:50] for r in records)
    
    for q in queries:
        print(f'[Twitter/Google] Searching: {q}')
        try:
            for result in search(q, num_results=20, advanced=True):
                # result has title, description, url
                text = result.description.strip()
                if len(text) > 30 and text[:50] not in seen_texts:
                    seen_texts.add(text[:50])
                    records.append({
                        'id': f'tw-bulk-{uuid.uuid4().hex[:12]}',
                        'source': 'Twitter/X',
                        'platform': 'Web',
                        'text': text,
                        'rating': None,
                        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'url': result.url,
                    })
                    new_count += 1
            time.sleep(1)
        except Exception as e:
            print('Error on query', q, e)
            
    RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), 'utf-8')
    print(f'[Twitter/Google] Saved {new_count} new tweets.')

if __name__ == '__main__':
    run()
