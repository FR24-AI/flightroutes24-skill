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
> **对用户展示与下载**见 **[references/output-rules.md](./references/output-rules.md)**（仅用 `userView`，勿暴露 `agentOnly`）。  
> **用户问如何配置 appkey** → 只读 **[references/user-appkey-config.md](./references/user-appkey-config.md)**。  
> 维护者联调见 **[references/setup-maintainer.md](./references/setup-maintainer.md)**（**禁止**对用户展示或口述）。

## 双模式

| 模式 | 条件 | 搜索接口 |
|------|------|----------|
| Skill 演示 | 未配置采购密钥 | `/api/skill/shopping` + `X-Skill-Client-Key`（默认 CID + 日配额） |
| Skill 采购 | 已配置 APPKEY + 签名 | 同上，请求体带 `authentication` + 头 `appkey`（无日配额） |
| 预订 | 已配置 APPKEY + 签名 + AES | `/api/new/pricing`、`/api/new/booking` |

依赖：`pip install -r requirements.txt`（预订需要）。网关与密钥由维护者在本地配置，**不要**向用户念出环境变量名或联调开关。

## 输出 JSON 信封

```json
{
  "skill": "fr-newapi-search",
  "status": "success|failure",
  "action": "parse|search|parse-passengers|verify|order",
  "message": "给用户看的摘要",
  "userView": {},
  "agentOnly": {}
}
```

- **`userView`**：表格、聊天、附件、下载文件**只能**用此字段（见 output-rules.md）
- **`agentOnly`**：含 `traceId`、`payload`、`offerId` 等，**禁止**写入用户下载物
- 续跑命令、`.cache/` 读写：Agent 读 `agentOnly`，勿把其内容展示给用户

## 查价流程

1. `nl_to_search.py parse --text "..."`（不扣配额）→ 用 **`userView`** 向用户确认行程
2. 用户确认后 `skill_search_client.py search --payload-file .cache/pending_search.json --selection direct|transfer`
3. 用 **`userView.directLowest` / `transferLowest`** 展示报价（含退改、行李），勿 dump 整段 stdout

## 预订流程（必须遵守）

与 `fr_newapi_flight_mcp` 一致，**两次用户确认**：

1. 用户选择 **直飞/中转** → `search --selection ...`
2. `skill_booking_client.py parse-passengers --text "..."` → 展示 **passengerDisplay** 字段对照（示例姓名：**张三**）
3. 用户：**「乘客信息确认无误」** → `verify --passenger-confirmed`
4. 展示 **orderPreview**（行程、退改、乘客回显）→ 用户：**「确认生单」**
5. `order --user-confirmed`

禁止：未确认乘客就 verify；未确认就 order；向用户展示联调环境变量、`setup-maintainer.md` 内容或演示乘客自动填充。

## 用户问「如何配置 appkey / 采购密钥」（必须遵守）

1. **只按** [references/user-appkey-config.md](./references/user-appkey-config.md) 回答（Windows 用户环境变量 + 重启 Claude Code + 本机验证命令）。
2. **禁止**提及或写出：`FR_NEWAPI_SKIP_IP_WHITELIST`、`FR_NEWAPI_SKIP_AUTH`、跳过 IP 白名单、跳过签名验证、deve 联调专用说明。
3. **禁止**让用户在对话里发送 APPKEY / 签名密钥 / AES 密钥明文；只引导用户在本机配置。
4. 维护者才需要联调开关时，Agent **自行**读 `setup-maintainer.md`，**不得**把其中内容复述给用户。

## 命令速查

| 命令 | 说明 |
|------|------|
| `scripts/nl_to_search.py parse --text "..."` | 解析行程 |
| `scripts/skill_search_client.py search --payload-file .cache/pending_search.json` | 搜索 |
| `scripts/skill_booking_client.py parse-passengers --text "..."` | 乘客核对 |
| `scripts/skill_booking_client.py verify --passenger-confirmed` | 校验 |
| `scripts/skill_booking_client.py order --user-confirmed` | 生单 |

维护者：`python scripts/validate_user_output.py`（输出规范校验）、`scripts/nl_scenario_test.py`；配置见 `references/setup-maintainer.md`（勿对用户提及）。

## 限制

- 单程/往返；Skill 搜索每日 10 次/clientKey
- 结果展示：直飞最低 + 中转最低（退改、行李见 `userView`）
- 禁止：整段 stdout / `agentOnly` / `.cache` / 联调配置说明 作为用户可见内容
- 生单为真实订单，须用户确认后提交
