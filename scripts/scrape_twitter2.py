import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from duckduckgo_search import DDGS

RAW_PATH = Path('data/raw/bulk_raw.json')

def run():
    ddgs = DDGS()
    print('[Twitter] Fetching tweets for Blinkit via DuckDuckGo...')
    queries = [
        'site:twitter.com/Blinkit "review"',
        'site:twitter.com/Blinkit "late"',
        'site:twitter.com/Blinkit "fast"',
        'site:twitter.com "blinkit delivery"',
        'site:twitter.com "blinkit order"',
        'site:twitter.com "blinkit worst"',
        'site:twitter.com "blinkit amazing"'
    ]
    
    records = []
    if RAW_PATH.exists():
        records = json.loads(RAW_PATH.read_text('utf-8'))
        
    new_count = 0
    seen_texts = set(r['text'][:50] for r in records)
    
    for q in queries:
        print(f'[Twitter] Searching: {q}')
        try:
            results = list(ddgs.text(q, max_results=30))
            for r in results:
                text = r.get('body', '').strip()
                if len(text) > 30 and text[:50] not in seen_texts:
                    seen_texts.add(text[:50])
                    records.append({
                        'id': f'tw-bulk-{uuid.uuid4().hex[:12]}',
                        'source': 'Twitter/X',
                        'platform': 'Web',
                        'text': text,
                        'rating': None,
                        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'url': r.get('href', ''),
                    })
                    new_count += 1
            time.sleep(2)
        except Exception as e:
            print('Error on query', q, e)
            
    RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), 'utf-8')
    print(f'[Twitter] Saved {new_count} new tweets.')

if __name__ == '__main__':
    run()
