#!/usr/bin/env python3
"""多人搜索/证件解析与人数一致性自检。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
for p in (_SCRIPTS, _ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def main() -> int:
    errors: list[str] = []

    from passenger_count import count_passengers_by_type, validate_passengers_match_search  # noqa: E402
    from passenger_parser import parse_passengers  # noqa: E402
    from pax_info_parser import parse_passengers_and_contact  # noqa: E402

    if parse_passengers("两位成人")["adultNum"] != 2:
        errors.append("两位成人 parse failed")
    if parse_passengers("2位成人")["adultNum"] != 2:
        errors.append("2位成人 parse failed")
    if parse_passengers("十一成人")["adultNum"] != 11:
        errors.append("十一成人 parse failed")
    if parse_passengers("1大1小")["childNum"] != 1:
        errors.append("1大1小 parse failed")

    two_labeled = (
        "成人：张三，男，1990-01-15，护照 E11111111，2030-12-31 到期，国籍 CN。\n"
        "成人：李四，男，1991-02-20，护照 E22222222，2031-06-30 到期，国籍 CN。\n"
        "联系人：张三，手机 13800138000，邮箱 zhangsan@example.com"
    )
    pax, contact, _, _, err = parse_passengers_and_contact(two_labeled)
    if err or len(pax) != 2:
        errors.append(f"two labeled adults failed: {err} len={len(pax)}")
    if contact is None:
        errors.append("two labeled adults missing contact")

    two_inline = (
        "张三 男 1990-01-15 护照 E11111111，2030-12-31 到期，国籍 CN。\n"
        "李四 男 1991-02-20 护照 E22222222，2031-06-30 到期，国籍 CN。\n"
        "联系人：张三，手机 13800138000，邮箱 zhangsan@example.com"
    )
    pax2, _, _, _, err2 = parse_passengers_and_contact(two_inline)
    if err2 or len(pax2) != 2:
        errors.append(f"two inline adults failed: {err2} len={len(pax2)}")

    family = (
        "成人：张三，男，1988-03-20，护照 G11111111，2031-06-30 到期，中国籍。\n"
        "成人：李四，男，1989-04-21，护照 G22222222，2031-06-30 到期，中国籍。\n"
        "儿童：张小三，男，2018-06-01，护照 G33333333，2031-06-30 到期，中国籍，与成人李四同行。\n"
        "联系人：张三，13800138000，zhangsan@example.com"
    )
    pax3, _, _, _, err3 = parse_passengers_and_contact(family)
    if err3 or len(pax3) != 3:
        errors.append(f"family parse failed: {err3}")
    else:
        child = next(p for p in pax3 if p["paxType"] == "CHD")
        if child.get("accompaniedPaxId") != "2":
            errors.append(f"child should accompany pax 2, got {child.get('accompaniedPaxId')}")

    counts = count_passengers_by_type(
        [{"paxType": "ADT"}, {"paxType": "ADT"}, {"paxType": "CHD"}]
    )
    if counts != {"adultNum": 2, "childNum": 1, "infantNum": 0}:
        errors.append(f"count_passengers_by_type: {counts}")

    mismatch = validate_passengers_match_search(
        [{"paxType": "ADT"}],
        {"adultNum": 2, "childNum": 0, "infantNum": 0},
    )
    if not mismatch or "成人2人" not in mismatch:
        errors.append(f"mismatch message unexpected: {mismatch}")

    ok = validate_passengers_match_search(
        [{"paxType": "ADT"}, {"paxType": "ADT"}],
        {"adultNum": 2, "childNum": 0, "infantNum": 0},
    )
    if ok is not None:
        errors.append(f"expected match ok, got {ok}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, "tests": 11}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
