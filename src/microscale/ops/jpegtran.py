from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from PIL import Image

from ..config import SCALE_HEIGHT, TARGET_RATIO

logger = logging.getLogger(__name__)

JPEGTRAN_BIN = "jpegtran"
JPEG_BLOCK = 8  # jpegtran requires multiples of 8


class JpegtranError(Exception):
    """Raised when jpegtran fails."""


def run_jpegtran(args: list[str]) -> None:
    """Run jpegtran and raise a clean, informative error on failure."""
    try:
        subprocess.run([JPEGTRAN_BIN, *args], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() if e.stderr else "jpegtran failed with no stderr"
        raise JpegtranError(msg) from None


def _round_down_block(x: int, block: int = JPEG_BLOCK) -> int:
    """Round down x to nearest multiple of block (jpegtran requirement)."""
    return x - (x % block)


def _crop_geometry(w: int, h: int, target_ratio: float) -> str:
    """
    Compute jpegtran crop geometry for a wide image.

    Width is reduced to match target_ratio; height unchanged.
    Geometry is centered horizontally and block-aligned.
    """
    crop_w = _round_down_block(int(h * target_ratio))
    crop_h = _round_down_block(h)
    left = (w - crop_w) // 2
    return f"{crop_w}x{crop_h}+{left}+0"


def descale(fp: Path, fp_out: Path, scale_height: int = SCALE_HEIGHT) -> Path:
    """
    Lossless removal of scale bar from the bottom of a JPEG.
    """
    with Image.open(fp) as im:
        w, h = im.size

    new_h = h - scale_height
    if new_h <= 0:
        raise ValueError(f"{fp.name}: scale height ({scale_height}) exceeds image height ({h})")

    crop_h = _round_down_block(new_h)
    crop_str = f"{w}x{crop_h}+0+0"
    run_jpegtran(["-crop", crop_str, "-outfile", str(fp_out), str(fp)])
    logger.debug("%s: Descale done -> %s", fp.name, fp_out.name)
    return fp_out


def crop(fp: Path, fp_out: Path, target_ratio: float = TARGET_RATIO) -> Path:
    """
    Lossless crop to target aspect ratio by trimming left/right sides.
    """
    with Image.open(fp) as im:
        w, h = im.size

    current_ratio = w / h
    if current_ratio <= target_ratio:
        raise ValueError(
            f"{fp.name}: Cannot crop - image ratio {current_ratio:.3f} < target {target_ratio}"
        )

    crop_str = _crop_geometry(w, h, target_ratio)
    run_jpegtran(["-crop", crop_str, "-outfile", str(fp_out), str(fp)])
    logger.debug("%s: Crop done -> %s", fp.name, fp_out.name)
    return fp_out


def rotate(fp: Path) -> Path:
    """
    Lossless rotate a JPEG image 180° in place.
    """
    run_jpegtran(["-rotate", "180", "-outfile", str(fp), str(fp)])
    logger.debug("%s: Rotation done", fp.name)
    return fp
