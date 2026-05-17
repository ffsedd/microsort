from __future__ import annotations

import argparse
import logging
import os
from multiprocessing import Pool
from pathlib import Path
from send2trash import send2trash

from .model import Ops
from .pipeline import process_image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="microscale")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--noiptc", action="store_true")
    p.add_argument("--crop", action="store_true")
    p.add_argument("--rotate", action="store_true")
    p.add_argument("--scale", action="store_true")
    p.add_argument("--descale", action="store_true")
    p.add_argument("-j", "--jobs", type=int, default=os.cpu_count())  # default to CPU cores
    p.add_argument("-v", "--verbose", action="count", default=0)
    p.add_argument("-t", "--trash", action="store_true", help="Move original files to trash after successful processing")
    return p.parse_args()


def process_and_trash(fp_ops: tuple[Path, Ops], trash: bool) -> None:
    fp, ops = fp_ops
    process_image(fp, ops)
    logging.info(f"{fp.name} {ops}")
    if trash:
        send2trash(fp)
        logging.info(f"Moved original {fp} to trash")


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.WARNING - 10 * args.verbose,
        format="%(levelname)s %(message)s",
    )

    ops = Ops(
        noiptc=args.noiptc,
        descale=args.descale,
        crop=args.crop,
        rotate=args.rotate,
        scale=args.scale,
    )

    if args.descale and args.crop:
        raise ValueError("Cannot use both --descale and --crop")

    jobs = [(fp, ops) for fp in args.files]

    if args.jobs > 1:
        with Pool(args.jobs) as pool:
            # pass `trash` flag via starmap
            pool.starmap(process_and_trash, [(job, args.trash) for job in jobs])
    else:
        for job in jobs:
            process_and_trash(job, args.trash)
