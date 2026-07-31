"""export HTTP：Skill 搜索。"""
from __future__ import annotations

import gzip
import json
import secrets
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import hashlib
import time

from config import (  # noqa: E402
    CACHE_DIR,
    CLIENT_KEY_FILE,
    CLIENT_KEY_HEADER,
    EXPORT_BASE_URL,
    FR24_API_HEADER,
    GRAY_HEADER,
    NEWAPI_APP_KEY,
    NEWAPI_SIGN_SECRET,
    NEWAPI_SKIP_AUTH,
    NEWAPI_SKIP_IP_WHITELIST,
    SHOPPING_V2_PATH,
    is_newapi_configured,
)


def _sha512_sign(app_key: str, app_secret: str, timestamp: str) -> str:
    raw = f"{app_key}{app_secret}{timestamp}"
    return hashlib.sha512(raw.encode("utf-8")).hexdigest()


def _build_authentication(app_key: str, app_secret: str) -> dict[str, str]:
    ts = str(int(time.time()))
    return {"timestamp": ts, "sign": _sha512_sign(app_key, app_secret, ts)}

BJ = ZoneInfo("Asia/Shanghai")
SUCCESS_CODES = frozenset({"0", "000000"})


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


def _decompress_response(resp) -> bytes:
    """读取 HTTP 响应体，自动解压 gzip。"""
    data = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        data = gzip.decompress(data)
    return data


def _http_post(url: str, body: dict, headers: dict[str, str], timeout: int = 120) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(_decompress_response(resp).decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw_bytes = e.read()
        try:
            raw_bytes = gzip.decompress(raw_bytes)
        except Exception:
            pass
        raw = raw_bytes.decode("utf-8", errors="replace")
        if raw.strip():
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        return {"code": str(e.code), "message": raw or e.reason}
    except urllib.error.URLError as e:
        return {"code": "NETWORK_ERROR", "message": f"无法连接 {EXPORT_BASE_URL}：{e.reason}"}


def _strip_client_only_prefs(payload: dict) -> dict:
    """剔除仅客户端本地使用的 preferences 字段，避免后端 Jackson 解析报错。

    preferredFlightNo 用于客户端摘要阶段精确匹配/置顶，后端 ApiSearchPreferences
    不包含该字段，发送会导致 UnrecognizedPropertyException（HTTP 400）。
    """
    body = dict(payload)
    prefs = body.get("preferences")
    if isinstance(prefs, dict) and "preferredFlightNo" in prefs:
        body["preferences"] = {k: v for k, v in prefs.items() if k != "preferredFlightNo"}
    return body


def _require_newapi_secrets() -> str | None:
    if NEWAPI_SKIP_AUTH:
        return None if NEWAPI_APP_KEY else "未配置 FR_NEWAPI_APPKEY"
    if not NEWAPI_APP_KEY:
        return "未配置 FR_NEWAPI_APPKEY"
    if not NEWAPI_SIGN_SECRET:
        return "未配置 FR_NEWAPI_SIGN_SECRET"
    return None


def _attach_auth(body: dict[str, Any]) -> dict[str, Any]:
    payload = dict(body)
    if not NEWAPI_SKIP_AUTH:
        payload["authentication"] = _build_authentication(NEWAPI_APP_KEY, NEWAPI_SIGN_SECRET)
    return payload


def skill_shopping_v2(payload: dict) -> dict:
    """走 /ai/shopping/v2：直飞按航班号去重后各取最低价（最多 N 条），中转取一条最低价。"""
    key = ensure_client_key()
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        CLIENT_KEY_HEADER: key,
    }
    body: dict = _strip_client_only_prefs(payload)
    if is_newapi_configured():
        err = _require_newapi_secrets()
        if err:
            return {"code": "CONFIG_REQUIRED", "message": f"采购密钥配置错误：{err}"}
        headers["appkey"] = NEWAPI_APP_KEY
        headers["Accept-Encoding"] = "gzip"
        if NEWAPI_SKIP_AUTH:
            headers["fr24-skip-auth"] = "1"
        if NEWAPI_SKIP_IP_WHITELIST:
            headers[FR24_API_HEADER] = "1"
        body = _attach_auth(body)
    if GRAY_HEADER:
        headers["gray"] = GRAY_HEADER
    return _http_post(EXPORT_BASE_URL + SHOPPING_V2_PATH, body, headers)


def run_search_v2(payload: dict) -> tuple[dict, str]:
    """v2 搜索：直飞按航班号去重，每航班号取最低价，最多 N 条。"""
    mode = "skill-auth" if is_newapi_configured() else "skill"
    return skill_shopping_v2(payload), mode
