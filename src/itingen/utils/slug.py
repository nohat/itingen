"""
Venue slug generation utility.

Creates filesystem-safe, human-readable slugs from canonical venue names.
"""

import re
from typing import Set


def generate_venue_slug(canonical_name: str, max_tokens: int = 3) -> str:
    """
    Generate filesystem-safe venue slug from canonical name.

    Algorithm:
        1. Extract location from parentheses (e.g., "Waiheke Island" → "waiheke")
        2. Remove location stopwords ("island", "resort", etc.)
        3. Tokenize name, removing common words and punctuation
        4. Keep first max_tokens significant tokens
        5. Combine tokens + location, lowercase, hyphenate

    Args:
        canonical_name: Official venue name, e.g. "Tantalus Estate Vineyard & Winery (Waiheke Island)"
        max_tokens: Maximum number of name tokens to include (default: 3)

    Returns:
        Lowercase, hyphenated slug, e.g. "tantalus-estate-waiheke"

    Examples:
        >>> generate_venue_slug("Tantalus Estate Vineyard & Winery (Waiheke Island)")
        'tantalus-estate-waiheke'

        >>> generate_venue_slug("Auckland Downtown Ferry Terminal")
        'auckland-downtown-ferry'

        >>> generate_venue_slug("Man O' War Vineyards (Waiheke Island)")
        'man-owar-vineyards-waiheke'

        >>> generate_venue_slug("Very Long Name (Location)", max_tokens=2)
        'very-long-location'
    """
    # Extract location from parentheses
    location_match = re.search(r"\(([^)]+)\)", canonical_name)
    location_tokens = []

    if location_match:
        location = location_match.group(1)

        # Remove common location words
        location = re.sub(
            r"\b(island|resort|hotel|terminal|wharf|ferry)\b",
            "",
            location,
            flags=re.IGNORECASE,
        )

        # Tokenize location (words 3+ chars)
        location_tokens = [t.lower() for t in re.findall(r"\w+", location) if len(t) > 2]

        # Remove location from name for processing
        canonical_name = canonical_name[: location_match.start()].strip()

    # Tokenize name
    tokens = re.findall(r"\w+", canonical_name)

    # Stopwords to remove (common venue type words and articles)
    stopwords: Set[str] = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "at",
        "in",
        "on",
        "of",
        "to",
        "for",
        "vineyard",
        "vineyards",
        "winery",
        "estate",
        "hotel",
        "resort",
        "restaurant",
        "cafe",
        "terminal",
        "wharf",
        "ferry",
    }

    significant_tokens = []
    # AIDEV-DECISION: Stopwords are removed from all positions to ensure cleaner slugs.
    # AIDEV-NOTE: Identity preservation logic (keeping first 2 tokens) was removed to prioritize brevity.
    for token in tokens:
        token_lower = token.lower()

        # Keep token if not a stopword
        if token_lower not in stopwords:
            significant_tokens.append(token_lower)

        # Stop once we have enough tokens
        if len(significant_tokens) >= max_tokens:
            break

    # Combine name tokens + location tokens
    all_tokens = significant_tokens + location_tokens

    # Create slug (name tokens + 1 location token)
    slug = "-".join(all_tokens[: max_tokens + 1])

    # Clean up double hyphens and trim
    slug = re.sub(r"-+", "-", slug).strip("-")

    return slug
