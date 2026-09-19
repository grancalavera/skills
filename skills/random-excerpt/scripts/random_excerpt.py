#!/usr/bin/env python3
"""Seek to a random byte in a text file and print the readable passage around it.

Given a file, picks a random byte offset. Given a directory, first picks a random
text file inside it (recursively, or within --depth levels), then a random byte
in that file. The raw window
around the offset is trimmed outward-in to clean boundaries -- paragraph breaks
where the file has them, line breaks otherwise -- so the excerpt reads as text
rather than starting mid-word.

Binary files are refused when named directly and skipped when walking a directory.
"""

from __future__ import annotations

import argparse
import os
import random
import sys

SNIFF_BYTES = 8192

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".next",
    ".cache",
}

# Below this size we can afford to count newlines for human-friendly line numbers.
LINE_NUMBER_LIMIT = 10 * 1024 * 1024


class ExcerptError(Exception):
    """Something the user needs to know about, reported without a traceback."""


def looks_binary(path: str) -> bool:
    """Sniff the head of a file for NUL bytes or undecodable UTF-8."""
    try:
        with open(path, "rb") as handle:
            head = handle.read(SNIFF_BYTES)
    except OSError:
        return True
    if b"\x00" in head:
        return True
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        # A multi-byte character may straddle the sniff boundary, so only the
        # tail is allowed to fail.
        try:
            head[:-4].decode("utf-8")
        except UnicodeDecodeError:
            return True
    return False


def candidate_files(root: str, max_depth: int | None = None) -> list[str]:
    """Every non-empty, non-hidden file under root, noise directories pruned.

    max_depth counts directory levels: 1 keeps only the files sitting directly in
    root, 2 also takes its immediate subdirectories, and None walks the whole tree.
    """
    found = []
    root_depth = os.path.normpath(root).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        ]
        if max_depth is not None:
            depth = os.path.normpath(dirpath).count(os.sep) - root_depth + 1
            if depth >= max_depth:
                dirnames[:] = []
        for name in filenames:
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            try:
                if os.path.isfile(full) and os.path.getsize(full) > 0:
                    found.append(full)
            except OSError:
                continue
    return sorted(found)


def empty_pool_message(root: str, max_depth: int | None, readable: bool = False) -> str:
    """Explain an empty pool, naming --depth when that is what emptied it.

    A depth-limited draw that finds nothing is usually a scoping mistake rather
    than an empty folder, so it is worth saying whether the rest of the tree has
    something in it.
    """
    kind = "readable text files" if readable else "files"
    if max_depth is not None and candidate_files(root):
        return (
            f"no {kind} directly under {root} at --depth {max_depth}, "
            f"though there are some deeper in the tree"
        )
    return f"no {kind} found under {root}"


def pick_file(
    root: str,
    rng: random.Random,
    weight_by_size: bool,
    max_depth: int | None = None,
) -> str:
    """Choose a random readable text file under root.

    Files are equally likely by default rather than weighted by length: the point
    is to visit different documents, and size weighting would keep landing in
    whichever file happens to be biggest.
    """
    pool = candidate_files(root, max_depth)
    if not pool:
        raise ExcerptError(empty_pool_message(root, max_depth))

    weights = None
    if weight_by_size:
        weights = [max(1, os.path.getsize(p)) for p in pool]

    # Binary files are only detected by reading them, so sample and retry rather
    # than sniffing the whole tree up front.
    for _ in range(min(50, len(pool) * 2)):
        if weights:
            choice = rng.choices(pool, weights=weights, k=1)[0]
        else:
            choice = rng.choice(pool)
        if not looks_binary(choice):
            return choice
        index = pool.index(choice)
        pool.pop(index)
        if weights:
            weights.pop(index)
        if not pool:
            break
    raise ExcerptError(empty_pool_message(root, max_depth, readable=True))


def snap_to_char_boundary(handle, offset: int, file_size: int) -> int:
    """Nudge an offset forward off the middle of a multi-byte character.

    The window is split at the offset and each half decoded separately, so a split
    inside a character would leave both halves ragged at the join and the excerpt
    would no longer be a contiguous slice of the file.
    """
    handle.seek(offset)
    probe = handle.read(4)
    shift = 0
    while shift < len(probe) and 0x80 <= probe[shift] <= 0xBF:
        shift += 1
    return min(offset + shift, file_size)


def decode_forward(chunk: bytes) -> str:
    """Decode a chunk whose first bytes may be a truncated character."""
    for skip in range(4):
        try:
            return chunk[skip:].decode("utf-8")
        except UnicodeDecodeError:
            continue
    return chunk.decode("utf-8", errors="ignore")


def decode_backward(chunk: bytes) -> str:
    """Decode a chunk whose last bytes may be a truncated character."""
    for trim in range(4):
        end = len(chunk) - trim
        try:
            return chunk[:end].decode("utf-8")
        except UnicodeDecodeError:
            continue
    return chunk.decode("utf-8", errors="ignore")


def trim_start(text: str) -> str:
    """Drop the ragged head of the window, preferring a paragraph break.

    A paragraph break is only accepted in the first half; past that it would cost
    more context than the tidiness is worth, so a line break is used instead.
    Files without either -- minified code, one long line -- keep the raw cut.
    """
    if not text:
        return text
    limit = len(text) // 2
    para = text.find("\n\n")
    if 0 <= para <= limit:
        return text[para + 2 :].lstrip("\n")
    line = text.find("\n")
    if line >= 0:
        return text[line + 1 :]
    return text


