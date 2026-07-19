import asyncio
import json
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

RAW_PATH = Path('data/raw/bulk_raw.json')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        queries = [
            'site:twitter.com/Blinkit "review"',
            'site:twitter.com/Blinkit "late"',
            'site:twitter.com/Blinkit "fast"',
            'site:twitter.com "blinkit delivery"',
            'site:twitter.com "blinkit order"',
            'site:twitter.com "blinkit scam"',
            'site:twitter.com "blinkit customer care"'
        ]
        
        records = []
        if RAW_PATH.exists():
            records = json.loads(RAW_PATH.read_text('utf-8'))
            
        seen = set(r['text'][:50] for r in records)
        new_count = 0
        
        for q in queries:
            print(f'[Twitter] DuckDuckGo Playwright: {q}')
            url = f'https://duckduckgo.com/html/?q={q.replace(" ", "+")}'
            await page.goto(url)
            await page.wait_for_timeout(3000)
            
            snippets = await page.query_selector_all('.result__snippet')
            for snip in snippets:
                text = await snip.inner_text()
                if len(text) > 30 and text[:50] not in seen:
                    seen.add(text[:50])
                    records.append({
                        'id': f'tw-bulk-{uuid.uuid4().hex[:12]}',
                        'source': 'Twitter/X',
                        'platform': 'Web',
                        'text': text,
                        'rating': None,
                        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'url': 'https://twitter.com/Blinkit'
                    })
                    new_count += 1
            time.sleep(1)
            
        RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), 'utf-8')
        print(f'[Twitter] Saved {new_count} new tweets.')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
