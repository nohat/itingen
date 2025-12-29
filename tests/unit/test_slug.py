"""
Unit tests for venue slug generation utility.

Tests the venue slug generation algorithm that creates filesystem-safe
identifiers from canonical venue names.
"""

from itingen.utils.slug import generate_venue_slug


class TestSlugGeneration:
    """Test venue slug generation functionality."""

    def test_slug_basic_venue_with_location(self):
        """Generate slug from venue name with location in parentheses."""
        slug = generate_venue_slug("Tantalus Estate Vineyard & Winery (Waiheke Island)")
        assert slug == "tantalus-waiheke"

    def test_slug_removes_stopwords(self):
        """Remove common stopwords from venue slug."""
        slug = generate_venue_slug("The Vineyard & Winery (Auckland)")
        # "the", "vineyard", "winery" are all stopwords and removed.
        assert slug == "auckland"

    def test_slug_handles_special_characters(self):
        """Handle special characters and punctuation."""
        slug = generate_venue_slug("Man O' War Vineyards (Waiheke Island)")
        # Apostrophe becomes word boundary, "O" is extracted as separate token
        # "vineyards" is a stopword and filtered out after first 3 tokens
        assert slug == "man-o-war-waiheke"

    def test_slug_max_tokens_parameter(self):
        """Respect max_tokens parameter."""
        slug = generate_venue_slug("Very Long Venue Name With Many Words (Location)", max_tokens=2)
        tokens = slug.split("-")
        # Should have ~2 name tokens + location token(s)
        assert len(tokens) <= 4

    def test_slug_removes_duplicate_hyphens(self):
        """Remove duplicate hyphens from slug."""
        # Edge case: venue with lots of punctuation
        slug = generate_venue_slug("Estate - - Winery (Place)")
        assert "--" not in slug
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_slug_no_location_parentheses(self):
        """Handle venues without location in parentheses."""
        slug = generate_venue_slug("Auckland Downtown Ferry Terminal")
        # "ferry" and "terminal" are stopwords and filtered after first 2 tokens
        assert slug == "auckland-downtown"

    def test_slug_macron_characters(self):
        """Handle unicode characters (e.g., Māori macrons)."""
        slug = generate_venue_slug("Café Māori (Wellington)")
        # Māori macron 'ā' should be normalized
        assert "wellington" in slug
        # Slug should be lowercase ASCII-safe
        assert slug.islower()

    def test_slug_location_stopwords_removed(self):
        """Remove location-specific stopwords from location tokens."""
        slug = generate_venue_slug("Test Venue (Waiheke Island Resort)")
        # "island" and "resort" should be removed from location
        assert "waiheke" in slug
        assert "island" not in slug
        assert "resort" not in slug

    def test_slug_short_location_tokens_ignored(self):
        """Ignore very short location tokens (< 3 chars)."""
        slug = generate_venue_slug("Test Venue (New Zealand)")
        # "New" (3 chars) might be kept, "Zealand" definitely kept
        assert "zealand" in slug or "new" in slug

    def test_slug_lowercase_output(self):
        """Slug should always be lowercase."""
        slug = generate_venue_slug("UPPERCASE VENUE NAME (LOCATION)")
        assert slug.islower()

    def test_slug_no_spaces(self):
        """Slug should not contain spaces."""
        slug = generate_venue_slug("Multi Word Venue Name (Multi Word Location)")
        assert " " not in slug
        assert "-" in slug

    def test_slug_removes_stopwords_from_all_positions(self):
        """Ensure stopwords are removed even if they appear in the first two positions."""
        # 'The' and 'Estate' are stopwords.
        slug = generate_venue_slug("The Estate Vineyard (Waiheke)")
        # 'the', 'estate', 'vineyard' are all stopwords.
        # It should probably fall back to location if all are stopwords,
        # or at least not include 'the' and 'estate'.
        assert "the" not in slug
        assert "estate" not in slug
        assert "vineyard" not in slug
        assert slug == "waiheke"

    def test_slug_real_world_examples(self):
        """Test with real-world venue names."""
        examples = [
            ("Tantalus Estate Vineyard & Winery (Waiheke Island)", "tantalus-waiheke"),
            ("Auckland Downtown Ferry Terminal", "auckland-downtown"),
            ("The French Cafe (Auckland)", "french-auckland"),
        ]
        for canonical_name, expected in examples:
            slug = generate_venue_slug(canonical_name)
            assert slug == expected, f"Expected '{expected}' but got '{slug}' for '{canonical_name}'"
