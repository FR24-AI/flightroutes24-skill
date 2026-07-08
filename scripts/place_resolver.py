"""地名 -> IATA 三字码（优先 export /ai/place/resolve，降级 places.json）。"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

PLACES_FILE = Path(__file__).resolve().parent.parent / "references" / "places.json"
IATA_RE = re.compile(r"^[A-Za-z]{3}$")
_SUCCESS_CODES = frozenset({"0", "000000"})


def _skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_export_config():
    root = _skill_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from config import (  # noqa: WPS433
        CLIENT_KEY_FILE,
        CLIENT_KEY_HEADER,
        EXPORT_BASE_URL,
        GRAY_HEADER,
        PLACE_RESOLVE_PATH,
    )

    return EXPORT_BASE_URL, PLACE_RESOLVE_PATH, CLIENT_KEY_HEADER, CLIENT_KEY_FILE, GRAY_HEADER


def load_places() -> dict[str, str]:
    with PLACES_FILE.open(encoding="utf-8") as f:
        raw = json.load(f)
    return {k.strip().lower(): v.upper() for k, v in raw.items()}


def _ensure_client_key(client_key_file: Path) -> str:
    if client_key_file.is_file():
        data = json.loads(client_key_file.read_text(encoding="utf-8"))
        key = str(data.get("clientKey") or "")
        if len(key) >= 32:
            return key
    raise RuntimeError("clientKey not ready")


def _resolve_via_export_api(text: str, *, language: str = "zh_CN") -> dict | None:
    if os.environ.get("FR_PLACE_RESOLVE_OFF", "").strip().lower() in ("1", "true", "yes"):
        return None
    try:
        base_url, path, header_name, client_key_file, gray_header = _load_export_config()
        client_key = _ensure_client_key(client_key_file)
        url = f"{base_url.rstrip('/')}{path}"
        body = json.dumps({"text": text, "language": language, "searchType": 0, "limit": 5}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                header_name: client_key,
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "fr24-api": gray_header,
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if str(payload.get("code")) not in _SUCCESS_CODES:
            return None
        return payload.get("data") or None
    except (urllib.error.URLError, OSError, json.JSONDecodeError, RuntimeError, ValueError):
        return None


def resolve_place_detail(text: str, places: dict[str, str] | None = None) -> dict | None:
    """解析地名，返回 {code, codeType, chineseName, englishName} 或 None。"""
    if not text or not str(text).strip():
        return None
    t = str(text).strip()
    if IATA_RE.match(t):
        code = t.upper()
        return {"code": code, "codeType": "A", "chineseName": None, "englishName": None}
    api_data = _resolve_via_export_api(t)
    if api_data and api_data.get("best"):
        best = api_data["best"]
        code = best.get("code")
        if code:
            return {
                "code": str(code).upper(),
                "codeType": best.get("codeType") or "C",
                "chineseName": best.get("chineseName"),
                "englishName": best.get("englishName"),
            }
    table = places if places is not None else load_places()
    code = table.get(t.lower()) or table.get(t)
    if code:
        return {"code": code.upper(), "codeType": "C", "chineseName": None, "englishName": None}
    return None


def resolve_place(text: str, places: dict[str, str] | None = None) -> str | None:
    detail = resolve_place_detail(text, places)
    return detail.get("code") if detail else None


def resolve_place_required(text: str, label: str) -> tuple[str | None, str | None]:
    detail = resolve_place_detail(text)
    if detail and detail.get("code"):
        return detail["code"], None
    return None, f"无法识别{label}：{text}，请使用 IATA 三字码或常见城市名"
