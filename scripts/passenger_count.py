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
    type_labels = (("adultNum", "成人"), ("childNum", "儿童"), ("infantNum", "婴儿"))
    mismatches: list[str] = []
    for key, label in type_labels:
        if actual[key] != expected[key]:
            mismatches.append(f"{label}：搜索 {expected[key]} 人，实际填写 {actual[key]} 人")
    if not mismatches:
        return None

    expected_parts = []
    for key, label in type_labels:
        if expected[key] > 0:
            expected_parts.append(f"{label} {expected[key]} 人")
    expected_desc = "、".join(expected_parts) if expected_parts else "成人 1 人"

    return (
        "乘客人数与搜索不符：\n"
        + "\n".join(f"  · {m}" for m in mismatches)
        + f"\n\n本次搜索为 {expected_desc}，请按以下方式处理：\n"
        + f"  · 仍预订 {expected_desc}：请重新提供对应人数的乘客证件信息。\n"
        + "  · 需要更改人数：请先说「重新搜索」并指定新的人数，再提供乘客信息。"
    )
