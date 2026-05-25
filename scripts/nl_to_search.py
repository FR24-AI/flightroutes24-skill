#!/usr/bin/env python3
"""自然语言 -> 待确认搜索 payload。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from query_parser import build_payload_from_intent, parse_simple_text  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
PENDING = _ROOT / ".cache" / "pending_search.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["parse", "build"])
    parser.add_argument("--text", default="")
    parser.add_argument("--intent-file", default="")
    args = parser.parse_args()

    if args.command == "parse":
        payload, summary, err = parse_simple_text(args.text)
    else:
        intent = json.loads(Path(args.intent_file).read_text(encoding="utf-8"))
        payload, summary, err = build_payload_from_intent(intent)

    if err:
        out = {"skill": "fr-newapi-search", "status": "failure", "action": "parse", "message": err}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1)

    PENDING.parent.mkdir(parents=True, exist_ok=True)
    PENDING.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out = {
        "skill": "fr-newapi-search",
        "status": "success",
        "action": "parse",
        "data": {"payload": payload, "intentSummary": summary, "payloadFile": str(PENDING)},
        "message": "解析成功。请向用户确认后执行：python scripts/skill_search_client.py search --payload-file .cache/pending_search.json",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
