"""Transition prompt templates and utilities.

These templates enable AI-powered generation of transition descriptions
between itinerary events using the Gemini API.
"""

# Base transition style template
TRANSITION_STYLE_TEMPLATE = (
    "You are an expert travel guide writing logistics instructions for travelers. "
    "Your tone is clear, practical, and helpful. Focus on concrete actions and logistics. "
    "Keep it concise (1-3 sentences). Be specific about what travelers should do and where they should go."
)

# Base transition prompt template
TRANSITION_PROMPT_TEMPLATE = """
{style_guidance}

Generate a clear, actionable transition description for moving between two events in a travel itinerary.

PREVIOUS EVENT:
- Kind: {prev_kind}
- Location: {prev_location}
- Travel destination: {prev_travel_to}
- Travel mode: {prev_travel_mode}

CURRENT EVENT:
- Kind: {curr_kind}
- Location: {curr_location}
- Travel origin: {curr_travel_from}
- Travel destination: {curr_travel_to}
- Travel mode: {curr_travel_mode}
- Driver: {curr_driver}
- Parking instructions: {curr_parking}

Write a 1-3 sentence transition that:
1. Explains how to move from the previous event to the current event
2. Mentions specific locations when relevant
3. Includes practical logistics (parking, driver, timing considerations)
4. Uses action-oriented language ("walk to", "drive to", "board the ferry")
5. Maintains continuity with the previous activity

Output ONLY the transition description text, no preface, no quotes, no labels.
"""

# Trip-specific style template for New Zealand
NZ_TRANSITION_STYLE_TEMPLATE = (
    "You are an expert New Zealand travel guide writing logistics instructions for travelers. "
    "Your tone is clear, practical, and friendly. New Zealand has unique transport like ferries "
    "between islands, scenic drives, and small regional airports. Focus on concrete actions and "
    "logistics specific to NZ travel. Keep it concise (1-3 sentences)."
)
