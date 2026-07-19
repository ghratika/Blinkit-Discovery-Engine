
import asyncio
import json
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

RAW_PATH = Path('data/raw/bulk_raw.json')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print('[MouthShut] Navigating to reviews...')
        await page.goto('https://www.mouthshut.com/product-reviews/blinkit-reviews-925738270', wait_until='domcontentloaded')
        
        print('[MouthShut] Scrolling to load reviews...')
        for _ in range(15):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
        articles = await page.query_selector_all('.review-article')
        print(f'[MouthShut] Found {len(articles)} review articles')
        
        records = []
        if RAW_PATH.exists():
            records = json.loads(RAW_PATH.read_text('utf-8'))
            
        new_count = 0
        for a in articles:
            text_el = await a.query_selector('.more.reviewdata')
            if not text_el:
                text_el = await a.query_selector('.review-data')
            
            if text_el:
                text = (await text_el.inner_text()).strip()
                if len(text) > 30:
                    records.append({
                        'id': f'ms-bulk-{uuid.uuid4().hex[:12]}',
                        'source': 'MouthShut',
                        'platform': 'Web',
                        'text': text,
                        'rating': None,
                        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'url': 'https://www.mouthshut.com/product-reviews/blinkit-reviews-925738270',
                    })
                    new_count += 1
        
        RAW_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), 'utf-8')
        print(f'[MouthShut] Saved {new_count} new reviews.')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
