"""从 booking_context 缓存中选定报价（不重新搜索）。"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from config import BOOKING_CONTEXT_FILE


def load_booking_context(path: Path | None = None) -> dict[str, Any]:
    p = path or BOOKING_CONTEXT_FILE
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_booking_context(ctx: dict[str, Any], path: Path | None = None) -> None:
    p = path or BOOKING_CONTEXT_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")


def _norm_offer_id(value: Any) -> str:
    return str(value or "").strip()


def _match_flight(flights: str | None, token: str) -> bool:
    if not flights or not token:
        return False
    want = re.sub(r"\s+", "", token.upper())
    hay = re.sub(r"\s+", "", str(flights).upper())
    return want in hay or hay in want


def _find_by_offer_id(ctx: dict[str, Any], offer_id: str) -> tuple[dict[str, Any] | None, str]:
    oid = _norm_offer_id(offer_id)
    if not oid:
        return None, "报价ID为空"
    for opt in ctx.get("directOptions") or []:
        if isinstance(opt, dict) and _norm_offer_id(opt.get("offerId")) == oid:
            return opt, f"direct-offer-{oid}"
    transfer = ctx.get("transferLowest")
    if isinstance(transfer, dict) and _norm_offer_id(transfer.get("offerId")) == oid:
        return transfer, "transfer"
    return None, f"未找到报价ID：{oid}"


def _find_by_flight(ctx: dict[str, Any], flight: str) -> tuple[dict[str, Any] | None, str]:
    token = (flight or "").strip()
    if not token:
        return None, "航班号为空"
    matches: list[dict[str, Any]] = []
    for opt in ctx.get("directOptions") or []:
        if isinstance(opt, dict) and _match_flight(opt.get("flights"), token):
            matches.append(opt)
    if len(matches) == 1:
        return matches[0], f"direct-flight-{token.upper()}"
    if len(matches) > 1:
        return None, f"航班号 {token} 匹配到多条直飞报价，请用序号或报价ID选择"
    transfer = ctx.get("transferLowest")
    if isinstance(transfer, dict) and _match_flight(transfer.get("flights"), token):
        return transfer, "transfer"
    return None, f"未找到航班号：{token}"


def resolve_offer_selection(
    ctx: dict[str, Any],
    *,
    index: int | None = None,
    offer_id: str | None = None,
    flight: str | None = None,
    pick: str | None = None,
) -> tuple[dict[str, Any] | None, str | None, str | None]:
    """
    从已有搜索缓存中选定报价。

    Returns:
        (selected_offer, selection_key, error_message)
    """
    if not ctx.get("directOptions") and not ctx.get("transferLowest"):
        return None, None, "请先完成搜索，再选择报价"

    modes = sum(
        1
        for v in (index, offer_id, flight, pick)
        if v is not None and (not isinstance(v, str) or v.strip())
    )
    if modes != 1:
        return None, None, "请指定一种选择方式：--index / --offer-id / --flight / --pick"

    if pick:
        mode = pick.strip().lower()
        if mode in ("direct", "direct-lowest", "direct_lowest"):
            selected = ctx.get("directLowest")
            if not selected:
                options = ctx.get("directOptions") or []
                selected = options[0] if options else None
            if not selected:
                return None, None, "当前搜索结果中没有直飞报价"
            return selected, "direct-lowest", None
        if mode == "transfer":
            selected = ctx.get("transferLowest")
            if not selected:
                return None, None, "当前搜索结果中没有中转报价"
            return selected, "transfer", None
        return None, None, f"不支持的 --pick 值：{pick}（可用 direct-lowest / transfer）"

    if index is not None:
        if index < 1:
            return None, None, "序号须从 1 开始"
        options = [o for o in (ctx.get("directOptions") or []) if isinstance(o, dict)]
        if index > len(options):
            return None, None, f"直飞报价共 {len(options)} 条，无法选择第 {index} 条"
        return options[index - 1], f"direct-index-{index}", None

    if offer_id:
        selected, key = _find_by_offer_id(ctx, offer_id)
        if not selected:
            return None, None, key
        return selected, key, None

    if flight:
        selected, key = _find_by_flight(ctx, flight)
        if not selected:
            return None, None, key
        return selected, key, None

    return None, None, "未指定选择条件"


def apply_offer_selection(
    ctx: dict[str, Any],
    selected: dict[str, Any],
    selection_key: str,
) -> dict[str, Any]:
    updated = dict(ctx)
    updated["selectedOffer"] = selected
    updated["selection"] = selection_key
    return updated
