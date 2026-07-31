"""Skill 配置（Skill 搜索）。"""
from __future__ import annotations

import json
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
CACHE_DIR = SKILL_DIR / ".cache"
CLIENT_KEY_FILE = CACHE_DIR / "skill_client.json"
PENDING_PAYLOAD_FILE = CACHE_DIR / "pending_search.json"
BOOKING_CONTEXT_FILE = CACHE_DIR / "booking_context.json"
KEYS_FILE = CACHE_DIR / "keys.json"
ENV_FILE = SKILL_DIR / ".env"

CLIENT_KEY_HEADER = "X-Skill-Client-Key"
DAILY_LIMIT = 10

# 项目与 Skill 标识（对外信封、安装目录名）
PROJECT_NAME = "FR24-AI"
SKILL_ID = "fr24-ai"
SKILL_DISPLAY_NAME = "Flightroutes24航路国际机票"
SKILL_AUTHOR = "FR24"

# --- export 网关（项目内固定；切换环境请直接改此处，勿使用 skill.local.env）---
EXPORT_BASE_URL = "https://flight-deve.flightroutes24.com"
GRAY_HEADER = "ww"

SHOPPING_V2_PATH = "/ai/shopping/v2"
PLACE_RESOLVE_PATH = "/ai/place/resolve"
PLACE_RESOLVE_BATCH_PATH = "/ai/place/resolve/batch"


# ---------------------------------------------------------------------------
# 多源配置读取：环境变量 > .env 文件 > .cache/keys.json
# ---------------------------------------------------------------------------

_ENV_TO_JSON_KEYS = {
    "FR_NEWAPI_APPKEY": "appkey",
    "FR_NEWAPI_SIGN_SECRET": "signSecret",
    "FR_NEWAPI_SKIP_AUTH": "skipAuth",
    "FR_NEWAPI_SKIP_IP_WHITELIST": "skipIpWhitelist",
}

_dotenv_cache: dict[str, str] | None = None
_keys_json_cache: dict[str, str] | None = None


def _load_dotenv() -> dict[str, str]:
    """解析 .env 文件（KEY=VALUE，忽略 # 注释和空行）。"""
    global _dotenv_cache
    if _dotenv_cache is not None:
        return _dotenv_cache
    result: dict[str, str] = {}
    if not ENV_FILE.is_file():
        _dotenv_cache = result
        return result
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("\"'")
    _dotenv_cache = result
    return result


def _load_keys_json() -> dict[str, str]:
    """读取 .cache/keys.json。"""
    global _keys_json_cache
    if _keys_json_cache is not None:
        return _keys_json_cache
    result: dict[str, str] = {}
    if KEYS_FILE.is_file():
        try:
            data = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                result = {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
    _keys_json_cache = result
    return result


def _read_config(env_name: str, default: str = "") -> str:
    """按优先级读取配置：环境变量 > .env 文件 > .cache/keys.json。"""
    # 1. 环境变量（最高优先级）
    val = os.environ.get(env_name, "").strip()
    if val:
        return val
    # 2. .env 文件
    json_key = _ENV_TO_JSON_KEYS.get(env_name, env_name)
    val = _load_dotenv().get(env_name, "").strip()
    if val:
        return val
    # 3. .cache/keys.json
    val = _load_keys_json().get(json_key, "").strip()
    if val:
        return val
    return default


def _read_config_bool(env_name: str) -> bool:
    """读取布尔配置（字符串 '1'/'true'/'yes' 视为 True）。"""
    return _read_config(env_name).lower() in ("1", "true", "yes")


def reload_config() -> None:
    """清除内部缓存，下次读取时重新加载 .env 和 keys.json。"""
    global _dotenv_cache, _keys_json_cache
    _dotenv_cache = None
    _keys_json_cache = None


# NewApi 采购密钥（支持多源读取，勿写入仓库）
NEWAPI_APP_KEY = _read_config("FR_NEWAPI_APPKEY")
NEWAPI_SIGN_SECRET = _read_config("FR_NEWAPI_SIGN_SECRET")
NEWAPI_SKIP_AUTH = _read_config_bool("FR_NEWAPI_SKIP_AUTH")
NEWAPI_SKIP_IP_WHITELIST = _read_config_bool("FR_NEWAPI_SKIP_IP_WHITELIST")
FR24_API_HEADER = "fr24-api"

REGISTER_PORTAL_URL = "https://www.flightroutes24.com/"

CONTACT_PHONE = "181xxxx888"

CONTACT_MESSAGE = f"如需预订，请联系我们的工作人员：{CONTACT_PHONE}"

CONTACT_MESSAGE_EN = f"To place a booking, please contact our staff: {CONTACT_PHONE}"

USER_SKILL_QUOTA_EXCEEDED_MESSAGE = (
    f"搜索失败，请确认采购密钥已正确配置。"
    f"若尚未开通采购，请打开 {REGISTER_PORTAL_URL} 注册并开通 API 采购，"
    f"取得采购 APPKEY 后在本机完成密钥配置。"
    f"询问「如何配置 appkey」可查看配置步骤。"
)

USER_SKILL_QUOTA_EXCEEDED_MESSAGE_EN = (
    f"Search failed. Please verify your procurement keys are correctly configured. "
    f"If you haven't activated procurement yet, please register at {REGISTER_PORTAL_URL}. "
    f"Ask 'how to configure appkey' for setup instructions."
)


def is_newapi_configured() -> bool:
    if not NEWAPI_APP_KEY:
        return False
    if NEWAPI_SKIP_AUTH:
        return True
    return bool(NEWAPI_SIGN_SECRET)
