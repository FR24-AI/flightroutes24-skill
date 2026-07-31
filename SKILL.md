---
name: fr24-ai
description: "Flightroutes24 航路国际机票（FR24-AI，作者 FR24）。查价 POST /ai/shopping/v2（需采购密钥）；如需预订请联系工作人员：181xxxx888。触发词：查航班、搜机票、飞。Keywords: flight search, search flights, air ticket, check fare, flight price, international flight, one-way, round trip."
homepage: https://www.flightroutes24.com/
metadata: {"openclaw": {"emoji": "✈️", "primaryEnv": "FR_NEWAPI_APPKEY", "homepage": "https://www.flightroutes24.com/", "requires": {"anyBins": ["python3", "python"]}, "envVars": [{"name": "FR_NEWAPI_APPKEY", "required": false, "description": "采购 APPKEY（演示模式无需配置）"}, {"name": "FR_NEWAPI_SIGN_SECRET", "required": false, "description": "SHA512 签名密钥（采购模式）"}]}}
---

# FR24-AI · fr24-ai

| 项 | 说明 |
|----|------|
| 项目 | FR24-AI |
| Skill | `fr24-ai` |
| 产品 | Flightroutes24 航路国际机票 |
| 作者 | FR24 |

安装与配置见 **[INSTALL.md](./INSTALL.md)**。  
对用户展示与下载见 **[references/output-rules.md](./references/output-rules.md)**。  
用户询问采购密钥配置时，仅按 **[references/user-appkey-config.md](./references/user-appkey-config.md)** 回答。

---

## 语言策略 / Language Policy

- 用户使用中文时，全程中文回复。
- When the user writes in English, respond entirely in English throughout the conversation.
- `refine` supports English time keywords (morning / afternoon / evening / nonstop) and English airline names (Air China / China Eastern …).

---

## 服务模式

| 模式 | 条件 | 接口 |
|------|------|------|
| 查价 | 需配置 APPKEY 与签名密钥（未配置返回 `307904`） | `POST /ai/shopping/v2`，请求头 `appkey`，请求体 `authentication` |

> **演示版本**：本版本仅支持查价。需要下单或完整体验 AI 自动报价功能的，可以联系我们的工作人员 **181xxxx888** 协助 ✈️

---

## 响应结构

脚本标准输出为 JSON，包含：

```json
{
  "skill": "fr24-ai",
  "status": "success|failure",
  "action": "parse|search|refine",
  "message": "给用户看的摘要",
  "userView": {},
  "agentOnly": {}
}
```

| 字段 | 用途 |
|------|------|
| `userView`、`message` | **唯一**可对用户展示、制表、下载的内容 |
| `agentOnly` | 仅 Agent 内部续跑（如 `payload`、`traceId`），不得写入用户可见材料 |

---

## OpenClaw 适配（必读）

本 Skill 的 `SKILL.md` frontmatter 含 `metadata.openclaw`，安装路径通常为 `{baseDir}`（如 `/root/.openclaw/skills/fr24-ai`）。OpenClaw Agent **必须执行脚本**，不得自行推断行程或手写 `pending_search.json`。

### 启动与初始化

1. **首次查价/解析前**：`parse` / `build` 会自动生成 `clientKey`（写入 `{baseDir}/.cache/skill_client.json`），无需单独记忆 `ensure-key`；维护者自检仍可执行 `skill_search_client.py ensure-key`。
2. **Python**：需满足 `metadata.openclaw.requires.anyBins`（`python3` 或 `python`）。
3. **采购密钥**：通过环境变量 `FR_NEWAPI_APPKEY` 等配置；OpenClaw 以 `primaryEnv: FR_NEWAPI_APPKEY` 识别。环境变量优先级高于 `.cache/keys.json`。

### 查价流程（OpenClaw）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `cd {baseDir} && python3 scripts/nl_to_search.py parse --text "..."` | **必须**执行；stdout 为 JSON，只向用户展示 `userView` |
| 2 | 等待用户确认 | 禁止未确认即搜索 |
| 3 | `python3 scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json` | 用户确认后执行 |

- 用户从列表选「第 N 条」时：**`select --index N`**，**禁止**再 `search`。
- 输入已是 **IATA 三字码**（如 YYC、PEK）时，**不会**调用 `/ai/place/resolve`，属正常设计。
- 输入为 **中文/英文城市名** 时，脚本自动调 export 地名接口（请求头 `gray: ww`）。

### 禁止行为

- 禁止 Agent 手算日期、手写 intent 却不跑 `build --intent-file`
- 禁止跳过脚本直接展示报价
- 禁止向用户展示 `agentOnly`、`.cache` 路径或整段 stdout

---

## 查价流程

> **前提**：搜索接口（v2）需要采购密钥。若返回 `307904`（请提供采购认证信息），说明尚未配置采购密钥，请先按「采购密钥」章节完成配置，再重试搜索。

> **强制要求**：每次用户发起查价（含重新搜索、修改条件后搜索），**必须重新执行搜索脚本**，不得直接展示对话历史中的旧搜索结果。

> **绝对禁止**：无论何种输入格式，**严禁自行手动构造 payload JSON 写入 `.cache/pending_search.json` 或其他缓存文件**。所有行程解析必须通过 `nl_to_search.py parse` 或 `nl_to_search.py build --intent-file` 命令执行。

### 步骤 0：判断输入类型（必须先做）

收到用户搜索请求后，**先判断输入是自然语言还是 GDS/PNR 格式**：

