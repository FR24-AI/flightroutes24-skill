#!/usr/bin/env python3
"""调用 export /api/skill/shopping。"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request
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
    EXPORT_BASE_URL,
    GRAY_HEADER,
    PENDING_PAYLOAD_FILE,
    SHOPPING_PATH,
)

from booking_format import wrap_search  # noqa: E402
from newapi_client import run_search  # noqa: E402

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
        "skill": "fr-newapi-search",
        "status": "success",
        "action": "quota-status",
        "data": {"clientKeyReady": True, "clientKeyPrefix": key[:8] + "..."},
        "message": "客户端密钥已就绪，搜索后将返回剩余次数",
    }


def _build_request_headers(client_key: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        CLIENT_KEY_HEADER: client_key,
    }
    if GRAY_HEADER:
        headers["gray"] = GRAY_HEADER
    return headers


def search(payload: dict, *, selection: str = "direct") -> dict:
    raw, mode = run_search(payload)
    code = str(raw.get("code", ""))
    success = code in ("0", "000000")
    result = wrap_search(raw, mode)
    if not success:
        if code == "307901":
            result["message"] = "今日搜索次数已用完（每日 10 次），请明日再试"
        return result

    data = result.get("data") or {}
    pick = (selection or "direct").strip().lower()
    selected = data.get("directLowest") if pick == "direct" else data.get("transferLowest")
    if not selected:
        selected = data.get("directLowest") or data.get("transferLowest")
    if selected:
        BOOKING_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        BOOKING_CONTEXT_FILE.write_text(
            json.dumps(
                {
                    "searchPayload": payload,
                    "searchMode": mode,
                    "traceId": data.get("traceId"),
                    "processingTime": data.get("processingTime"),
                    "selection": pick,
                    "selectedOffer": selected,
                    "directLowest": data.get("directLowest"),
                    "transferLowest": data.get("transferLowest"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return result


def _http_error_hint(status_code: int) -> str | None:
    if status_code == 404 and not GRAY_HEADER:
        return "测试环境通常需要设置 FR_SKILL_GRAY_HEADER（如 ww）"
    if status_code == 404 and GRAY_HEADER:
        return f"已带 gray={GRAY_HEADER} 仍 404，请确认域名与路径 {SHOPPING_PATH}"
    return None


def main():
    parser = argparse.ArgumentParser(description="fr-newapi-search skill client")
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
        out = search(payload, selection=args.selection)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
