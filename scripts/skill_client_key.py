"""Skill 客户端密钥（clientKey）读写，供搜索/地名解析等模块共用。"""
from __future__ import annotations

import json
import secrets
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_SCRIPTS = Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import CACHE_DIR, CLIENT_KEY_FILE  # noqa: E402

BJ = ZoneInfo("Asia/Shanghai")


def ensure_client_key() -> str:
    """读取或生成 clientKey（OpenClaw 首次解析/搜索前自动调用）。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if CLIENT_KEY_FILE.is_file():
        data = json.loads(CLIENT_KEY_FILE.read_text(encoding="utf-8"))
        key = str(data.get("clientKey") or "")
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
