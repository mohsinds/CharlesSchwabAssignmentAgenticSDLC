#!/usr/bin/env python3
"""CLI helper to ingest a codebase path into the knowledge store."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--collection", default="default")
    args = parser.parse_args()
    from services.knowledge.ingest import ingest_directory

    result = await ingest_directory(args.path, collection=args.collection)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
