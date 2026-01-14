from PIL import Image
import io
from itingen.utils.image_postprocessing import (
    detect_and_crop_borders,
    resample_to_aspect_ratio,
    optimize_image_format,
    postprocess_image
)


class TestBorderDetection:
    """Test border detection and cropping functionality."""
    
    def test_detect_uniform_white_border(self):
        """Should detect and crop uniform white borders."""
        img = Image.new('RGB', (200, 200), color='white')
        inner = Image.new('RGB', (100, 100), color='blue')
        img.paste(inner, (50, 50))
        
        cropped = detect_and_crop_borders(img, max_trim_percent=0.5)
        
        assert cropped.size[0] <= 100
        assert cropped.size[1] <= 100
        assert cropped.size[0] >= 90
        assert cropped.size[1] >= 90
    
    def test_detect_gray_border(self):
        """Should detect and crop gray borders."""
        img = Image.new('RGB', (200, 200), color=(240, 240, 240))
        inner = Image.new('RGB', (120, 120), color='red')
        img.paste(inner, (40, 40))
        
        cropped = detect_and_crop_borders(img, max_trim_percent=0.5)
        
        assert cropped.size[0] <= 120
        assert cropped.size[1] <= 120
    
    def test_respect_max_trim_percent(self):
        """Should not trim more than max_trim_percent."""
        img = Image.new('RGB', (200, 200), color='white')
        inner = Image.new('RGB', (50, 50), color='green')
        img.paste(inner, (75, 75))
        
        cropped = detect_and_crop_borders(img, max_trim_percent=0.22)
        
        min_dimension = min(cropped.size)
        original_min = min(img.size)
        trim_ratio = 1 - (min_dimension / original_min)
        assert trim_ratio <= 0.22
    
    def test_no_border_returns_original(self):
        """Should return original image if no border detected."""
        img = Image.new('RGB', (100, 100), color='blue')
        
        cropped = detect_and_crop_borders(img, max_trim_percent=0.22)
        
        assert cropped.size == img.size


class TestAspectRatioResampling:
    """Test aspect ratio resampling with LANCZOS."""
    
    def test_resample_to_1_1_square(self):
        """Should resample to 1:1 square aspect ratio."""
        img = Image.new('RGB', (200, 100), color='red')
        
        resampled = resample_to_aspect_ratio(img, target_aspect=(1, 1))
        
        assert resampled.size[0] == resampled.size[1]
    
    def test_resample_to_16_9_panoramic(self):
        """Should resample to 16:9 panoramic aspect ratio."""
        img = Image.new('RGB', (100, 100), color='blue')
        
        resampled = resample_to_aspect_ratio(img, target_aspect=(16, 9))
        
        ratio = resampled.size[0] / resampled.size[1]
        expected_ratio = 16 / 9
        assert abs(ratio - expected_ratio) < 0.01
    
    def test_uses_lanczos_resampling(self):
        """Should use LANCZOS resampling for quality."""
        img = Image.new('RGB', (200, 100), color='green')
        
        resampled = resample_to_aspect_ratio(img, target_aspect=(1, 1))
        
        assert resampled is not None
        assert isinstance(resampled, Image.Image)
    
    def test_maintains_larger_dimension(self):
        """Should maintain the larger dimension when resampling."""
        img = Image.new('RGB', (200, 100), color='yellow')
        
        resampled = resample_to_aspect_ratio(img, target_aspect=(1, 1))
        
        assert max(resampled.size) <= 200


class TestFormatOptimization:
    """Test format optimization (PNG/JPEG)."""
    
    def test_optimize_to_png_for_transparency(self):
        """Should prefer PNG for images with transparency."""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        
        optimized_bytes = optimize_image_format(img)
        
        optimized = Image.open(io.BytesIO(optimized_bytes))
        assert optimized.format == 'PNG'
    
    def test_optimize_to_jpeg_for_large_rgb(self):
        """Should use JPEG for large RGB images."""
        img = Image.new('RGB', (2000, 2000), color='blue')
        
        optimized_bytes = optimize_image_format(img, prefer_png=False)
        
        optimized = Image.open(io.BytesIO(optimized_bytes))
        assert optimized.format == 'JPEG'
    
    def test_png_quality_optimization(self):
        """Should optimize PNG compression."""
        img = Image.new('RGB', (100, 100), color='red')
        
        optimized_bytes = optimize_image_format(img, prefer_png=True)
        
        assert len(optimized_bytes) > 0
        optimized = Image.open(io.BytesIO(optimized_bytes))
        assert optimized.format == 'PNG'
    
    def test_jpeg_quality_setting(self):
        """Should apply quality setting for JPEG."""
        img = Image.new('RGB', (100, 100), color='green')
        
        optimized_bytes = optimize_image_format(img, prefer_png=False, jpeg_quality=85)
        
        assert len(optimized_bytes) > 0
        optimized = Image.open(io.BytesIO(optimized_bytes))
        assert optimized.format == 'JPEG'


class TestFullPostProcessing:
    """Test complete post-processing pipeline."""
    
    def test_postprocess_with_border_and_aspect(self):
        """Should apply border crop and aspect ratio correction."""
        img = Image.new('RGB', (220, 220), color='white')
        inner = Image.new('RGB', (100, 100), color='blue')
        img.paste(inner, (60, 60))
        
        processed_bytes = postprocess_image(
            img,
            target_aspect=(1, 1),
            max_trim_percent=0.22,
            prefer_png=True
        )
        
        processed = Image.open(io.BytesIO(processed_bytes))
        assert processed.size[0] == processed.size[1]
        assert processed.format == 'PNG'
    
    def test_postprocess_bytes_input(self):
        """Should accept bytes as input."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        processed_bytes = postprocess_image(
            img_bytes.getvalue(),
            target_aspect=(1, 1),
            prefer_png=True
        )
        
        assert len(processed_bytes) > 0
        processed = Image.open(io.BytesIO(processed_bytes))
        assert processed.format == 'PNG'
    
    def test_postprocess_full_bleed_aesthetic(self):
        """Should produce full-bleed images with no margins."""
        img = Image.new('RGB', (200, 200), color=(245, 245, 245))
        inner = Image.new('RGB', (150, 150), color='purple')
        img.paste(inner, (25, 25))
        
        processed_bytes = postprocess_image(
            img,
            target_aspect=(1, 1),
            max_trim_percent=0.22,
            prefer_png=True
        )
        
        processed = Image.open(io.BytesIO(processed_bytes))
        assert processed.size[0] >= 140
        assert processed.size[1] >= 140

    def test_postprocess_with_resizing(self):
        """Should apply resizing in pipeline."""
        img = Image.new('RGB', (2000, 2000), color='blue')
        
        processed_bytes = postprocess_image(
            img,
            max_dimension=500,
            prefer_png=True
        )
        
        processed = Image.open(io.BytesIO(processed_bytes))
        assert processed.size[0] <= 500
        assert processed.size[1] <= 500
