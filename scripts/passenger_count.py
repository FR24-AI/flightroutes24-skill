"""乘客证件列表与搜索人数一致性校验。"""
from __future__ import annotations

from typing import Any


def count_passengers_by_type(passengers: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"adultNum": 0, "childNum": 0, "infantNum": 0}
    for pax in passengers:
        pax_type = str(pax.get("paxType") or "ADT").upper()
        if pax_type == "CHD":
            counts["childNum"] += 1
        elif pax_type == "INF":
            counts["infantNum"] += 1
        else:
            counts["adultNum"] += 1
    return counts


def expected_passengers_from_search(search_payload: dict[str, Any] | None) -> dict[str, int]:
    payload = search_payload or {}
    return {
        "adultNum": int(payload.get("adultNum", 1) or 1),
        "childNum": int(payload.get("childNum", 0) or 0),
        "infantNum": int(payload.get("infantNum", 0) or 0),
    }


def validate_passengers_match_search(
    passengers: list[dict[str, Any]],
    search_payload: dict[str, Any] | None,
) -> str | None:
    """校验证件列表人数是否与搜索 payload 一致。"""
    if not passengers:
        return "未识别到乘客信息"
    expected = expected_passengers_from_search(search_payload)
    actual = count_passengers_by_type(passengers)
    mismatches: list[str] = []
    labels = (("adultNum", "成人"), ("childNum", "儿童"), ("infantNum", "婴儿"))
    for key, label in labels:
        if actual[key] != expected[key]:
            mismatches.append(f"{label}{expected[key]}人（实际解析{actual[key]}人）")
    if not mismatches:
        return None
    return (
        "乘客人数与搜索不一致："
        + "、".join(mismatches)
        + "。请按搜索人数补全每位乘客信息（建议用「成人：」「儿童：」分行标注）。"
    )
