---
name: fr-newapi-search
description: >
  航路国际机票 Skill（纯脚本，无 MCP）。Skill 查价 POST /api/skill/shopping；
  配置 FR_NEWAPI_* 后支持 NewApi 搜索/校验/生单。触发词：查航班、搜机票、预订、生单、飞。
metadata:
  openclaw:
    emoji: "✈️"
    requires: {}
    install: []
---

# NewAPI 航班搜索与预订 Skill（无 MCP）

> 安装见 **[INSTALL.md](./INSTALL.md)**。预订流程见 **[references/booking.md](./references/booking.md)**。

## 双模式

| 模式 | 条件 | 搜索接口 |
|------|------|----------|
| Skill 演示 | 未配置 `FR_NEWAPI_APPKEY` | `/api/skill/shopping` + `X-Skill-Client-Key`（默认 CID + 日配额，exportConf 可配） |
| Skill 采购 | 已配置 APPKEY + 签名 | 同上，请求体带 `authentication` + 头 `appkey`（无日配额） |
| 预订 | 已配置 APPKEY + 签名 + AES | `/api/new/pricing`、`/api/new/booking` |

## 环境

```bash
set FR_SKILL_EXPORT_BASE_URL=https://flight-deve.flightroutes24.com
set FR_SKILL_GRAY_HEADER=ww
# 预订可选：
set FR_NEWAPI_APPKEY=FRG
set FR_NEWAPI_SIGN_SECRET=...
set FR_NEWAPI_AES_SECRET=...
set FR_NEWAPI_SKIP_IP_WHITELIST=1
```

依赖：`pip install -r requirements.txt`

## 输出 JSON 信封

```json
{
  "skill": "fr-newapi-search",
  "status": "success|failure",
  "action": "parse|search|parse-passengers|verify|order",
  "data": {},
  "message": "说明"
}
```

## 查价流程

1. `nl_to_search.py parse --text "..."`（不扣配额）
2. 向用户确认 `intentSummary`
3. `skill_search_client.py search --payload-file .cache/pending_search.json --selection direct|transfer`

## 预订流程（必须遵守）

与 `fr_newapi_flight_mcp` 一致，**两次用户确认**：

1. 用户选择 **直飞/中转** → `search --selection ...`
2. `skill_booking_client.py parse-passengers --text "..."` → 展示 **passengerDisplay** 字段对照
3. 用户：**「乘客信息确认无误」** → `verify --passenger-confirmed`
4. 展示 **orderPreview**（行程、退改、乘客回显）→ 用户：**「确认生单」**
5. `order --user-confirmed`

禁止：未确认乘客就 verify；未确认就 order；擅自用演示乘客（除非 `FR_BOOKING_TEST_ORDER` 联调）。

## 命令速查

| 命令 | 说明 |
|------|------|
| `scripts/nl_to_search.py parse --text "..."` | 解析行程 |
| `scripts/skill_search_client.py search --payload-file .cache/pending_search.json` | 搜索 |
| `scripts/skill_booking_client.py parse-passengers --text "..."` | 乘客核对 |
| `scripts/skill_booking_client.py verify --passenger-confirmed` | 校验 |
| `scripts/skill_booking_client.py order --user-confirmed` | 生单 |
| `scripts/booking_flow_test.py` | 全流程联调 |
| `scripts/nl_scenario_test.py` | 解析场景回归 |

## 限制

- 单程/往返；Skill 搜索每日 10 次/clientKey
- 结果展示：直飞最低 + 中转最低
- 生单为真实订单（deve 亦需谨慎）
