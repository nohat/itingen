"""Unit tests for PDF day banner generation."""

from unittest.mock import Mock

from itingen.core.domain.events import Event
from itingen.rendering.timeline import TimelineDay


def test_day_banner_generator_cache_miss_generates_banner(tmp_path):
    from itingen.rendering.pdf.banners import DayBannerGenerator

    client = Mock()
    client.generate_image_with_imagen.return_value = b"fake-png-bytes"

    generator = DayBannerGenerator(client=client, cache_dir=tmp_path)

    day = TimelineDay(
        date_str="2025-12-31",
        day_header="2025-12-31 (Wednesday)",
        events=[
            Event(event_heading="Visit Sky Tower", location="Auckland"),
            Event(event_heading="Ferry to Waiheke", location="Waiheke Island"),
        ],
    )

    [enriched_day] = generator.generate([day])

    assert enriched_day.banner_image_path is not None
    assert enriched_day.banner_image_path.endswith(".png")

    banner_path = tmp_path / "banners" / enriched_day.banner_image_path.split("/")[-1]
    assert banner_path.exists()
    assert banner_path.stat().st_size > 0

    client.generate_image_with_imagen.assert_called_once()


def test_day_banner_generator_cache_hit_skips_generation(tmp_path):
    from itingen.rendering.pdf.banners import DayBannerGenerator

    client = Mock()
    client.generate_image_with_imagen.return_value = b"fake-png-bytes"

    generator = DayBannerGenerator(client=client, cache_dir=tmp_path)

    day1 = TimelineDay(
        date_str="2025-12-31",
        day_header="2025-12-31 (Wednesday)",
        events=[Event(event_heading="Visit Sky Tower", location="Auckland")],
    )

    [enriched1] = generator.generate([day1])
    assert enriched1.banner_image_path is not None

    client.generate_image_with_imagen.reset_mock()

    day2 = TimelineDay(
        date_str="2025-12-31",
        day_header="2025-12-31 (Wednesday)",
        events=[Event(event_heading="Visit Sky Tower", location="Auckland")],
    )

    [enriched2] = generator.generate([day2])

    assert enriched2.banner_image_path == enriched1.banner_image_path
    client.generate_image_with_imagen.assert_not_called()
