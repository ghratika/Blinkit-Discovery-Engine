"""
Enrichment Prompts — src/enrichment/prompts.py

Contains the system and user prompts used for the Groq API
to extract themes, sentiment, segments, and unmet needs from reviews.
"""

ENRICHMENT_SYSTEM_PROMPT = "You are an expert UX researcher analyzing user reviews of quick-commerce apps. Expect and translate/handle Hinglish (Hindi written in English script) in the reviews organically."

ENRICHMENT_USER_PROMPT_TEMPLATE = """Analyze the following review and return a JSON object with these exact keys:
- "themes": list of 1-3 short theme labels (e.g., "Habit Loop", "Category Trust", "Stockout Frustration")
- "sentiment": one of "Positive", "Neutral", "Negative". If a review uses sarcasm (e.g., "Great job delivering expired milk!"), tag it as Negative. Assign sentiment specifically *relative to the target platform* (Blinkit) being analyzed.
- "segment": list of BEHAVIORAL user segments inferred from the review text. Segments MUST predict a specific purchase-category need or an exploration pattern. 
  BASELINE CATEGORIES TO USE IF APPLICABLE: "Frequent Shoppers", "Busy Professionals", "Foodies", "Grocery Shoppers (The Natural Explorers)", "Budget Shoppers", "Household Managers".
  DO NOT use categories like "Deal-Driven Buyer", "Weekend Stock-up Buyer", "New Parent", "Pet Owner", or "Bulk Grocery Buyer". DO NOT extract demographics, platform usage, or general identities.
  Only derive segments from these two structural types:
  1. Life-stage/Need-driven: The label implies a specific product category need.
  2. Habit/Purchase-pattern-driven: The label describes a recurring buying behavior.
  Return an empty list if no valid behavioral segment can be inferred.
- "unmet_needs": list of 0-2 explicit gaps or requests mentioned (empty list if none)

Review: "{review_text}"

Return ONLY valid JSON. No explanation.
"""

# Synthesis Prompts for Research Questions

SYNTHESIS_PROMPTS = {
    "q1_repeated_categories": """Based on the following aggregated themes related to 'Habit Loop', why do users repeatedly buy the same categories on our quick-commerce app? Summarize with evidence from the themes.
Themes: {themes}""",
    
    "q2_prevent_exploration": """Based on the following negative reviews and 'Category Discovery' themes, what prevents users from exploring new categories on the app?
Data: {data}""",
    
    "q3_discovery_methods": """Based on the 'Discovery Method' themes extracted from reviews, how do users currently discover new products?
Themes: {themes}""",
    
    "q4_habit_and_routine": """Based on 'Fixed Weekly List' and 'Routine' themes, what role do habit and routine play in shopping behavior?
Themes: {themes}""",
    
    "q5_trust_signals": """Based on 'Category Trust' and 'Quality Concern' themes, what information/trust signals do users need before trying an unfamiliar category?
Themes: {themes}""",
    
    "q6_frustrations": """What are the top recurring frustrations based on these highly frequent negative themes?
Themes: {themes}""",
    
    "q7_segments_exploration": """Based on the cross-reference of user segments with 'Exploration' themes, which user segments show a higher tendency for exploration?
Data: {data}""",
    
    "q8_unmet_needs": """Based on the following aggregated unmet needs from all reviews, what category gaps or unmet needs come up consistently?
Unmet Needs: {unmet_needs}"""
}