def trim_end(text: str) -> str:
    """Drop the ragged tail of the window, mirroring trim_start."""
    if not text:
        return text
    limit = len(text) // 2
    para = text.rfind("\n\n")
    if para >= limit:
        return text[:para].rstrip("\n")
    line = text.rfind("\n")
    if line >= 0:
        return text[:line]
    return text


def read_excerpt(path: str, size: int, rng: random.Random) -> dict:
    """Read a size-ish byte window around a random offset and tidy its edges."""
    file_size = os.path.getsize(path)
    if file_size == 0:
        raise ExcerptError(f"{path} is empty")
    if looks_binary(path):
        raise ExcerptError(
            f"{path} looks like a binary file -- this skill only reads text"
        )

    offset = rng.randrange(file_size)

    if file_size <= size:
        # Nothing to sample: trimming a file that already fits would only lose
        # text the user was going to see anyway.
        with open(path, "rb") as handle:
            whole = handle.read()
        text = whole.decode("utf-8", errors="ignore").strip("\n")
        if not text.strip():
            raise ExcerptError(f"{path} has no readable text")
        return {
            "path": path,
            "offset": offset,
            "start_byte": 0,
            "end_byte": file_size,
            "file_size": file_size,
            "text": text,
            "start_line": 1,
            "end_line": 1 + text.count("\n"),
        }

    half = max(1, size // 2)
    # Extra margin so trimming has boundaries to find without eating the excerpt.
    margin = max(200, size // 4)
    raw_start = max(0, offset - half - margin)
    raw_end = min(file_size, offset + half + margin)

    with open(path, "rb") as handle:
        offset = snap_to_char_boundary(handle, offset, file_size)
        raw_start = max(0, offset - half - margin)
        raw_end = min(file_size, offset + half + margin)
        handle.seek(raw_start)
        before = handle.read(offset - raw_start)
        after = handle.read(raw_end - offset)

    head = decode_forward(before)[-half:]
    tail = decode_backward(after)[:half]

    head = trim_start(head)
    tail = trim_end(tail)
    combined = head + tail
    text = combined.strip("\n")
    if not text.strip():
        # Landed in a run of blank lines; the untrimmed window is better than nothing.
        head = decode_forward(before)[-half:]
        tail = decode_backward(after)[:half]
        combined = head + tail
        text = combined.strip("\n")
    if not text.strip():
        raise ExcerptError(f"{path} has no readable text around byte {offset}")

    # The stripped newlines are one byte each, so the offsets stay exact -- which
    # matters because the reported line numbers are derived from start_byte.
    lead = len(combined) - len(combined.lstrip("\n"))
    trail = len(combined) - len(combined.rstrip("\n"))
    start_byte = offset - len(head.encode("utf-8")) + lead
    end_byte = offset + len(tail.encode("utf-8")) - trail

    result = {
        "path": path,
        "offset": offset,
        "start_byte": max(0, start_byte),
        "end_byte": min(file_size, end_byte),
        "file_size": file_size,
        "text": text,
        "start_line": None,
        "end_line": None,
    }

    if file_size <= LINE_NUMBER_LIMIT:
        with open(path, "rb") as handle:
            preceding = handle.read(max(0, start_byte))
        start_line = preceding.count(b"\n") + 1
        result["start_line"] = start_line
        result["end_line"] = start_line + text.count("\n")

    return result


def format_excerpt(item: dict, root: str | None) -> str:
    """Render one excerpt with a header that says where in the file it came from."""
    path = item["path"]
    if root and os.path.isdir(root):
        try:
            path = os.path.relpath(path, root)
        except ValueError:
            pass

    parts = [path]
    if item["start_byte"] == 0 and item["end_byte"] == item["file_size"]:
        # The file fit inside the window, so there is no "where in the file" to report.
        parts.append(f"whole file, {item['file_size']:,} bytes")
    else:
        if item["start_line"] is not None:
            parts.append(f"lines {item['start_line']:,}-{item['end_line']:,}")
        position = 100.0 * item["offset"] / item["file_size"]
        parts.append(
            f"bytes {item['start_byte']:,}-{item['end_byte']:,} "
            f"of {item['file_size']:,} ({position:.0f}% in)"
        )
    header = " · ".join(parts)

    return f"--- {header} ---\n\n{item['text']}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the text around a random byte offset in a file, "
        "or in a random text file under a directory."
    )
    parser.add_argument("path", help="file or directory to sample from")
    parser.add_argument(
        "--size",
        type=int,
        default=2000,
        help="approximate excerpt size in bytes (default: 2000)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="number of excerpts to draw (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="seed the generator to reproduce a previous draw",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="in a directory, how many levels to descend: 1 is the named "
        "directory only, 2 adds its immediate subdirectories (default: no limit)",
    )
    parser.add_argument(
        "--weight-by-size",
        action="store_true",
        help="in a directory, favour longer files instead of treating all files equally",
    )
    args = parser.parse_args(argv)

    target = os.path.expanduser(args.path)
    if not os.path.exists(target):
        print(f"error: no such file or directory: {target}", file=sys.stderr)
        return 1
    if args.size < 100:
        print("error: --size must be at least 100 bytes", file=sys.stderr)
        return 1
    if args.count < 1:
        print("error: --count must be at least 1", file=sys.stderr)
        return 1
    if args.depth is not None and args.depth < 1:
        print("error: --depth must be at least 1", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    root = target if os.path.isdir(target) else None

    chunks = []
    try:
        for _ in range(args.count):
            source = (
                pick_file(target, rng, args.weight_by_size, args.depth)
                if root
                else target
            )
            chunks.append(format_excerpt(read_excerpt(source, args.size, rng), root))
    except ExcerptError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print("\n".join(chunks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
