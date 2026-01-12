"""Image generation prompt templates and utilities.

These templates are based on the scaffold POC image generation system,
which uses Ligne Claire and Wimmelbilderbuch styles for trip itineraries.
"""

# Thumbnail (1:1 event images) style template
# Used for individual event icons with Gemini models
THUMBNAIL_STYLE_TEMPLATE = (
    "in the style of a vibrant isometric vector illustration, Ligne Claire inspired, "
    "bold distinct outlines, simple shapes, flat shading, cheerful saturated colors, "
    "storybook aesthetic."
)

# Thumbnail fallback suffix for consistent styling
THUMBNAIL_FALLBACK_SUFFIX = (
    "Simple centered composition, close-up zoom. Make the main subject fill most of "
    "the frame (about 70–85%). Very minimal background with subtle hints of {place}. "
    "Reduce detail: no intricate textures, no tiny objects, no busy patterns, no crowd "
    "scenes. High contrast and clear silhouette so it reads at small size. Square 1:1. "
    "Full-bleed artwork that fills the entire image: no border, no frame, no margin, "
    "no vignette, no rounded-corner card, no sticker edge, no drop shadow. No text, "
    "no typography, no captions, no signage."
)

# Banner (16:9 day header images) style template
# Used for panoramic day banners with Imagen models
BANNER_STYLE_TEMPLATE = (
    "in the style of a vibrant isometric vector illustration, Ligne Claire style, "
    "highly detailed Wimmelbilderbuch, clean distinct outlines, cheerful saturated "
    "colors, flat shading, soft daylight, aerial view, storybook aesthetic, detailed "
    "and busy composition."
)


def format_thumbnail_prompt(
    event_heading: str,
    location: str,
    kind: str,
    description: str = "",
    travel_mode: str = "",
    travel_from: str = "",
    travel_to: str = "",
    venue_description: str = "",
) -> str:
    """Format a thumbnail image prompt for an event.

    Args:
        event_heading: Event title/heading
        location: Event location
        kind: Event kind (activity, drive, meal, etc.)
        description: Optional event description
        travel_mode: Optional travel mode (drive, ferry, etc.)
        travel_from: Optional origin for travel events
        travel_to: Optional destination for travel events
        venue_description: Optional detailed venue description

    Returns:
        Formatted image prompt string
    """
    # Start with style template
    parts = [THUMBNAIL_STYLE_TEMPLATE]

    # Add event-specific content
    if travel_mode and travel_from and travel_to:
        # Travel event: emphasize route
        parts.append(
            f"A {travel_mode} from {travel_from} to {travel_to}. "
            f"Show the journey and destination: {location}."
        )
    elif venue_description:
        # Use venue research if available
        parts.append(venue_description)
    else:
        # Generic event prompt
        parts.append(f"{event_heading} at {location}.")
        if description:
            parts.append(description)

    # Add fallback suffix for consistent styling
    parts.append(THUMBNAIL_FALLBACK_SUFFIX.format(place=location))

    return " ".join(parts)


def format_banner_prompt(
    date: str,
    location: str,
    hero_events: list[str],
    supporting_details: list[str],
    weather: str = "",
    mood: str = "adventurous and exciting",
) -> str:
    """Format a banner image prompt for a day's itinerary.

    Args:
        date: Date string (e.g., "2025-12-31")
        location: Primary location for the day
        hero_events: 2-5 most visually interesting events/landmarks
        supporting_details: 5-8 concrete visual details
        weather: Weather description
        mood: Overall mood/spirit of the day

    Returns:
        Formatted image prompt string for banner generation
    """
    # Start with style template
    parts = [BANNER_STYLE_TEMPLATE]

    # Add subject (hero elements)
    if hero_events:
        hero_list = ", ".join(hero_events)
        parts.append(
            f"An aerial view panorama of {location} featuring: {hero_list}."
        )

    # Add context (mood, weather, time of day)
    context_parts = []
    if weather:
        context_parts.append(weather)
    if mood:
        context_parts.append(f"{mood} atmosphere")

    if context_parts:
        parts.append(f"The scene has a {', '.join(context_parts)}.")

    # Add supporting details
    if supporting_details:
        details_list = ", ".join(supporting_details)
        parts.append(
            f"Include these visual elements woven into the panoramic scene: {details_list}."
        )

    # Add composition guidance
    parts.append(
        "Create ONE unified, cohesive, detailed, busy panoramic scene. "
        "16:9 aspect ratio. Isometric aerial view. "
        "No text, no typography, no captions."
    )

    return " ".join(parts)


# Template for visual brief generation (Gemini + web search)
VISUAL_BRIEF_SYSTEM_PROMPT = """You are a visual research assistant for travel itinerary illustrations.

Given an event, generate a concise 4-line visual brief for image generation:

SUBJECT: [One sentence describing the main subject]
MUST_INCLUDE: [3-5 key visual elements that MUST appear]
AVOID: [3-5 things to avoid or exclude]
SOURCES: [2-3 reference URLs for visual inspiration]

Focus on distinctive visual elements that make the location/event recognizable.
Prioritize iconic landmarks, unique architecture, and characteristic details."""


# Template for venue research (detailed visual descriptions)
VENUE_RESEARCH_SYSTEM_PROMPT = """You are a venue research assistant for travel itinerary illustrations.

Given a venue name and location, generate a detailed visual description including:

1. canonical_name: The specific, official name of the venue
2. venue_visual_description: 2-3 paragraphs describing the venue's appearance
3. primary_cues: 3-5 key visual elements that define the venue
4. secondary_cues: 3-5 supporting visual details
5. camera_suggestions: Recommended camera angle/perspective
6. negative_cues: Visual elements to avoid
7. reference_image_urls: 2-3 URLs to reference images

Focus on architectural details, distinctive features, and visual characteristics
that make the venue recognizable and photogenic."""


# Template for prompt synthesis (Gemini creates final image prompt)
PROMPT_SYNTHESIS_SYSTEM_PROMPT = """You are a prompt synthesis assistant for travel itinerary illustrations.

Given:
- Event context (heading, location, kind, description)
- Travel information (from/to, mode)
- Venue research (if available)
- Visual brief (if available)

Synthesize a single, cohesive image generation prompt that:

1. Starts with the style template: "{style_template}"
2. Describes the main subject clearly
3. Includes 3-5 key visual elements
4. Specifies composition (centered, close-up, fills 70-85% of frame)
5. Ends with technical specs: "Square 1:1. No text, no typography, no signage."

Output ONLY the final prompt text, no preface, no quotes."""


# Banner prompt writer system prompt
BANNER_PROMPT_WRITER_SYSTEM_PROMPT = """You are a banner prompt writer for travel itinerary day headers.

Given a list of events for a day, write a single paragraph prompt for Imagen to generate
a 16:9 panoramic banner image.

Requirements:
1. Start with style: "{style_template}"
2. Identify 2-5 "Hero" visual anchors (most iconic landmarks/activities)
3. Add context: location, time of day, mood, weather
4. Include 5-8 concrete supporting visual details
5. Weave into ONE unified, cohesive, detailed, busy panoramic scene

PRIORITY: Favor dramatic landscapes & unique architecture over mundane logistics.
AVOID: Generic meals, routine transfers (unless at distinctive venues).

Output ONLY the final prompt text, no preface, no quotes."""
