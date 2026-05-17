from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from PIL import Image

from .jpegtran import run_jpegtran

MetadataOption = Literal["all", "exif", "iptc", "none"]


def enlarge_with_jpegtran(
    path: Path,
    size: tuple[int, int],
    new_size: tuple[int, int],
    metadata: MetadataOption = "all",
) -> Path:
    """Enlarge the image to new_size using jpegtran, top-left aligned."""
    w, h = size
    w2, h2 = new_size

    if (w, h) == (w2, h2):
        logging.debug("No enlargement needed.")
        return path

    cmd = [
        "-copy",
        metadata,
        "-perfect",
        "-crop",
        f"{w2}x{h2}+0+0",
        "-outfile",
        str(path),
        str(path),
    ]

    run_jpegtran(cmd)

    with Image.open(path) as im:
        logging.debug("Enlarged image size: %s", im.size)

    return path


def concatenate(
    fp: Path,
    fp2: Path,
    fp_out: Path,
    metadata: MetadataOption = "all",
) -> Path:
    """Concatenate two JPEG images vertically using jpegtran."""

    logging.debug(
        "Concatenating images: %s + %s (metadata=%s)",
        fp.name,
        fp2.name,
        metadata,
    )

    with Image.open(fp) as im1, Image.open(fp2) as im2:
        w, h = im1.size
        w2, h2 = im2.size

    if w != w2:
        raise ValueError(f"Image widths do not match: {w} vs {w2}")

    final_height = h + h2

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_path = Path(tmp_file.name)

    try:
        shutil.copy2(fp, tmp_path)

        enlarge_with_jpegtran(
            tmp_path,
            (w, h),
            (w, final_height),
            metadata=metadata,
        )

        drop_geo = f"+0+{h}"
        cmd_drop = [
            "-copy",
            metadata,
            "-perfect",
            "-drop",
            drop_geo,
            str(fp2),
            "-outfile",
            str(tmp_path),
            str(tmp_path),
        ]

        run_jpegtran(cmd_drop)

        shutil.copy2(tmp_path, fp_out)

    finally:
        tmp_path.unlink(missing_ok=True)

    logging.debug("Concatenation done: %s", fp_out.name)
    return fp_out
