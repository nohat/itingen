"""
Unit tests for EXIF metadata utilities.

Tests cover reading and writing EXIF metadata to JPEG images,
including error handling for missing files and invalid images.
"""

import json
from pathlib import Path

from PIL import Image

from itingen.utils.exif import read_exif_metadata, write_exif_metadata


class TestReadExifMetadata:
    """Tests for reading EXIF metadata from JPEG images."""

    def test_read_exif_from_jpeg_with_metadata(self, tmp_path: Path) -> None:
        """Read EXIF metadata from JPEG with embedded metadata."""
        # Create a test JPEG with EXIF metadata
        img_path = tmp_path / "test_image.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        exif = img.getexif()

        # Embed test metadata in UserComment field (tag 37510)
        test_metadata = {
            "fingerprint": "abc123",
            "prompt": "test prompt",
            "model": "test-model"
        }
        metadata_str = "SCFTH:" + json.dumps(test_metadata, sort_keys=True)
        exif[37510] = metadata_str
        img.save(img_path, format="JPEG", exif=exif.tobytes())

        # Read the metadata
        result = read_exif_metadata(str(img_path))

        assert result is not None
        assert result["fingerprint"] == "abc123"
        assert result["prompt"] == "test prompt"
        assert result["model"] == "test-model"

    def test_read_exif_from_jpeg_without_metadata(self, tmp_path: Path) -> None:
        """Return None when JPEG has no EXIF metadata."""
        img_path = tmp_path / "no_metadata.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(img_path, format="JPEG")

        result = read_exif_metadata(str(img_path))

        assert result is None

    def test_read_exif_from_nonexistent_file(self) -> None:
        """Return None when file doesn't exist."""
        result = read_exif_metadata("/nonexistent/file.jpg")

        assert result is None

    def test_read_exif_from_empty_path(self) -> None:
        """Return None when path is empty string."""
        result = read_exif_metadata("")

        assert result is None

    def test_read_exif_fallback_to_image_description(self, tmp_path: Path) -> None:
        """Fallback to ImageDescription (tag 270) if UserComment is missing."""
        img_path = tmp_path / "fallback.jpg"
        img = Image.new("RGB", (100, 100), color="green")
        exif = img.getexif()

        # Only set ImageDescription, not UserComment
        test_metadata = {"key": "value"}
        metadata_str = "SCFTH:" + json.dumps(test_metadata, sort_keys=True)
        exif[270] = metadata_str
        img.save(img_path, format="JPEG", exif=exif.tobytes())

        result = read_exif_metadata(str(img_path))

        assert result is not None
        assert result["key"] == "value"

    def test_read_exif_handles_malformed_json(self, tmp_path: Path) -> None:
        """Return None when EXIF contains malformed JSON."""
        img_path = tmp_path / "malformed.jpg"
        img = Image.new("RGB", (100, 100), color="yellow")
        exif = img.getexif()

        # Set malformed JSON
        exif[37510] = "SCFTH:{not valid json"
        img.save(img_path, format="JPEG", exif=exif.tobytes())

        result = read_exif_metadata(str(img_path))

        assert result is None

    def test_read_exif_without_scfth_prefix(self, tmp_path: Path) -> None:
        """Return None when EXIF data doesn't have SCFTH: prefix."""
        img_path = tmp_path / "no_prefix.jpg"
        img = Image.new("RGB", (100, 100), color="purple")
        exif = img.getexif()

        # Set JSON without SCFTH: prefix
        exif[37510] = json.dumps({"key": "value"})
        img.save(img_path, format="JPEG", exif=exif.tobytes())

        result = read_exif_metadata(str(img_path))

        assert result is None

    def test_read_exif_handles_non_bytes_raw_data(self, tmp_path: Path) -> None:
        """Handle cases where exif.get() returns a non-bytes object that is not a string."""
        img_path = tmp_path / "non_bytes.jpg"
        img = Image.new("RGB", (10, 10))
        img.save(img_path, format="JPEG")
        
        # We need to mock the behavior where exif.get() returns something weird
        with Image.open(img_path) as im:
            exif = im.getexif()
            # Tag 37510 is UserComment
            exif[37510] = 12345 # Not bytes, not string
            
            import unittest.mock as mock
            with mock.patch("PIL.Image.open") as mock_open:
                mock_im = mock.MagicMock()
                mock_im.getexif.return_value = exif
                mock_open.return_value = mock_im
                
                result = read_exif_metadata(str(img_path))
                assert result is None

    def test_read_exif_exception_handling(self, tmp_path: Path) -> None:
        """Return None if an unexpected exception occurs during reading."""
        img_path = tmp_path / "exception.jpg"
        img = Image.new("RGB", (10, 10))
        img.save(img_path, format="JPEG")
        
        import unittest.mock as mock
        with mock.patch("PIL.Image.open", side_effect=RuntimeError("Unexpected error")):
            result = read_exif_metadata(str(img_path))
            assert result is None

    def test_write_exif_exception_handling(self, tmp_path: Path) -> None:
        """Return False if an unexpected exception occurs during writing."""
        img_path = tmp_path / "write_exception.jpg"
        img = Image.new("RGB", (10, 10))
        img.save(img_path, format="JPEG")
        
        import unittest.mock as mock
        with mock.patch("PIL.Image.open", side_effect=RuntimeError("Unexpected error")):
            result = write_exif_metadata(img_path=str(img_path), meta={"test": "data"})
            assert result is False

    def test_write_exif_no_exif_object(self, tmp_path: Path) -> None:
        """Return False if image has no EXIF object (though PIL usually provides one)."""
        img_path = tmp_path / "no_exif_obj.jpg"
        img = Image.new("RGB", (10, 10))
        img.save(img_path, format="JPEG")
        
        import unittest.mock as mock
        with mock.patch("PIL.Image.open") as mock_open:
            mock_im = mock.MagicMock()
            mock_im.getexif.return_value = None
            mock_open.return_value = mock_im
            
            result = write_exif_metadata(img_path=str(img_path), meta={"test": "data"})
            assert result is False


