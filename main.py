#!/usr/bin/env python3
"""Publish the finished front page for the make.fun news-image-20261125 entry.

The artwork itself (entry.png) was drawn by the builder program kept in
build/compose.py and ships next to this file.  This runner has exactly one
job: prove the bundled image is the exact file the entry was built from,
then place an identical copy where the harness expects it.

It is deliberately boring: standard library only, no network, no clock and
no randomness, so the same input always yields the same output.  That is
also what the harness requires — a program that runs twice must write the
same bytes both times.

Before publishing, the runner also checks that the bytes really are a PNG
of the size the competition allows (at most 1024 by 1024 pixels, at most
1 MiB), by reading the PNG signature and the IHDR chunk with the standard
library alone.  After writing, it reads the published file back and
compares its hash with the expected one, so a failed or partial write can
never pass silently.  `python3 main.py --check` performs every check
without writing anything.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path

# SHA-256 of the front-page image this entry was built from.  If the image
# on disk does not hash to this value, something changed it and we refuse
# to publish it rather than silently shipping the wrong picture.
EXPECTED_DIGEST = (
    "65e13dbdbf417b181bb0be83764256a00eeab857463080ec1397cc0f58c6c10d"
)

IMAGE_NAME = "entry.png"

# Where the copy lands when MAKEFUN_OUTPUT_DIR is not set.
FALLBACK_OUTPUT_DIR = "/output"

# Competition limits for the image file.
MAX_BYTES = 1048576
MAX_WIDTH = 1024
MAX_HEIGHT = 1024

# The eight-byte signature every PNG file starts with.
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def folder_of_this_file() -> Path:
    """Directory holding this script (and, by convention, entry.png)."""
    return Path(__file__).resolve().parent


def digest_of(path: Path) -> str:
    """SHA-256 hex digest of a file, read in modest chunks."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def read_verified_image() -> bytes:
    """Return the bytes of entry.png, but only if its hash matches.

    Raises:
        FileNotFoundError: no entry.png sits next to this script.
        ValueError: the image exists but is not the expected one.
    """
    image_path = folder_of_this_file() / IMAGE_NAME
    if not image_path.is_file():
        raise FileNotFoundError(
            f"expected image not found: {image_path} "
            f"(run build/compose.py first so entry.png sits next to main.py)"
        )
    actual = digest_of(image_path)
    if actual != EXPECTED_DIGEST:
        raise ValueError(
            f"entry.png failed its integrity check: "
            f"expected sha256 {EXPECTED_DIGEST}, got {actual}. "
            f"The image on disk is not the one this entry was built from."
        )
    return image_path.read_bytes()


def check_png(image_bytes: bytes) -> tuple[int, int]:
    """Validate the PNG signature, size and dimensions; return (width, height).

    Raises:
        ValueError: the bytes are not a PNG, are too large, or exceed the
            competition's pixel limits.
    """
    if len(image_bytes) > MAX_BYTES:
        raise ValueError(
            f"entry.png is {len(image_bytes)} bytes, over the 1 MiB limit"
        )
    if image_bytes[:8] != PNG_SIGNATURE:
        raise ValueError("entry.png does not start with the PNG signature")
    if len(image_bytes) < 33 or image_bytes[12:16] != b"IHDR":
        raise ValueError("entry.png has no IHDR chunk where one belongs")
    width, height = struct.unpack(">II", image_bytes[16:24])
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise ValueError(
            f"entry.png is {width}x{height}, over the 1024x1024 limit"
        )
    return width, height


def destination_dir() -> Path:
    """Output folder from the environment, falling back to /output."""
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    return Path(raw) if raw else Path(FALLBACK_OUTPUT_DIR)


def publish(image_bytes: bytes, out_dir: Path) -> Path:
    """Write the verified bytes to <out_dir>/entry.png and return its path.

    The written file is read back and hashed: publishing only counts as
    done when the copy on disk matches the expected digest exactly.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / IMAGE_NAME
    target.write_bytes(image_bytes)
    if digest_of(target) != EXPECTED_DIGEST:
        raise ValueError(
            f"published file failed its re-read check: {target} "
            f"does not hash to the expected digest"
        )
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish the verified entry.png to /output/entry.png."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the bundled image without writing anything",
    )
    args = parser.parse_args(argv)
    image_bytes = read_verified_image()
    width, height = check_png(image_bytes)
    print(
        f"entry.png: {len(image_bytes)} bytes, {width}x{height}, "
        f"sha256 {EXPECTED_DIGEST}"
    )
    if args.check:
        print("check passed: bundled image is the expected one")
        return 0
    target = publish(image_bytes, destination_dir())
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
