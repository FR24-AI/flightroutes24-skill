"""Skill 配置（Skill 搜索 + NewApi 预订）。"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
LOCAL_ENV_FILE = SKILL_DIR / "skill.local.env"


# skill.local.env 仅允许网关项；采购 CID/密钥必须走环境变量
_LOCAL_ENV_ALLOWED_KEYS = frozenset(
    {"FR_SKILL_EXPORT_BASE_URL", "FR_SKILL_GRAY_HEADER"},
)


def _load_skill_local_env() -> None:
    """加载 skill.local.env（仅网关；不覆盖已有环境变量；忽略 FR_NEWAPI_*）。"""
    if not LOCAL_ENV_FILE.is_file():
        return
    for raw in LOCAL_ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key not in _LOCAL_ENV_ALLOWED_KEYS:
            continue
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_skill_local_env()
CACHE_DIR = SKILL_DIR / ".cache"
CLIENT_KEY_FILE = CACHE_DIR / "skill_client.json"
PENDING_PAYLOAD_FILE = CACHE_DIR / "pending_search.json"
BOOKING_CONTEXT_FILE = CACHE_DIR / "booking_context.json"
PASSENGERS_FILE = CACHE_DIR / "passengers.json"

CLIENT_KEY_HEADER = "X-Skill-Client-Key"
DAILY_LIMIT = 10

# export 根地址（deve 默认）
EXPORT_BASE_URL = os.environ.get(
    "FR_SKILL_EXPORT_BASE_URL",
    "https://flight-deve.flightroutes24.com",
).rstrip("/")

SHOPPING_PATH = "/api/skill/shopping"
NEWAPI_SHOPPING_PATH = "/api/new/shopping"
PRICING_PATH = "/api/new/pricing"
BOOKING_PATH = "/api/new/booking"

GRAY_HEADER = os.environ.get("FR_SKILL_GRAY_HEADER", "").strip()
if not GRAY_HEADER and "deve." in EXPORT_BASE_URL:
    GRAY_HEADER = "ww"

# NewApi 采购密钥（环境变量，勿写入仓库）
NEWAPI_APP_KEY = os.environ.get("FR_NEWAPI_APPKEY", "").strip()
NEWAPI_SIGN_SECRET = os.environ.get("FR_NEWAPI_SIGN_SECRET", "").strip()
NEWAPI_AES_SECRET = os.environ.get("FR_NEWAPI_AES_SECRET", "").strip()
NEWAPI_SKIP_AUTH = os.environ.get("FR_NEWAPI_SKIP_AUTH", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
NEWAPI_SKIP_IP_WHITELIST = os.environ.get("FR_NEWAPI_SKIP_IP_WHITELIST", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
FR24_API_HEADER = "fr24-api"

REGISTER_PORTAL_URL = "https://www.flightroutes24.com/"

USER_BOOKING_USER_MESSAGE = (
    f"当前为演示查价。若要预订，请打开 {REGISTER_PORTAL_URL} 注册并开通 API 采购，"
    f"由管理员在本机配置采购密钥后，再按预订流程提供乘客信息。"
)

USER_BOOKING_AGENT_HINT = (
    "维护者：配置 FR_NEWAPI_APPKEY、FR_NEWAPI_SIGN_SECRET、FR_NEWAPI_AES_SECRET；"
    "联调见 references/setup-maintainer.md（勿展示给用户）。"
)

BOOKING_CONFIG_HINT = USER_BOOKING_AGENT_HINT

SEARCH_ONLY_HINT = "（仅查价）当前未开通采购预订；注册并配置密钥后可继续预订。"


def is_newapi_configured() -> bool:
    if not NEWAPI_APP_KEY:
        return False
    if NEWAPI_SKIP_AUTH:
        return True
    return bool(NEWAPI_SIGN_SECRET)


def is_booking_ready() -> bool:
    if not is_newapi_configured():
        return False
    return bool(NEWAPI_AES_SECRET)


def booking_required_payload(step: str = "booking") -> dict:
    return {
        "code": "CONFIG_REQUIRED",
        "success": False,
        "step": step,
        "registerPortalUrl": REGISTER_PORTAL_URL,
        "message": USER_BOOKING_USER_MESSAGE,
        "bookingConfigHint": USER_BOOKING_AGENT_HINT,
    }


def booking_config_required_envelope(action: str, step: str = "booking") -> dict:
    """未配置采购密钥时，统一返回注册/申请引导（含 registerPortalUrl）。"""
    data = booking_required_payload(step=step)
    return {
        "skill": "fr-newapi-search",
        "status": "failure",
        "action": action,
        "data": data,
        "message": data["message"],
    }