class TestWriteExifMetadata:
    """Tests for writing EXIF metadata to JPEG images."""

    def test_write_exif_to_jpeg(self, tmp_path: Path) -> None:
        """Write EXIF metadata to JPEG and verify it can be read back."""
        img_path = tmp_path / "write_test.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img_path, format="JPEG")

        metadata = {
            "fingerprint_sha256": "abc123",
            "prompt_preview": "test prompt",
            "event_model": "test-model",
            "aspect_ratio": "16:9"
        }

        result = write_exif_metadata(img_path=str(img_path), meta=metadata)

        assert result is True

        # Verify we can read it back
        read_back = read_exif_metadata(str(img_path))
        assert read_back is not None
        assert read_back["fingerprint_sha256"] == "abc123"
        assert read_back["event_model"] == "test-model"

    def test_write_exif_creates_human_readable_description(self, tmp_path: Path) -> None:
        """Write creates human-readable ImageDescription field."""
        img_path = tmp_path / "description_test.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(img_path, format="JPEG")

        metadata = {
            "fingerprint_sha256": "abc123",
            "event_model": "gemini-1.5-flash",
            "aspect_ratio": "16:9",
            "prompt_preview": "A beautiful sunset"
        }

        write_exif_metadata(img_path=str(img_path), meta=metadata)

        # Read raw EXIF to check ImageDescription
        img = Image.open(img_path)
        exif = img.getexif()
        description = exif.get(270)

        assert description is not None
        assert "gemini-1.5-flash" in str(description)
        assert "16:9" in str(description)
        assert "abc123" in str(description)

    def test_write_exif_to_nonexistent_file(self) -> None:
        """Return False when file doesn't exist."""
        result = write_exif_metadata(
            img_path="/nonexistent/file.jpg",
            meta={"key": "value"}
        )

        assert result is False

    def test_write_exif_with_empty_path(self) -> None:
        """Return False when path is empty string."""
        result = write_exif_metadata(img_path="", meta={"key": "value"})

        assert result is False

    def test_write_exif_preserves_image_quality(self, tmp_path: Path) -> None:
        """Writing EXIF doesn't significantly degrade image quality."""
        img_path = tmp_path / "quality_test.jpg"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(img_path, format="JPEG", quality=95)

        original_size = img_path.stat().st_size

        metadata = {"key": "value"}
        write_exif_metadata(img_path=str(img_path), meta=metadata)

        new_size = img_path.stat().st_size

        # Size should be similar (allow 50% variance for small images with EXIF overhead)
        assert abs(new_size - original_size) / original_size < 0.5

    def test_write_exif_roundtrip_stability(self, tmp_path: Path) -> None:
        """Metadata written can be read back identically."""
        img_path = tmp_path / "roundtrip.jpg"
        img = Image.new("RGB", (100, 100), color="yellow")
        img.save(img_path, format="JPEG")

        original_metadata = {
            "fingerprint_sha256": "test123",
            "prompt_preview": "test prompt",
            "event_model": "test-model",
            "aspect_ratio": "16:9",
            "use_gemini_image": True,
            "ref_hashes": ["hash1", "hash2"]
        }

        write_exif_metadata(img_path=str(img_path), meta=original_metadata)
        read_metadata = read_exif_metadata(str(img_path))

        assert read_metadata is not None
        # All written fields should be readable
        for key, value in original_metadata.items():
            assert read_metadata.get(key) == value

    def test_write_exif_custom_title(self, tmp_path: Path) -> None:
        """Write EXIF metadata with a custom title and verify it's in ImageDescription."""
        img_path = tmp_path / "custom_title.jpg"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(img_path, format="JPEG")

        metadata = {"fingerprint_sha256": "xyz789"}
        custom_title = "Custom Trip Title"
        write_exif_metadata(img_path=str(img_path), meta=metadata, title=custom_title)

        img = Image.open(img_path)
        exif = img.getexif()
        description = str(exif.get(270) or "")
        assert description.startswith(custom_title)

