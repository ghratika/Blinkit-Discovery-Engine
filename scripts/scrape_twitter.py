
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from ntscraper import Nitter

RAW_PATH = Path('data/raw/bulk_raw.json')

def run():
    scraper = Nitter()
    print('[Twitter] Fetching tweets for Blinkit...')
    tweets = scraper.get_tweets('blinkit', mode='term', number=150)
    tweet_list = tweets.get('tweets', [])
    print(f'[Twitter] Got {len(tweet_list)} tweets.')
    
    records = []
    if RAW_PATH.exists():
        records = json.loads(RAW_PATH.read_text('utf-8'))
        
    new_count = 0
    for t in tweet_list:
        text = t.get('text', '').strip()
        if len(text) > 30:
            records.append({
                'id': f'tw-bulk-{uuid.uuid4().hex[:12]}',
                'source': 'Twitter/X',
                'platform': 'Web',
                'text': text,
                'rating': None,
                'timestamp': t.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),
                'url': t.get('link', ''),
            })
            new_count += 1
            
    RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), 'utf-8')
    print(f'[Twitter] Saved {new_count} new tweets.')

if __name__ == '__main__':
    run()
