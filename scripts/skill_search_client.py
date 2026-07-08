#!/usr/bin/env python3
"""调用 export /ai/shopping/v2。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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

from booking_format import wrap_search_v2, wrap_select  # noqa: E402
from newapi_client import run_search_v2  # noqa: E402
from offer_select import (  # noqa: E402
    apply_offer_selection,
    load_booking_context,
    resolve_offer_selection,
    save_booking_context,
)
from skill_client_key import ensure_client_key  # noqa: E402


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


def _write_booking_context(
    payload: dict,
    agent: dict[str, Any],
    *,
    mode: str,
    selection: str | None = None,
    selected: dict | None = None,
) -> None:
    ctx: dict[str, Any] = {
        "searchPayload": payload,
        "searchMode": mode,
        "traceId": agent.get("traceId"),
        "processingTime": agent.get("processingTime"),
        "directOptions": agent.get("directOptions"),
        "directLowest": agent.get("directLowest"),
        "transferLowest": agent.get("transferLowest"),
    }
    if selection and selected:
        ctx["selection"] = selection
        ctx["selectedOffer"] = selected
    else:
        ctx["selection"] = None
    save_booking_context(ctx)
    if PASSENGERS_FILE.exists():
        PASSENGERS_FILE.unlink()


def search_v2(payload: dict, *, selection: str = "none") -> dict:
    """v2 搜索：直飞按航班号去重，每航班号取最低价，最多 20 条。"""
    raw, mode = run_search_v2(payload)
    code = str(raw.get("code", ""))
    success = code in ("0", "000000")
    result = wrap_search_v2(raw, mode, search_payload=payload)
    if not success:
        return result

    agent = result.get("agentOnly") or {}
    pick = (selection or "none").strip().lower()
    selected = None
    if pick == "direct":
        selected = agent.get("directLowest")
    elif pick == "transfer":
        selected = agent.get("transferLowest")
    if selected:
        _write_booking_context(payload, agent, mode=mode, selection=pick, selected=selected)
    else:
        _write_booking_context(payload, agent, mode=mode)
    return result


def select_offer(
    *,
    index: int | None = None,
    offer_id: str | None = None,
    flight: str | None = None,
    pick: str | None = None,
    context_file: Path | None = None,
) -> dict:
    ctx = load_booking_context(context_file or BOOKING_CONTEXT_FILE)
    selected, selection_key, err = resolve_offer_selection(
        ctx,
        index=index,
        offer_id=offer_id,
        flight=flight,
        pick=pick,
    )
    if err or not selected or not selection_key:
        from output_export import failure_envelope  # noqa: E402

        return failure_envelope(
            "select",
            err or "选择失败",
            agent_only={"detail": "请先 search，再用 select --index / --offer-id / --flight / --pick"},
        )
    updated = apply_offer_selection(ctx, selected, selection_key)
    save_booking_context(updated, context_file or BOOKING_CONTEXT_FILE)
    return wrap_select(selected, updated, selection_key=selection_key)


def main():
    parser = argparse.ArgumentParser(description="fr24-ai skill client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ensure-key", help="生成或读取本地 clientKey")
    sub.add_parser("quota-status", help="检查本地密钥状态")
    p_search = sub.add_parser("search", help="执行搜索")
    p_search.add_argument("--payload-file", required=True, help="SkillSearchRq JSON 文件")
    p_search.add_argument(
        "--selection",
        default="none",
        choices=("none", "direct", "transfer"),
        help="搜索后自动选中：none=仅缓存列表（默认）；direct=直飞最低；transfer=中转最低",
    )
    p_select = sub.add_parser("select", help="从上次搜索结果中选择报价（不重新搜索）")
    p_select.add_argument("--index", type=int, help="直飞列表序号（从 1 开始，对应展示的第 N 条）")
    p_select.add_argument("--offer-id", dest="offer_id", help="报价ID（quoteId）")
    p_select.add_argument("--flight", help="航班号（如 SQ8617）")
    p_select.add_argument(
        "--pick",
        choices=("direct-lowest", "transfer"),
        help="选中直飞最低或中转最低（等同 search --selection direct|transfer，但不重搜）",
    )
    p_select.add_argument(
        "--context-file",
        default=str(BOOKING_CONTEXT_FILE),
        help="booking_context.json 路径",
    )
    args = parser.parse_args()
    if args.cmd == "ensure-key":
        ensure_client_key()
        out = quota_status()
    elif args.cmd == "quota-status":
        out = quota_status()
    elif args.cmd == "select":
        out = select_offer(
            index=args.index,
            offer_id=args.offer_id,
            flight=args.flight,
            pick=args.pick,
            context_file=Path(args.context_file),
        )
    else:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
        PENDING_PAYLOAD_FILE.parent.mkdir(parents=True, exist_ok=True)
        PENDING_PAYLOAD_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out = search_v2(payload, selection=args.selection)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
