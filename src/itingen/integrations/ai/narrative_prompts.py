"""Narrative prompt templates and utilities.

These templates are ported from the scaffold POC to provide richer, 
more engaging travel narratives.
"""

NARRATIVE_STYLE_TEMPLATE = (
    "You are an expert travel writer and local guide. Your tone is engaging, "
    "knowledgeable, and evocative. Use sensory details to make the scene come alive. "
    "Keep it concise (1-3 sentences)."
)

NARRATIVE_PROMPT_TEMPLATE = (
    "{style_guidance}\n\n"
    "Describe the following travel event in a friendly, engaging narrative tone:\n"
    "Event: {heading}\n"
    "Kind: {kind}\n"
    "Location: {location}\n"
    "Description: {description}\n"
    "Participants: {who}\n"
    "\n"
    "Focus on the experience and atmosphere. Avoid stating the obvious logistics."
)
