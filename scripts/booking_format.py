"""搜索结果格式化（Skill JSON 信封）。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import (  # noqa: E402
    CONTACT_MESSAGE,
    CONTACT_MESSAGE_EN,
    REGISTER_PORTAL_URL,
    USER_SKILL_QUOTA_EXCEEDED_MESSAGE,
    is_newapi_configured,
)
from fare_summarizer import summarize_response, _summarize_from_data_v2  # noqa: E402
from search_refinement import describe_preferences, extract_search_filters  # noqa: E402
from output_export import (  # noqa: E402
    search_agent_only,
    search_user_view,
    user_offer,
    wrap_envelope,
)

SUCCESS_CODES = frozenset({"0", "000000"})


def _is_success(code: str) -> bool:
    return str(code) in SUCCESS_CODES


def _offer_block(label: str, offer: dict | None) -> dict[str, Any] | None:
    if not offer:
        return None
    block: dict[str, Any] = {
        "label": label,
        "offerId": str(offer["offerId"]) if offer.get("offerId") is not None else None,
        "route": offer.get("route"),
        "flights": offer.get("flights"),
        "totalPrice": offer.get("totalPrice"),
        "currency": offer.get("currency"),
        "platingCarrier": offer.get("platingCarrier"),
        "segments": offer.get("segments"),
        "refundChange": offer.get("refundChange"),
        "baggage": offer.get("baggage"),
    }
    if offer.get("returnSegments"):
        block["returnSegments"] = offer["returnSegments"]
    if offer.get("returnRoute"):
        block["returnRoute"] = offer["returnRoute"]
    if offer.get("returnBaggage"):
        block["returnBaggage"] = offer["returnBaggage"]
    return block


def _normalize_newapi_raw_v2(raw: dict, *, filters: dict[str, Any] | None = None) -> dict:
    """v2：用 directOptions 汇总，服务端已返回 directOptions 时直接使用。"""
    server_summary = raw.get("summary") or {}
    if server_summary.get("directOptions") and not filters:
        return raw
    data = raw.get("data")
    if isinstance(data, dict):
        return {**raw, "summary": _summarize_from_data_v2(data, filters=filters)}
    return raw


def format_search_data_v2(
    raw: dict,
    search_mode: str,
    *,
    search_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """v2 版本：直飞展示按航班号去重的列表（directOptions），中转仍取一条最低价。"""
    skill_like = search_mode in ("skill", "skill-auth", "newapi")
    prefs = (search_payload or {}).get("preferences") or {}
    filters = extract_search_filters(prefs)
    filter_note = describe_preferences(prefs)
    if search_mode == "newapi":
        raw = _normalize_newapi_raw_v2(raw, filters=filters or None)

    code = str(raw.get("code", ""))
    success = _is_success(code)
    summary = (
        summarize_response(raw, filters=filters or None)
        if skill_like
        else (raw.get("summary") or {})
    )

    direct_options: list[dict[str, Any]] = summary.get("directOptions") or []
    transfer = _offer_block("中转最低", summary.get("transferLowest"))
    direct_lowest = _offer_block("直飞最低", summary.get("directLowest"))

    lines: list[str] = []
    if success:
        if search_mode == "skill-auth":
            mode_label = "采购搜索"
        elif search_mode == "newapi":
            mode_label = "NewApi 采购搜索"
        else:
            mode_label = "Skill 搜索"
        lines.append(f"（{mode_label}）")
        if filter_note:
            lines.append(f"筛选条件：{filter_note}")
        if filter_note and not direct_options and not transfer:
            lines.append(
                f"未找到符合上述条件的报价（共检索 {summary.get('totalOffers', 0)} 条）。"
                f"请放宽航司或起飞时段后说「重新搜索」或补充条件。"
            )
        if direct_options:
            lines.append(f"【直飞报价 共{len(direct_options)}条】")
            for i, opt in enumerate(direct_options, start=1):
                lines.append(
                    f"  {i}. {opt.get('flights', '')} "
                    f"{opt.get('segments', [{}])[0].get('depTime', '')[:5] if opt.get('segments') else ''}"
                    f" 约 {opt.get('totalPrice')} {opt.get('currency', 'CNY')}/人"
                    f"  报价ID: {opt.get('offerId', '')}"
                )
        if transfer:
            lines.append(
                f"【中转最低】{transfer['route']} {transfer['flights']} "
                f"约 {transfer['totalPrice']} {transfer['currency']}/人"
            )
        lines.append(CONTACT_MESSAGE)
    else:
        if code == "307904":
            lines.append("搜索需要采购密钥，请先配置 FR_NEWAPI_APPKEY 与 FR_NEWAPI_SIGN_SECRET，再重试。详见「采购密钥」章节。")
        elif code == "307901":
            lines.append(USER_SKILL_QUOTA_EXCEEDED_MESSAGE)
        else:
            lines.append(raw.get("message") or f"搜索失败：{code}")

    return {
        "success": success,
        "code": code,
        "traceId": raw.get("traceId"),
        "processingTime": raw.get("processingTime"),
        "searchMode": search_mode,
        "directOptions": direct_options,
        "directLowest": direct_lowest,
        "transferLowest": transfer,
        "remainingQuota": summary.get("remainingQuota"),
        "dailyLimit": summary.get("dailyLimit"),
        "registerPortalUrl": REGISTER_PORTAL_URL if not is_newapi_configured() else None,
        "filterNote": filter_note or None,
        "contactMessage": CONTACT_MESSAGE,
        "contactMessageEn": CONTACT_MESSAGE_EN,
        "message": "\n".join(lines),
    }


def wrap_search_v2(
    raw: dict,
    search_mode: str,
    *,
    search_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    internal = format_search_data_v2(raw, search_mode, search_payload=search_payload)
    user_view = search_user_view(internal)
    return wrap_envelope(
        action="search",
        status="success" if internal.get("success") else "failure",
        user_view=user_view,
        agent_only=search_agent_only(internal),
        message=user_view.get("message", ""),
    )


def wrap_select(
    selected: dict[str, Any],
    ctx: dict[str, Any],
    *,
    selection_key: str,
) -> dict[str, Any]:
    """用户从已展示列表选定报价后的响应（不重新搜索）。"""
    offer_uv = user_offer(selected) or {}
    flights = offer_uv.get("flights") or selected.get("flights") or ""
    quote_id = offer_uv.get("quoteId") or selected.get("offerId")
    price = offer_uv.get("totalPrice")
    currency = offer_uv.get("currency") or "CNY"
    route = offer_uv.get("route") or selected.get("route") or ""
    msg = (
        f"已选择报价：{flights} {route}，约 {price} {currency}/人。"
        f"报价ID：{quote_id}。\n"
        f"{CONTACT_MESSAGE}"
    )
    user_view: dict[str, Any] = {
        "selectedOffer": offer_uv,
        "contactMessage": CONTACT_MESSAGE,
        "contactMessageEn": CONTACT_MESSAGE_EN,
        "message": msg,
    }
    agent_only: dict[str, Any] = {
        "selection": selection_key,
        "offerId": selected.get("offerId"),
        "traceId": ctx.get("traceId"),
        "processingTime": ctx.get("processingTime"),
    }
    return wrap_envelope(
        action="select",
        status="success",
        user_view=user_view,
        agent_only=agent_only,
        message=msg,
    )
