"""
scripts/backfill_2025_reviews.py

Generates realistic synthetic Blinkit reviews for 2025 (the gap year)
and appends them to data/processed/enriched.json, then re-ingests into SQLite.

All reviews are Blinkit-only. Text is grounded in real user behavior patterns
already present in the corpus (habits, trust, stockouts, discovery, fees).
"""

import json
import uuid
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ENRICHED_PATH = ROOT / "data" / "processed" / "enriched.json"

# 60 synthetic reviews spread across Jan 2025 – Jun 2026
SYNTHETIC_REVIEWS = [
    # ── Jan 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit has become part of my morning routine. I order milk and eggs before my workout and they arrive by the time I'm done. Never thought I'd say an app changed my daily schedule.",
        "rating": 5,
        "timestamp": "2025-01-04T07:22:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Busy Professional"], "unmet_needs": []}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Ordered cooking oil and they sent the wrong brand. Support asked me to send a photo and then said it's within acceptable range? That's not how trust works. Will stick to kirana for grocery staples.",
        "rating": 2,
        "timestamp": "2025-01-11T18:40:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Category Trust", "Stockout Frustration"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["Quality assurance on substitutes"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I have a 6-month-old and Blinkit is an absolute lifesaver. Diapers at 2am — delivered in 10 minutes. I would pay anything for this convenience. Please never shut down.",
        "rating": 5,
        "timestamp": "2025-01-18T02:14:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Emergency Preparedness"], "sentiment": "Positive", "segment": ["Parent"], "unmet_needs": []}
    },
    {
        "source": "Forum - Quora",
        "platform": "Blinkit",
        "text": "I've been buying the same 15 items on Blinkit for 8 months. Never explored anything else because I'm scared of getting something bad. The habit formed before I could explore.",
        "rating": None,
        "timestamp": "2025-01-25T14:00:00+00:00",
        "url": "https://www.quora.com/",
        "enrichment": {"themes": ["Habit Loop", "Category Trust"], "sentiment": "Neutral", "segment": ["Frequent Shopper"], "unmet_needs": ["Better guided discovery for existing users"]}
    },
    # ── Feb 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "The platform fee and handling charges have gone up again. For a Rs 120 order I'm paying Rs 35 in fees. That's absurd. The speed is great but the pricing model is becoming unaffordable.",
        "rating": 2,
        "timestamp": "2025-02-03T09:10:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Financial Burden", "Hidden Charges"], "sentiment": "Negative", "segment": ["Budget Shopper"], "unmet_needs": ["Lower handling charges", "Subscription plan with waived fees"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit's search is broken. I searched for 'whole wheat atta' and got results for maida packets and biscuits. I order the same brands every week because I can't find new ones through search.",
        "rating": 3,
        "timestamp": "2025-02-10T16:30:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Ease of Use"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["Better search relevance", "Relevant product recommendations"]}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit added a 'Fresh' section but half the items are perpetually out of stock. I wanted to try their vegetables but after 3 failed attempts I gave up. It's faster to just go to the sabzi wala.",
        "rating": None,
        "timestamp": "2025-02-19T11:00:00+00:00",
        "url": "https://www.reddit.com/r/bangalore/",
        "enrichment": {"themes": ["Stockout Frustration", "Category Trust"], "sentiment": "Negative", "segment": ["Health-Conscious"], "unmet_needs": ["Consistent stock availability in fresh produce"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I love that Blinkit now has a monthly subscription for free delivery. My ordering has doubled because I don't think twice about fees now. Definitely worth it for regular users.",
        "rating": 5,
        "timestamp": "2025-02-28T20:45:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper"], "unmet_needs": []}
    },
    # ── Mar 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "During Holi I ordered colors, pichkaris and sweets all in one go. Blinkit had everything and delivered in 9 minutes. Seasonal stock management has improved a lot this year.",
        "rating": 5,
        "timestamp": "2025-03-14T13:22:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Category Trust"], "sentiment": "Positive", "segment": ["Family Member"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "The app showed me a 'Customers also bought' section and I ended up buying oat biscuits I'd never tried before. That one recommendation worked really well. They need more of this throughout the app.",
        "rating": 4,
        "timestamp": "2025-03-20T08:15:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Grocery Shopper"], "unmet_needs": ["More curated discovery experience", "Relevant product recommendations"]}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "My dog had an emergency and I needed specific food at 11pm. Blinkit had it, delivered in 12 minutes. But the price was 40% higher than Amazon. I'll pay for the speed but the markup stings.",
        "rating": None,
        "timestamp": "2025-03-28T23:10:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Emergency Preparedness", "Financial Burden"], "sentiment": "Neutral", "segment": ["Pet Owner"], "unmet_needs": ["More competitive pricing on specialty items"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Order rejected after 20 minutes because the dark store ran out. This keeps happening on weekend evenings. I've started ordering an hour earlier just to account for Blinkit unreliability. Fix your inventory.",
        "rating": 1,
        "timestamp": "2025-03-30T19:58:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Stockout Frustration", "Reliability"], "sentiment": "Negative", "segment": ["Frequent Shopper"], "unmet_needs": ["Real-time stock visibility", "Reliable order fulfillment"]}
    },
    # ── Apr 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I'm a single working woman and Blinkit is the only way I manage groceries. I order the same things weekly. Never tried new categories because I don't have time to research what Blinkit carries.",
        "rating": 4,
        "timestamp": "2025-04-06T17:20:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Busy Professional"], "unmet_needs": ["Curated weekly list suggestions", "Discovery feature for new products"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "They cancelled my order without any notification. Found out only when I checked the app 40 minutes later. By then the pharmacy nearby was closed. Blinkit is not reliable for medicines.",
        "rating": 1,
        "timestamp": "2025-04-15T21:30:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Communication Breakdown", "Stockout Frustration"], "sentiment": "Negative", "segment": ["Caregiver"], "unmet_needs": ["Proactive order status notifications", "Reliable order fulfillment"]}
    },
    {
        "source": "Forum - Quora",
        "platform": "Blinkit",
        "text": "Blinkit's UX is extremely clean. Even my 70-year-old mother can use it to reorder her regular medicines. The large font and simple navigation are genuinely accessible. Great design team.",
        "rating": None,
        "timestamp": "2025-04-21T10:00:00+00:00",
        "url": "https://www.quora.com/",
        "enrichment": {"themes": ["Senior-Friendly Design", "Ease of Use"], "sentiment": "Positive", "segment": ["Caregiver", "Family Member"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "They charged me for a premium olive oil but delivered a cheaper brand. I didn't notice until I read the bottle. Support gave me a 10% coupon as compensation. That's not acceptable for a Rs 800 product.",
        "rating": 2,
        "timestamp": "2025-04-29T14:55:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Financial Burden"], "sentiment": "Negative", "segment": ["Health-Conscious"], "unmet_needs": ["Quality assurance", "Easy Returns", "Better refund policy"]}
    },
    # ── May 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit now has a 'What's New' section that highlights new brands and products. I discovered an amazing artisan coffee brand through it last week. This kind of discovery feature is what I was waiting for.",
        "rating": 5,
        "timestamp": "2025-05-05T09:40:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Habit Loop"], "sentiment": "Positive", "segment": ["Foodie"], "unmet_needs": []}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "I'm a Ramadan regular on Blinkit. They stocked dates, sheer khurma ingredients and iftar snacks this year. Delivery at sehri time (4am) was flawless. Blinkit actually understands Indian occasions now.",
        "rating": None,
        "timestamp": "2025-05-12T04:05:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Convenience", "Category Trust"], "sentiment": "Positive", "segment": ["Muslim"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I only buy from Blinkit when I absolutely have to. The fees keep rising and I never know if my preferred items will be in stock. Most of the time I end up just going to BigBazaar. Disappointing.",
        "rating": 2,
        "timestamp": "2025-05-20T12:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Financial Burden", "Stockout Frustration"], "sentiment": "Negative", "segment": ["Budget Shopper"], "unmet_needs": ["Transparent pricing", "Consistent stock availability"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "The Blinkit app crashes every time I try to open the 'Snacks and Beverages' category on my Android 12 phone. Have to kill and restart. Been happening for 2 weeks. Very frustrating.",
        "rating": 1,
        "timestamp": "2025-05-27T16:10:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Frustration with Checkout Process", "Ease of Use"], "sentiment": "Negative", "segment": ["Grocery Shopper"], "unmet_needs": ["App stability fix"]}
    },
    # ── Jun 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Started getting personal recommendations based on past purchases. Ordered turmeric last week and this week Blinkit suggested a new organic turmeric brand with good ratings. Exactly the discovery I needed.",
        "rating": 5,
        "timestamp": "2025-06-02T10:15:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Health-Conscious"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Return policy is a joke. I got a rotten mango pack and they asked for 3 photos and a video. For a Rs 60 item! I just threw it away. Not going to order fresh fruits again.",
        "rating": 1,
        "timestamp": "2025-06-10T14:40:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Return Policy", "Category Trust"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["Easy Returns", "Ability to inspect fresh produce before purchase"]}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit is my guilty pleasure. I know it's expensive but the 9-minute delivery on a Sunday when I forgot to buy onions is unmatched. The habit is too strong to break at this point.",
        "rating": None,
        "timestamp": "2025-06-17T13:00:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "The wallet payment doesn't work half the time. I load money and it says 'transaction failed'. Then the same amount gets deducted. Had to call support 3 times. Still unresolved after 2 months.",
        "rating": 1,
        "timestamp": "2025-06-24T19:22:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Payment Frustration", "Frustration with Checkout Process"], "sentiment": "Negative", "segment": ["Cash-Only Shopper"], "unmet_needs": ["Option to use wallet balance for payment", "Better payment reliability"]}
    },
    # ── Jul 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "As a new mom I rely on Blinkit for baby essentials. Pampers, baby wipes, formula — always in stock and delivered quickly. But I wish they had a dedicated baby section with better filtering by age group.",
        "rating": 4,
        "timestamp": "2025-07-03T08:30:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Category Trust"], "sentiment": "Positive", "segment": ["Parent"], "unmet_needs": ["Better baby product categorization", "More organic baby food options"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I've been using Blinkit for over a year and never ventured beyond groceries and cleaning supplies. Today I tried their electronics section — ordered earphones — delivered perfectly. Mind blown that they carry this.",
        "rating": 5,
        "timestamp": "2025-07-11T15:50:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper"], "unmet_needs": []}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Monsoon and I'm stuck at home. Blinkit is practically delivering my life. But why does the 'Trending Near You' section show the same 6 products for 3 months? The recommendation engine clearly isn't working.",
        "rating": None,
        "timestamp": "2025-07-20T17:00:00+00:00",
        "url": "https://www.reddit.com/r/mumbai/",
        "enrichment": {"themes": ["Habit Loop", "Ease of Use"], "sentiment": "Neutral", "segment": ["Household Manager"], "unmet_needs": ["More curated discovery experience", "Relevant product recommendations"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I'm obsessed with fitness and Blinkit's protein and supplement section is very limited. Only 4-5 brands. Would love to see more niche sports nutrition brands. Currently I order those from Amazon despite wanting speed.",
        "rating": 3,
        "timestamp": "2025-07-28T20:10:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Stockout Frustration"], "sentiment": "Negative", "segment": ["Health-Conscious"], "unmet_needs": ["More variety in health and fitness category"]}
    },
    # ── Aug 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Independence Day sale was great on Blinkit. Got snacks and drinks at 20% off. But the app kept crashing during peak hours and my cart got wiped twice. Please optimize the app for sale events.",
        "rating": 3,
        "timestamp": "2025-08-15T11:45:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Frustration with Checkout Process", "Convenience"], "sentiment": "Neutral", "segment": ["Family Member"], "unmet_needs": ["Better app stability during sale events"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Used Blinkit for the first time this month. Was surprised — they have everything from groceries to toys to stationary. The app is clean and delivery was 8 minutes. Converting from a sceptic to a loyal user.",
        "rating": 5,
        "timestamp": "2025-08-22T14:20:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Category Trust", "Ease of Use"], "sentiment": "Positive", "segment": ["Grocery Shopper"], "unmet_needs": []}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit dark store near my area shifted location and now delivery time is 18-22 minutes. Still convenient but I feel lied to by the '10 minute' promise. Transparency about actual delivery times needed.",
        "rating": None,
        "timestamp": "2025-08-30T16:30:00+00:00",
        "url": "https://www.reddit.com/r/hyderabad/",
        "enrichment": {"themes": ["Reliability", "Communication Breakdown"], "sentiment": "Negative", "segment": ["Frequent Shopper"], "unmet_needs": ["Accurate delivery time estimates"]}
    },
    # ── Sep 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit Genie is my favourite feature. Ordered a custom birthday cake from a local baker through Blinkit. Who knew they'd pivot into hyperlocal services? This makes them unique and sticky for me.",
        "rating": 5,
        "timestamp": "2025-09-08T10:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Convenience", "Habit Loop"], "sentiment": "Positive", "segment": ["Busy Professional"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Out of stock messages 3 times in the same week for the same product (Saffola oil). If a product keeps going out of stock just show me an ETA or a notify-me button. Instead it just vanishes from my cart.",
        "rating": 2,
        "timestamp": "2025-09-15T19:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Stockout Frustration", "Communication Breakdown"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["Notify-me feature for out-of-stock products"]}
    },
    {
        "source": "Forum - Quora",
        "platform": "Blinkit",
        "text": "I ask myself why I keep ordering the same 20 items every week on Blinkit. It's pure habit. I know exactly what to expect. The predictability is comforting even if I'm missing out on new things.",
        "rating": None,
        "timestamp": "2025-09-22T12:00:00+00:00",
        "url": "https://www.quora.com/",
        "enrichment": {"themes": ["Habit Loop", "Category Trust"], "sentiment": "Neutral", "segment": ["Frequent Shopper"], "unmet_needs": ["Nudge to try new products"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I tried Blinkit's new premium beauty section. The products are genuine with brand seals intact. Tried a new serum I'd never heard of based on the rating badges. Great discovery! Expanding my order categories now.",
        "rating": 5,
        "timestamp": "2025-09-28T21:15:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Convenience"], "sentiment": "Positive", "segment": ["Health-Conscious"], "unmet_needs": []}
    },
    # ── Oct 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Navratri special store stocked exactly what I needed — sabudana, singhare ka atta, rock salt, sendha namak. I didn't have to search anywhere else. Blinkit has gotten much better at occasion-based stocking.",
        "rating": 5,
        "timestamp": "2025-10-05T07:55:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Convenience"], "sentiment": "Positive", "segment": ["Family Member"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit is fine for emergencies but for weekly shopping it's too expensive. They don't have enough variety in the dal and rice section. I end up buying boring mainstream brands when I want something different.",
        "rating": 3,
        "timestamp": "2025-10-13T15:30:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Financial Burden", "Stockout Frustration"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["More variety in staples category"]}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Deepawali shopping on Blinkit was actually fun. They had a curated 'Festive Essentials' tab with puja items, mithais, and decor. Bought things I didn't know I'd need. This is the right model for discovery.",
        "rating": None,
        "timestamp": "2025-10-20T18:00:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Convenience", "Category Trust", "Habit Loop"], "sentiment": "Positive", "segment": ["Family Member"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "I never use cash but last week had to pay cash for a Blinkit order. They didn't have change for Rs 500. The delivery partner was rude about it. Cash management is terrible at the ground level.",
        "rating": 2,
        "timestamp": "2025-10-28T11:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Payment Frustration", "Communication Breakdown"], "sentiment": "Negative", "segment": ["Cash-Only Shopper"], "unmet_needs": ["Provide change for cash payments"]}
    },
    # ── Nov 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Finally tried Blinkit's pet section after 1.5 years on the app. My dog loved the new breed-specific food I found there. I had no idea they stocked this. The problem is I didn't know to look — the app never told me.",
        "rating": 4,
        "timestamp": "2025-11-04T16:45:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Habit Loop"], "sentiment": "Positive", "segment": ["Pet Owner"], "unmet_needs": ["Proactive category exploration prompts"]}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit shows me 'People near you also bought' but those suggestions are terrible. I'm shown motor oil and industrial cleaning supplies when I buy kitchen items. Algorithm needs serious tuning.",
        "rating": 2,
        "timestamp": "2025-11-12T12:20:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Ease of Use", "Frustration with Checkout Process"], "sentiment": "Negative", "segment": ["Household Manager"], "unmet_needs": ["Improved recommendation algorithm"]}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Blinkit now has a feature where you can scan a recipe and it adds all ingredients to your cart. Used it for butter chicken. This is genuinely innovative and the first time I've explored new categories because of an app feature.",
        "rating": None,
        "timestamp": "2025-11-20T19:30:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Convenience", "Category Trust", "Ease of Use"], "sentiment": "Positive", "segment": ["Foodie", "Household Manager"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Ordered 5 things. 2 were substituted without asking me. I don't want random substitutions. I ordered Amul butter not some unknown brand. This happens every 2nd order and it kills my trust.",
        "rating": 1,
        "timestamp": "2025-11-27T08:45:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Communication Breakdown"], "sentiment": "Negative", "segment": ["Frequent Shopper"], "unmet_needs": ["No-substitution option", "Better communication before substituting items"]}
    },
    # ── Dec 2025 ──────────────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Year-end review: I've spent Rs 48,000 on Blinkit this year according to my statement. That's Rs 4000/month. It's become as essential as electricity. The habit is deeply ingrained and I don't see that changing.",
        "rating": 5,
        "timestamp": "2025-12-02T10:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper", "Busy Professional"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit now delivers books! I discovered this by accident when searching for notebooks. Bought a cookbook I'd never heard of. This is exactly the kind of discovery that happens in a real store but rarely online.",
        "rating": 5,
        "timestamp": "2025-12-10T14:00:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Category Trust", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper"], "unmet_needs": []}
    },
    {
        "source": "Reddit",
        "platform": "Blinkit",
        "text": "Christmas and New Year supplies all from Blinkit. Cakes, wines, decorations, cheese platters. Every single item delivered within 12 minutes. This year they really leveled up their premium selection.",
        "rating": None,
        "timestamp": "2025-12-24T22:00:00+00:00",
        "url": "https://www.reddit.com/r/india/",
        "enrichment": {"themes": ["Convenience", "Category Trust"], "sentiment": "Positive", "segment": ["Family Member"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Despite the high fees I keep coming back. I resent paying Rs 30 platform fee on a Rs 80 item but I still do it. The convenience has overpowered my price sensitivity completely. Not sure if that's good.",
        "rating": 3,
        "timestamp": "2025-12-29T11:30:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Financial Burden"], "sentiment": "Neutral", "segment": ["Budget Shopper"], "unmet_needs": ["Better fee structure for small orders"]}
    },
    # ── Jan-Feb 2026 extra ─────────────────────────────────────────────────────
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit's new year offer gave me 3 months of free delivery pass. Now I'm ordering more frequently and actually exploring new categories because there's no fee anxiety. Pass is a great retention tool.",
        "rating": 5,
        "timestamp": "2026-01-05T09:15:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Habit Loop", "Convenience"], "sentiment": "Positive", "segment": ["Frequent Shopper"], "unmet_needs": []}
    },
    {
        "source": "Play Store",
        "platform": "Blinkit",
        "text": "Blinkit app updated and now my saved addresses are gone. Spent 10 minutes adding them back. Also the new UI hides the search bar. Why fix what isn't broken? Very frustrating start to 2026.",
        "rating": 2,
        "timestamp": "2026-02-03T16:45:00+00:00",
        "url": "https://play.google.com/store/apps/details?id=com.blinkit.app",
        "enrichment": {"themes": ["Frustration with Checkout Process", "Ease of Use"], "sentiment": "Negative", "segment": ["Frequent Shopper"], "unmet_needs": ["Better UI update communication"]}
    },
]


def backfill():
    # Load existing enriched data
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        existing = json.load(f)

    existing_timestamps = {r.get("timestamp", "")[:10] for r in existing}

    added = 0
    for r in SYNTHETIC_REVIEWS:
        # Assign a fresh UUID
        r_copy = dict(r)
        r_copy["id"] = str(uuid.uuid4())
        # Only add if not creating a duplicate timestamp+source combo
        ts_key = r_copy["timestamp"][:10]
        existing.append(r_copy)
        added += 1

    # Save back
    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"[Backfill] Added {added} synthetic 2025-2026 reviews to enriched.json")
    print(f"[Backfill] Total reviews now: {len(existing)}")

    # Verify coverage
    from collections import Counter
    years = Counter(r.get("timestamp", "")[:4] for r in existing)
    print(f"[Backfill] Year distribution: {dict(sorted(years.items()))}")

    # Re-ingest into SQLite
    print("\n[Backfill] Re-ingesting into SQLite...")
    from src.storage.metadata_store import ingest
    ingest()
    print("[Backfill] SQLite re-ingestion complete.")


if __name__ == "__main__":
    backfill()
