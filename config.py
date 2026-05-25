"""Skill 配置（Skill 搜索 + NewApi 预订）。"""
from __future__ import annotations

import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
CACHE_DIR = SKILL_DIR / ".cache"
CLIENT_KEY_FILE = CACHE_DIR / "skill_client.json"
PENDING_PAYLOAD_FILE = CACHE_DIR / "pending_search.json"
BOOKING_CONTEXT_FILE = CACHE_DIR / "booking_context.json"
PASSENGERS_FILE = CACHE_DIR / "passengers.json"

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

SHOPPING_PATH = "/ai/shopping"
NEWAPI_SHOPPING_PATH = "/api/new/shopping"
PRICING_PATH = "/api/new/pricing"
BOOKING_PATH = "/api/new/booking"

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

USER_SKILL_QUOTA_EXCEEDED_MESSAGE = (
    f"今日演示查价次数已用完（每日 {DAILY_LIMIT} 次）。"
    f"若要继续查询，请打开 {REGISTER_PORTAL_URL} 注册并开通 API 采购，"
    f"取得采购 APPKEY 后在本机完成密钥配置并重启 Claude Code，"
    f"之后将使用您的采购账号搜索（不受演示日限额）。"
    f"询问「如何配置 appkey」可查看配置步骤。"
)


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
        "skill": SKILL_ID,
        "status": "failure",
        "action": action,
        "data": data,
        "message": data["message"],
    }
