#!/usr/bin/env python3
"""调用 export /ai/shopping/v2。"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# 允许从 skill 根目录导入 config
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (  # noqa: E402
    BOOKING_CONTEXT_FILE,
    CACHE_DIR,
    CLIENT_KEY_FILE,
    CLIENT_KEY_HEADER,
    GRAY_HEADER,
    PASSENGERS_FILE,
    PENDING_PAYLOAD_FILE,
    SKILL_ID,
)

from booking_format import wrap_search_v2  # noqa: E402
from newapi_client import run_search_v2  # noqa: E402

BJ = ZoneInfo("Asia/Shanghai")


def ensure_client_key() -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CLIENT_KEY_FILE.exists():
        data = json.loads(CLIENT_KEY_FILE.read_text(encoding="utf-8"))
        key = data.get("clientKey", "")
        if len(key) >= 32:
            return key
    key = secrets.token_urlsafe(32)
    CLIENT_KEY_FILE.write_text(
        json.dumps(
            {"clientKey": key, "createdAt": datetime.now(BJ).isoformat()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return key


def quota_status() -> dict:
    key = ensure_client_key()
    # 服务端仅在搜索后返回 remainingQuota；本地仅展示 key 已就绪
    return {
        "skill": SKILL_ID,
        "status": "success",
        "action": "quota-status",
        "data": {"clientKeyReady": True, "clientKeyPrefix": key[:8] + "..."},
        "message": "客户端密钥已就绪，搜索后将返回剩余次数",
    }


def search_v2(payload: dict, *, selection: str = "direct") -> dict:
    """v2 搜索：直飞按航班号去重，每航班号取最低价，最多 20 条。"""
    raw, mode = run_search_v2(payload)
    code = str(raw.get("code", ""))
    success = code in ("0", "000000")
    result = wrap_search_v2(raw, mode, search_payload=payload)
    if not success:
        return result

    agent = result.get("agentOnly") or {}
    pick = (selection or "direct").strip().lower()
    selected = agent.get("directLowest") if pick == "direct" else agent.get("transferLowest")
    if not selected:
        selected = agent.get("directLowest") or agent.get("transferLowest")
    if selected:
        BOOKING_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        BOOKING_CONTEXT_FILE.write_text(
            json.dumps(
                {
                    "searchPayload": payload,
                    "searchMode": mode,
                    "traceId": agent.get("traceId"),
                    "processingTime": agent.get("processingTime"),
                    "selection": pick,
                    "selectedOffer": selected,
                    "directOptions": agent.get("directOptions"),
                    "directLowest": agent.get("directLowest"),
                    "transferLowest": agent.get("transferLowest"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        # 每次新搜索成功后清除旧乘客数据，强制下次预订重新收集
        if PASSENGERS_FILE.exists():
            PASSENGERS_FILE.unlink()
    return result


def main():
    parser = argparse.ArgumentParser(description="fr24-ai skill client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ensure-key", help="生成或读取本地 clientKey")
    sub.add_parser("quota-status", help="检查本地密钥状态")
    p_search = sub.add_parser("search", help="执行搜索")
    p_search.add_argument("--payload-file", required=True, help="SkillSearchRq JSON 文件")
    p_search.add_argument(
        "--selection",
        default="direct",
        choices=("direct", "transfer"),
        help="写入 booking_context 的选定报价（用户确认后）",
    )
    args = parser.parse_args()
    if args.cmd == "ensure-key":
        ensure_client_key()
        out = quota_status()
    elif args.cmd == "quota-status":
        out = quota_status()
    else:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        PENDING_PAYLOAD_FILE.parent.mkdir(parents=True, exist_ok=True)
        PENDING_PAYLOAD_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out = search_v2(payload, selection=args.selection)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
