#!/usr/bin/env python3
"""offer_select / select 子命令自检。"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _sample_context() -> dict:
    options = [
        {"flights": "LX9067", "offerId": "2164099825349836800", "totalPrice": 100, "currency": "CNY"},
        {"flights": "TG401", "offerId": "2164099825349836820", "totalPrice": 110, "currency": "CNY"},
        {"flights": "SQ8617", "offerId": "2164099825349836840", "totalPrice": 120, "currency": "CNY"},
    ]
    return {
        "traceId": "t1",
        "directOptions": options,
        "directLowest": options[0],
        "transferLowest": {"flights": "CX123", "offerId": "999", "totalPrice": 90, "currency": "CNY"},
    }


def main() -> int:
    errors: list[str] = []

    from offer_select import (  # noqa: E402
        apply_offer_selection,
        load_booking_context,
        resolve_offer_selection,
        save_booking_context,
    )
    from skill_search_client import select_offer  # noqa: E402

    ctx = _sample_context()

    selected, key, err = resolve_offer_selection(ctx, index=3)
    if err or not selected:
        errors.append(f"index=3 failed: {err}")
    elif selected.get("flights") != "SQ8617":
        errors.append(f"index=3 expected SQ8617, got {selected.get('flights')}")
    elif key != "direct-index-3":
        errors.append(f"index=3 key expected direct-index-3, got {key}")

    selected, key, err = resolve_offer_selection(ctx, offer_id="2164099825349836840")
    if err or selected.get("flights") != "SQ8617":
        errors.append(f"offer-id failed: {err} {selected}")

    selected, key, err = resolve_offer_selection(ctx, flight="SQ8617")
    if err or selected.get("offerId") != "2164099825349836840":
        errors.append(f"flight failed: {err} {selected}")

    selected, key, err = resolve_offer_selection(ctx, pick="direct-lowest")
    if err or selected.get("flights") != "LX9067":
        errors.append(f"pick direct-lowest failed: {err} {selected}")

    selected, key, err = resolve_offer_selection(ctx, pick="transfer")
    if err or selected.get("offerId") != "999":
        errors.append(f"pick transfer failed: {err} {selected}")

    _, _, err = resolve_offer_selection(ctx, index=99)
    if not err:
        errors.append("index=99 should fail")

    _, _, err = resolve_offer_selection(ctx, index=1, offer_id="x")
    if not err or "一种选择方式" not in err:
        errors.append(f"multiple selectors should fail: {err}")

    updated = apply_offer_selection(ctx, ctx["directOptions"][2], "direct-index-3")
    if updated.get("selectedOffer", {}).get("flights") != "SQ8617":
        errors.append("apply_offer_selection failed")

    with tempfile.TemporaryDirectory() as tmp:
        ctx_path = Path(tmp) / "booking_context.json"
        save_booking_context(ctx, ctx_path)
        loaded = load_booking_context(ctx_path)
        if len(loaded.get("directOptions") or []) != 3:
            errors.append("save/load context failed")

        out = select_offer(index=3, context_file=ctx_path)
        if out.get("status") != "success" or out.get("action") != "select":
            errors.append(f"select_offer CLI envelope: {out.get('status')} {out.get('action')}")
        uv = out.get("userView") or {}
        if (uv.get("selectedOffer") or {}).get("quoteId") != "2164099825349836840":
            errors.append(f"select userView quoteId: {uv}")
        saved = json.loads(ctx_path.read_text(encoding="utf-8"))
        if saved.get("selectedOffer", {}).get("flights") != "SQ8617":
            errors.append("select did not persist selectedOffer")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "tests": 10}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
