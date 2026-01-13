"""Image post-processing utilities for full-bleed aesthetic.

Ported from scaffold POC. Provides:
- Auto-detect and crop borders/padding (max 22% trim)
- Resample to target aspect ratio using LANCZOS
- Format optimization (PNG preferred, JPEG fallback)
- Full-bleed aesthetic (no margins/borders)
"""

from typing import Union, Tuple, Optional
from PIL import Image, ImageStat
import io


def detect_and_crop_borders(
    img: Image.Image,
    max_trim_percent: float = 0.22,
    threshold: int = 240
) -> Image.Image:
    """Detect and crop uniform borders from an image.
    
    Args:
        img: PIL Image to process
        max_trim_percent: Maximum percentage of image to trim (0.22 = 22%)
        threshold: RGB threshold for border detection (240 = near-white)
    
    Returns:
        Cropped PIL Image
    """
    width, height = img.size
    pixels = img.load()
    
    def is_border_color(x: int, y: int) -> bool:
        """Check if pixel is a border color (near-white or near-gray)."""
        if img.mode == 'RGBA':
            r, g, b, a = pixels[x, y]
        else:
            r, g, b = pixels[x, y]
        return r >= threshold and g >= threshold and b >= threshold
    
    left = 0
    for x in range(width // 2):
        if not all(is_border_color(x, y) for y in range(0, height, max(1, height // 20))):
            left = x
            break
    
    right = width
    for x in range(width - 1, width // 2, -1):
        if not all(is_border_color(x, y) for y in range(0, height, max(1, height // 20))):
            right = x + 1
            break
    
    top = 0
    for y in range(height // 2):
        if not all(is_border_color(x, y) for x in range(0, width, max(1, width // 20))):
            top = y
            break
    
    bottom = height
    for y in range(height - 1, height // 2, -1):
        if not all(is_border_color(x, y) for x in range(0, width, max(1, width // 20))):
            bottom = y + 1
            break
    
    crop_width = right - left
    crop_height = bottom - top
    
    max_trim_pixels_w = int(width * max_trim_percent)
    max_trim_pixels_h = int(height * max_trim_percent)
    
    if (width - crop_width) > max_trim_pixels_w:
        excess = (width - crop_width) - max_trim_pixels_w
        left = max(0, left - excess // 2)
        right = min(width, right + excess // 2)
    
    if (height - crop_height) > max_trim_pixels_h:
        excess = (height - crop_height) - max_trim_pixels_h
        top = max(0, top - excess // 2)
        bottom = min(height, bottom + excess // 2)
    
    if left == 0 and right == width and top == 0 and bottom == height:
        return img
    
    return img.crop((left, top, right, bottom))


def resample_to_aspect_ratio(
    img: Image.Image,
    target_aspect: Tuple[int, int],
    resample_filter: Image.Resampling = Image.Resampling.LANCZOS
) -> Image.Image:
    """Resample image to target aspect ratio using high-quality LANCZOS.
    
    Args:
        img: PIL Image to resample
        target_aspect: Target aspect ratio as (width, height) tuple
        resample_filter: PIL resampling filter (default: LANCZOS)
    
    Returns:
        Resampled PIL Image
    """
    current_width, current_height = img.size
    target_width, target_height = target_aspect
    
    target_ratio = target_width / target_height
    current_ratio = current_width / current_height
    
    if abs(target_ratio - current_ratio) < 0.01:
        return img
    
    if current_ratio > target_ratio:
        new_width = int(current_height * target_ratio)
        new_height = current_height
        x_offset = (current_width - new_width) // 2
        y_offset = 0
    else:
        new_width = current_width
        new_height = int(current_width / target_ratio)
        x_offset = 0
        y_offset = (current_height - new_height) // 2
    
    cropped = img.crop((
        x_offset,
        y_offset,
        x_offset + new_width,
        y_offset + new_height
    ))
    
    return cropped


def optimize_image_format(
    img: Image.Image,
    prefer_png: bool = True,
    jpeg_quality: int = 85
) -> bytes:
    """Optimize image format (PNG or JPEG) and return bytes.
    
    Args:
        img: PIL Image to optimize
        prefer_png: Prefer PNG format (default: True)
        jpeg_quality: JPEG quality setting 0-100 (default: 85)
    
    Returns:
        Optimized image as bytes
    """
    output = io.BytesIO()
    
    if img.mode == 'RGBA' or prefer_png:
        if img.mode == 'RGBA':
            img.save(output, format='PNG', optimize=True)
        else:
            img_rgb = img.convert('RGB')
            img_rgb.save(output, format='PNG', optimize=True)
    else:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output, format='JPEG', quality=jpeg_quality, optimize=True)
    
    output.seek(0)
    return output.getvalue()


def postprocess_image(
    image_input: Union[Image.Image, bytes],
    target_aspect: Optional[Tuple[int, int]] = None,
    max_trim_percent: float = 0.22,
    prefer_png: bool = True,
    jpeg_quality: int = 85
) -> bytes:
    """Complete post-processing pipeline for full-bleed aesthetic.
    
    Applies:
    1. Border detection and cropping
    2. Aspect ratio resampling (if target_aspect provided)
    3. Format optimization
    
    Args:
        image_input: PIL Image or bytes
        target_aspect: Optional target aspect ratio (width, height)
        max_trim_percent: Maximum trim percentage (default: 0.22)
        prefer_png: Prefer PNG format (default: True)
        jpeg_quality: JPEG quality if not using PNG (default: 85)
    
    Returns:
        Optimized image as bytes
    """
    if isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    else:
        img = image_input
    
    img = detect_and_crop_borders(img, max_trim_percent=max_trim_percent)
    
    if target_aspect:
        img = resample_to_aspect_ratio(img, target_aspect=target_aspect)
    
    return optimize_image_format(img, prefer_png=prefer_png, jpeg_quality=jpeg_quality)