- **GDS/PNR 格式**：输入中含有形如 `SS WS221 V 01JUL YWGYYC NN2` 的航段行 → **走下方「GDS 格式」分支，禁止走自然语言 `parse --text` 路径**
- **自然语言**：中文/英文描述行程（如"北京飞曼谷 7月1日"） → 走步骤 1

### 自然语言路径

1. **解析**：`{baseDir}/scripts/nl_to_search.py parse --text "..."`  
   → 展示 `userView`，**等待用户确认**行程、日期、人数、舱位后，才能执行步骤 2。
2. **搜索**：用户确认后执行  
   `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json`  
   → 按 **[output-rules.md](./references/output-rules.md)** 以**纯文本分行格式**展示，**顺序固定：先列完所有直飞，再列中转**。
   → `userView.directOptions` 有多少条展示多少条，**不得截断**，每条独占多行。
   → 每条必须包含：序号①②③、航班号、完整航线、各段起降时间（跨日注"次日"）、价格、**实际退改规则**、行李（每段）、**完整报价ID**（不得截断）。
   → 搜索结果末尾展示：**需要下单或完整体验 AI 自动报价功能的，可以联系我们的工作人员 181xxxx888 协助 ✈️**
3. 禁止将整段 stdout、`agentOnly` 或 `.cache` 路径直接提供给用户。

### GDS/PNR 格式路径

**严禁跳过脚本自行解析 GDS 并手动构造 payload。** 必须严格按以下步骤执行：

1. **构造 intent 文件**：从 GDS 行提取出发地、目的地、日期、人数，将原始 GDS 航段行整体放入 `gdsText` 字段，用 Agent 工具写成临时 intent JSON 文件。  
   → intent 格式（以 `SS WS221 V 01JUL YWGYYC NN2` 为例）：  
   ```json
   {
     "tripType": "OW",
     "legs": [{"originText": "YWG", "destinationText": "YYC", "depDateText": "2026-07-01"}],
     "passengers": {"adult": 2},
     "gdsText": "SS WS221 V 01JUL YWGYYC NN2"
   }
   ```

2. **执行解析脚本**：  
   `{baseDir}/scripts/nl_to_search.py build --intent-file <intent文件路径>`

3. **确认**：展示 `userView.intentSummary`，**等待用户确认**行程信息无误。**禁止在用户确认前执行搜索**。

4. **搜索**：用户确认后执行  
   `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json`

---

## 条件调整与重新搜索

用户对结果不满意并提出**航司**、**具体航班号**或**起飞时段**时：

1. 须**重新搜索**。
2. `{baseDir}/scripts/nl_to_search.py refine --text "<用户要求>"`（不扣配额，更新 `{baseDir}/.cache/pending_search.json`）。
3. 向用户确认更新后的 `userView`。
4. 再次执行 `search`。

---

## 如需预订

> **本演示版本不支持在线预订。**  
> 用户有预订意向时，直接告知：**需要下单或完整体验 AI 自动报价功能的，可以联系我们的工作人员 181xxxx888 协助 ✈️**  
> 禁止引导用户提供乘客证件信息、联系人信息或任何预订相关内容。

---

## 采购密钥（用户询问时）/ Procurement Keys (when user asks)

仅依据 [user-appkey-config.md](./references/user-appkey-config.md)：

- 引导用户在 [航路官网](https://www.flightroutes24.com/) 开通 API 采购；
- 在本机用户环境变量中配置 APPKEY、签名密钥；
- 配置后重启 Agent 客户端。

For English users: guide them to register at [Flightroutes24](https://www.flightroutes24.com/), activate API procurement, and configure keys locally per [user-appkey-config.md](./references/user-appkey-config.md).

---

## 命令一览

| 命令 | 说明 |
|------|------|
| `{baseDir}/scripts/nl_to_search.py parse --text "..."` | 解析行程（自然语言） |
| `{baseDir}/scripts/nl_to_search.py build --intent-file <文件>` | 解析行程（GDS/PNR，intent JSON 含 `gdsText` 字段） |
| `{baseDir}/scripts/nl_to_search.py refine --text "..."` | 合并航司、起飞时段等条件 |
| `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json` | 搜索（v2，默认不自动选价） |
| `{baseDir}/scripts/skill_search_client.py select --index 3` | 从缓存选第 3 条直飞（不重搜，仅用于用户想了解报价详情） |
| `{baseDir}/scripts/skill_search_client.py select --offer-id <id>` / `--flight SQ8617` / `--pick transfer` | 按报价ID、航班号或类别查看报价 |
| `{baseDir}/scripts/config_keys.py set --appkey ... --sign-secret ...` | 配置采购密钥 |
| `{baseDir}/scripts/config_keys.py status` | 查看配置状态 |
| `{baseDir}/scripts/config_keys.py clear` | 清除本地密钥配置 |

---

## 业务限制 / Business Constraints

- 支持单程、往返；不支持多段缺口程。/ Supports one-way and round-trip; multi-city itineraries are not supported.
- 搜索接口（v2）必须配置采购密钥；未配置时返回 `307904`，应引导用户按「采购密钥」章节完成配置。
- **本演示版本仅提供查价服务，不支持在线预订。需要下单或完整体验 AI 自动报价功能的，可以联系我们的工作人员 181xxxx888 协助 ✈️**  
  This demo version supports fare search only. To place a booking or experience the full AI fare search service, please contact our staff at 181xxxx888 ✈️
