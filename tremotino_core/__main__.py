#!/usr/bin/env python3
"""Command-line JSON facade for Tremotino core."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional

from . import core


def _json_arg(raw: Optional[str]) -> dict[str, Any]:
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise SystemExit("--json must decode to an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m tremotino_core")
    parser.add_argument("command")
    parser.add_argument("--json", dest="json_arg")
    args = parser.parse_args()
    payload = _json_arg(args.json_arg)

    result = core.dispatch(args.command, payload)
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
