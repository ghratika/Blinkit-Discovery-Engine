
import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print('Going to Mouthshut...')
        await page.goto('https://www.mouthshut.com/product-reviews/blinkit-reviews-925738270', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        for i in range(10):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000)
            
        articles = await page.query_selector_all('.review-article')
        print(f'Found {len(articles)} review articles')
        
        records = []
        for a in articles:
            text_el = await a.query_selector('.more.reviewdata')
            if not text_el:
                text_el = await a.query_selector('.review-data')
            
            if text_el:
                text = await text_el.inner_text()
                if len(text) > 30:
                    records.append(text)
        
        with open('ms_reviews.json', 'w', encoding='utf-8') as f:
            json.dump(records, f)
            
        print('Saved', len(records), 'reviews.')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())
