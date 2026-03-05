from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

from ..config import PIX_PER_MM, SCALE_HEIGHT
from .concatenate import concatenate


def lens_label(fp_stem: str) -> str:
    """Generate a lens label from the file stem."""
    if fp_stem.count("_") < 3:
        raise ValueError(f"Unexpected filename format for lens label: {fp_stem}")
    parts = fp_stem.split("_")
    label = parts[3]
    if not re.match(r"\w\d{1,2}", label):
        raise ValueError(f"Unexpected filename format for lens label: {fp_stem}")
    return label.lower()


def add_scale(fp: Path, fp_out: Path) -> Path:
    """Add a black scale bar at the bottom of the image using SCALE_HEIGHT."""
    with Image.open(fp) as im:
        w, h = im.size

    assert SCALE_HEIGHT % 8 == 0, "SCALE_HEIGHT must be multiple of 8"

    # Create temporary scale image
    pix_per_mm = PIX_PER_MM[lens_label(fp.stem)]
    fp_scale = make_temp_scale((w, SCALE_HEIGHT), pix_per_mm, fp.stem)

    try:
        # Concatenate images
        fp_out = concatenate(fp, fp_scale, fp_out, metadata="none")
    finally:
        # Clean up temp scale image
        fp_scale.unlink(missing_ok=True)

    return fp_out

def load_narrow_font(size: int) -> ImageFont.FreeTypeFont:
    # try a narrow or code font installed on Linux
    candidates = [
        "Iosevka Term",
        "Iosevka",
        "Inconsolata-Regular.ttf",
        "LiberationMono-Regular.ttf",
        "NotoMono-Regular.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    # fallback
    return ImageFont.load_default()




def make_temp_scale(size: Tuple[int, int], pix_per_mm: float, label: str) -> Path:
    """Create a temporary scale image with black background, white line, and text."""
    wid, hei = size

    scale_length_px, sc_label = calculate_scale_length(wid, pix_per_mm)

    line_xpos = wid - 350
    text_xpos = wid - 300

    # Create black image
    img = Image.new("RGB", (wid, hei), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Define font
    font = load_narrow_font(size=40)

    # Draw scale line
    draw.line([(line_xpos, 23), (line_xpos - scale_length_px, 23)], fill=(255, 255, 255), width=6)
    # Draw file label
    draw.text((10, 4), label, font=font, fill=(255, 255, 255))
    # Draw scale label
    draw.text((text_xpos, 0), sc_label, font=font, fill=(255, 255, 255))

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        out_file = Path(tmp_file.name)
    img.save(out_file, "JPEG", quality=90, subsampling=1)

    return out_file


def calculate_scale_length(width_px: int, pix_per_mm: float) -> Tuple[int, str]:
    """
    Calculate scale bar length in pixels and label.

    Args:
        width_px: Width of the image in pixels
        pix_per_mm: Pixels per millimeter

    Returns:
        Tuple of (scale length in pixels, scale label string)
    """
    img_w_um = width_px / pix_per_mm * 1000  # Image width in µm
    scale_um = round(img_w_um / 6, -2)

    if scale_um > 750:
        scale_um = round(scale_um, -3)
        sc_label = f"{scale_um / 1000:.0f} mm"
    elif scale_um > 350:
        scale_um = 500
        sc_label = "500 µm"
    else:
        sc_label = f"{scale_um:.0f} µm"

    scale_length_px = int(scale_um / 1000 * pix_per_mm)  # in pixels
    return scale_length_px, sc_label
