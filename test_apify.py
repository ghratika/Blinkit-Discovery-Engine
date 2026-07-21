import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ.get('APIFY_API_TOKEN'))

run_input = {
    "startUrls": [{"url": "https://www.reddit.com/search/?q=blinkit&sort=new"}],
    "maxItems": 10
}
print("Running apify search...")
run = client.actor("automation-lab/reddit-scraper").call(run_input=run_input)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item.get('title', '')[:50])
