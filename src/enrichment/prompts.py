"""
Enrichment Prompts — src/enrichment/prompts.py

Contains the system and user prompts used for the Groq API
to extract themes, sentiment, segments, and unmet needs from reviews.
"""

ENRICHMENT_SYSTEM_PROMPT = "You are an expert UX researcher analyzing user reviews of quick-commerce apps. Expect and translate/handle Hinglish (Hindi written in English script) in the reviews organically."

ENRICHMENT_USER_PROMPT_TEMPLATE = """Analyze the following review and return a JSON object with these exact keys:
- "themes": list of 1-3 short theme labels (e.g., "Habit Loop", "Category Trust", "Stockout Frustration")
- "sentiment": one of "Positive", "Neutral", "Negative". If a review uses sarcasm (e.g., "Great job delivering expired milk!"), tag it as Negative. Assign sentiment specifically *relative to the target platform* (Blinkit) being analyzed.
- "segment": list of user segments inferred FREELY from the review text itself (e.g., "Pet Owner", "New Parent", "Health-Conscious", "Budget Shopper"). Do NOT use a fixed list — derive segment labels organically based on what the reviewer says about themselves or their household context. Return an empty list if no segment can be inferred.
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
