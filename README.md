# microscale

Lossless JPEG post‑processing for scientific and technical imaging.

`microscale` is a small CLI toolchain built around **jpegtran**, **Pillow**, and **pyexiv2** to perform common image operations *without recompression*:

- descale / crop
- rotate
- append a scale bar (concatenation)
- preserve and repair metadata (EXIF / IPTC / XMP)
- rebuild broken EXIF thumbnails safely

It is designed for repeatable, batch‑safe processing of camera output in workflows where pixel integrity and metadata correctness matter.

---

## Why microscale exists

Most image tools either:

- recompress JPEGs (destroying data), or
- silently break metadata, or
- fail on slightly non‑standard files

`microscale` instead follows three rules:

1. **Lossless pixels** – all geometry changes use `jpegtran`
2. **Metadata survives** – EXIF/IPTC/XMP copied explicitly
3. **Broken thumbnails are rebuilt**, not propagated

If something is unsafe, it fails loudly.

---

## Features

- 📐 **Descale / crop** without recompression
- 🔄 **Rotate** using JPEG transforms
- 📏 **Add scale bar** by vertical concatenation
- 🧠 **Metadata‑aware** (EXIF / IPTC / XMP)
- 🧩 **Thumbnail repair** (fixes corrupted EXIF thumbnails)
- 🧪 **Test‑driven** core logic

---

## Installation

### System dependency

`jpegtran` must be available in PATH:

```bash
sudo apt install libjpeg-turbo-progs
```

(or equivalent for your OS)

### Python

```bash
mkdir ~/dev
cd ~/dev
git clone https://github.com/ffsedd/microscale.git
cd microscale
uv tool install -e .
```

---

## Usage

Basic example:

```bash
microscale --descale --rotate --scale *.jpg
```

Verbose output:

```bash
microscale --descale --rotate --scale *.jpg -v
```

Typical pipeline:

1. Input image is descaled
2. Rotation applied (lossless)
3. Scale image generated
4. Images concatenated with `jpegtran`
5. Metadata copied and thumbnail rebuilt

---

## Metadata handling (important)

- Metadata copying is done **explicitly** using `pyexiv2`
- Broken EXIF thumbnails from source files are **discarded**
- A **fresh thumbnail** is generated from the final image

This avoids common errors such as:

```
[warn] Directory Thumbnail, entry 0x0201: Data area exceeds data buffer
```

Which indicates corrupted thumbnail data in the source file.

---

## JPEG safety guarantees

`microscale` guarantees:

- no DCT recompression
- no color conversion
- no subsampling changes

Operations will fail if:

- JPEG sampling factors are incompatible
- dimensions are not block‑aligned



---

## Testing

Tests use real JPEG files generated via Pillow and validate:

- output dimensions
- failure on incompatible subsampling
- correct file creation

Run tests with:

```bash
pytest
```

---

## Limitations

- JPEG only
- requires `jpegtran`
- assumes sane EXIF blocks (repairs thumbnails, not arbitrary corruption)

---

## License

MIT (or project‑specific license — adjust as needed)

