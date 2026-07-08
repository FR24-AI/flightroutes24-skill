---
name: fr24-ai
description: "Flightroutes24 航路国际机票（FR24-AI，作者 FR24）。查价 POST /ai/shopping/v2（需采购密钥）；配置采购密钥后支持搜索、校验、生单。触发词：查航班、搜机票、预订、生单、飞。Keywords: flight search, search flights, book flight, book ticket, air ticket, check fare, flight price, buy ticket, international flight, one-way, round trip."
homepage: https://www.flightroutes24.com/
metadata: {"openclaw": {"emoji": "✈️", "primaryEnv": "FR_NEWAPI_APPKEY", "homepage": "https://www.flightroutes24.com/", "requires": {"anyBins": ["python3", "python"]}, "envVars": [{"name": "FR_NEWAPI_APPKEY", "required": false, "description": "采购 APPKEY（演示模式无需配置）"}, {"name": "FR_NEWAPI_SIGN_SECRET", "required": false, "description": "SHA512 签名密钥（采购模式）"}, {"name": "FR_NEWAPI_AES_SECRET", "required": false, "description": "16 字节 AES 密钥（预订功能）"}], "install": [{"id": "pip-deps", "kind": "uv", "args": ["pip", "install", "-r", "{baseDir}/requirements.txt"], "label": "Install Python deps (booking feature)"}]}}
---

# FR24-AI · fr24-ai

| 项 | 说明 |
|----|------|
| 项目 | FR24-AI |
| Skill | `fr24-ai` |
| 产品 | Flightroutes24 航路国际机票 |
| 作者 | FR24 |

安装与配置见 **[INSTALL.md](./INSTALL.md)**。预订细则见 **[references/booking.md](./references/booking.md)**。  
对用户展示与下载见 **[references/output-rules.md](./references/output-rules.md)**。  
用户询问采购密钥配置时，仅按 **[references/user-appkey-config.md](./references/user-appkey-config.md)** 回答。

---

## 语言策略 / Language Policy

- 用户使用中文时，全程中文回复。
- When the user writes in English, respond entirely in English throughout the conversation.
- Confirm phrases are accepted in **both languages**:
  - Passenger info confirmed: 「乘客信息确认无误」or **"passenger info confirmed"**
  - Place order: 「确认生单」or **"confirm order"**
- For English users, use "direct flight" / "connecting flight" instead of 直飞/中转, and "Quote ID" instead of 报价ID.
- Script output `userView.message` may contain Chinese labels — **do not copy them verbatim** when responding in English. Use `confirmPhraseEn` / `passengerConfirmPromptEn` / `orderConfirmPromptEn` from `userView` for the English confirm phrases.
- `refine` supports English time keywords (morning / afternoon / evening / nonstop) and English airline names (Air China / China Eastern …).

---

## 服务模式

| 模式 | 条件 | 接口 |
|------|------|------|
| 查价 | 需配置 APPKEY 与签名密钥（未配置返回 `307904`） | `POST /ai/shopping/v2`，请求头 `appkey`，请求体 `authentication` |
| 预订 | 已配置 APPKEY、签名密钥、AES 密钥 | `POST /api/new/pricing`、`POST /api/new/booking` |

预订依赖见 `requirements.txt`。网关地址在 `config.py` 中固定配置。

---

## 响应结构

脚本标准输出为 JSON，包含：

```json
{
  "skill": "fr24-ai",
  "status": "success|failure",
  "action": "parse|search|refine|parse-passengers|verify|order",
  "message": "给用户看的摘要",
  "userView": {},
  "agentOnly": {}
}
```

| 字段 | 用途 |
|------|------|
| `userView`、`message` | **唯一**可对用户展示、制表、下载的内容 |
| `agentOnly` | 仅 Agent 内部续跑（如 `payload`、`offerId`、`traceId`），不得写入用户可见材料 |

---

## OpenClaw 适配（必读）

本 Skill 的 `SKILL.md` frontmatter 含 `metadata.openclaw`，安装路径通常为 `{baseDir}`（如 `/root/.openclaw/skills/fr24-ai`）。OpenClaw Agent **必须执行脚本**，不得自行推断行程或手写 `pending_search.json`。

### 启动与初始化

1. **首次查价/解析前**：`parse` / `build` 会自动生成 `clientKey`（写入 `{baseDir}/.cache/skill_client.json`），无需单独记忆 `ensure-key`；维护者自检仍可执行 `skill_search_client.py ensure-key`。
2. **Python**：需满足 `metadata.openclaw.requires.anyBins`（`python3` 或 `python`）；预订功能执行 `pip install -r requirements.txt`（或 OpenClaw install 步骤）。
3. **采购密钥**：通过环境变量 `FR_NEWAPI_APPKEY` 等配置；OpenClaw 以 `primaryEnv: FR_NEWAPI_APPKEY` 识别。环境变量优先级高于 `.cache/keys.json`。

### 查价流程（OpenClaw）

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `cd {baseDir} && python3 scripts/nl_to_search.py parse --text "..."` | **必须**执行；stdout 为 JSON，只向用户展示 `userView` |
| 2 | 等待用户确认 | 禁止未确认即搜索 |
| 3 | `python3 scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json` | 用户确认后执行 |

- 用户从列表选「第 N 条」时：**`select --index N`**，**禁止**再 `search` 或误用 `search --selection direct`（那只是直飞最低价）。
- 输入已是 **IATA 三字码**（如 YYC、PEK）时，**不会**调用 `/ai/place/resolve`，属正常设计。
- 输入为 **中文/英文城市名** 时，脚本自动调 export 地名接口（请求头 `gray: ww`）。
- **禁止**从 YYC/YWG 等机场码误推航司；脚本已屏蔽此类误识别。若历史 payload 仍含错误 `preferredCarrier`，可执行 `refine --text "清除航司筛选"`。

### 禁止行为

- 禁止 Agent 手算日期、手写 intent 却不跑 `build --intent-file`
- 禁止跳过脚本直接展示报价
- 禁止向用户展示 `agentOnly`、`.cache` 路径或整段 stdout

---

## 查价流程

> **前提**：搜索接口（v2）需要采购密钥。若返回 `307904`（请提供采购认证信息），说明尚未配置采购密钥，请先按「采购密钥」章节完成配置，再重试搜索。

> **强制要求**：每次用户发起查价（含重新搜索、修改条件后搜索），**必须重新执行搜索脚本**，不得直接展示对话历史中的旧搜索结果。旧报价数据（价格、报价ID）可能已失效，沿用会导致校验失败。严禁在未执行搜索脚本的情况下向用户展示任何报价信息。

> **绝对禁止**：无论何种输入格式，**严禁自行手动构造 payload JSON 写入 `.cache/pending_search.json` 或其他缓存文件**。所有行程解析必须通过 `nl_to_search.py parse` 或 `nl_to_search.py build --intent-file` 命令执行，由脚本负责写入缓存文件。Agent 手动写入的 payload 会丢失舱位（如 V 舱被映射为 Y）、航司、航班号等过滤条件，导致搜索结果完全不准确。**发现自己想手动写入 JSON 文件时，立即停止，改走脚本路径。**

### 步骤 0：判断输入类型（必须先做）

收到用户搜索请求后，**先判断输入是自然语言还是 GDS/PNR 格式**：

- **GDS/PNR 格式**：输入中含有形如 `SS WS221 V 01JUL YWGYYC NN2` 的航段行（航司二字码+航班号+舱位单字母+日期+六字机场对，常以 `SS`/`HK`/`NN` 开头） → **走下方「GDS 格式」分支，禁止走自然语言 `parse --text` 路径**
- **自然语言**：中文/英文描述行程（如"北京飞曼谷 7月1日"） → 走步骤 1

### 自然语言路径

1. **解析**：`{baseDir}/scripts/nl_to_search.py parse --text "..."`（不消耗演示日配额）  
   → 展示 `userView`，**等待用户确认**行程、日期、人数、舱位后，才能执行步骤 2。
2. **搜索**：用户确认后执行  
   `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json`  
   → 默认**不自动选价**（`--selection none`）；仅缓存 `directOptions` 到 `booking_context.json`。  
   → 按 **[output-rules.md](./references/output-rules.md)** 以**纯文本分行格式**展示，**顺序固定：先列完所有直飞，再列中转**。
   → `userView.directOptions` 有多少条展示多少条，**不得截断、不得用"部分"或"更多"等方式省略**，每条独占多行。
   → 每条必须包含：序号①②③、航班号、完整航线、各段起降时间（跨日注"次日"）、价格、**实际退改规则**（不得用通用话术）、行李（每段）、**完整报价ID**（不得截断）。
3. 禁止将整段 stdout、`agentOnly` 或 `.cache` 路径直接提供给用户。

### GDS/PNR 格式路径

**严禁跳过脚本自行解析 GDS 并手动构造 payload。** 必须严格按以下步骤执行：

1. **构造 intent 文件**：从 GDS 行提取出发地、目的地、日期、人数，将原始 GDS 航段行整体放入 `gdsText` 字段，用 Agent 工具（如 write_file）写成临时 intent JSON 文件。  
   → intent 格式（以 `SS WS221 V 01JUL YWGYYC NN2` 为例）：  
   ```json
   {
     "tripType": "OW",
     "legs": [{"originText": "YWG", "destinationText": "YYC", "depDateText": "2026-07-01"}],
     "passengers": {"adult": 2},
     "gdsText": "SS WS221 V 01JUL YWGYYC NN2"
   }
   ```
   **注意**：`gdsText` 必须包含完整的原始 GDS 航段行，不得省略。Agent **不得**自行把舱位 `V` 映射为 `Y`，也不得自行决定 `preferredCarrier`——这些由脚本处理。

2. **执行解析脚本**：  
   `{baseDir}/scripts/nl_to_search.py build --intent-file <intent文件路径>`  
   → 脚本自动从 `gdsText` 结构化提取：舱位字母（`V`，**不映射为 Y**）、承运人（`WS`，写入 `preferredCarrier` 发服务端过滤）、航班号（`WS221`，写入 `preferredFlightNo` 客户端精确匹配），并自动跳过六字机场代码（如 YWGYYC）的模糊航司扫描，避免 YW/YY 被误识别。

3. **确认**：展示 `userView.intentSummary`（含舱位/航班号/航司/人数），**等待用户确认**行程信息无误。**禁止在用户确认前执行搜索**。

4. **搜索**：用户确认后执行  
   `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json`
   → 展示要求同自然语言路径步骤 2。

---

## 条件调整与重新搜索

用户对结果不满意并提出**航司**（如 CA/国航）、**具体航班号**（如 WS221）或**起飞时段**（如中午 12 点左右）时：

1. 不得仅在旧结果上口头筛选；须**重新搜索**（消耗演示配额；采购模式不受演示日限额约束）。
2. `{baseDir}/scripts/nl_to_search.py refine --text "<用户要求>"`（不扣配额，更新 `{baseDir}/.cache/pending_search.json`）。
3. 向用户确认更新后的 `userView`（含 `searchFilters` 或意图摘要中的航司、航班号、时段）。
4. 再次执行 `search`。
5. 仍无匹配报价时，建议放宽航司/航班号/时段；勿擅自清除用户已指定的 `preferredCarrier` / `preferredFlightNo`。

航司写入 `preferences.preferredCarrier` 并提交服务端；具体航班号写入 `preferences.preferredFlightNo`（仅客户端本地过滤，不随请求体发往服务端，用于在结果汇总阶段精确匹配展示）；起飞时段在结果汇总时按首段起飞时间过滤展示。

---

## 预订流程

须完成**两次用户确认**：

| 步骤 | 动作 |
|------|------|
| 1 | 用户从已展示列表选择报价 → **`select`（禁止为选序号重新 `search`）** |
| 2 | `{baseDir}/scripts/skill_booking_client.py parse-passengers --text "..."` → 展示 `passengerDisplay`、`contactDisplay` |
| 3 | 用户回复「**乘客信息确认无误**」或 **"passenger info confirmed"** → `verify --passenger-confirmed` |
| 4 | 展示 `orderPreview`、**报价ID**（`quoteId`）→ 用户回复「**确认生单**」或 **"confirm order"** |
| 5 | `{baseDir}/scripts/skill_booking_client.py order --user-confirmed` |
| 6 | 生单成功后，告知用户登录 https://www.flightroutes24.com/ 在「订单管理」中完成支付 |

### 选择报价（`select`，必读）

用户说「第3条」「第三个」「要 SQ8617」「报价ID xxx」「中转」时，**必须**从上次 `search` 缓存的 `booking_context.json` 中选价，**不得**再执行 `search`：

| 用户意图 | 命令 |
|----------|------|
| 直飞第 N 条（如「第三个」） | `skill_search_client.py select --index 3` |
| 报价ID | `skill_search_client.py select --offer-id <quoteId>` |
| 航班号 | `skill_search_client.py select --flight SQ8617` |
| 直飞最低 | `skill_search_client.py select --pick direct-lowest` |
| 中转最低 | `skill_search_client.py select --pick transfer` |

> **常见错误**：`search --selection direct` 表示「直飞最低价」，**不是**「直飞列表第 N 条」。选序号必须用 `select --index N`。

仅在以下情况重新 `search`：用户修改行程/日期/航司/时段（`refine` 后）、校验返回 **304016**、或上一轮搜索已过期需重查。

- 校验返回 **304016**（身份不一致）：说明新配置 APPKEY 后须**重新 search**，不可沿用旧报价标识。
- 禁止：未确认乘客即校验；未确认即生单。
- **每次新搜索后必须重新执行 `parse-passengers`**，不得沿用上一次的乘客信息。
- **`parse-passengers` / `verify` / `order` 会校验证件人数**与搜索 `adultNum/childNum/infantNum` 一致；多人须用「成人：」「儿童：」分行，或无标签时每行一位（姓名+性别+日期+护照）。
- **严禁**：搜索完成后用对话历史中的乘客信息自行调用 `parse-passengers`。
- 每次搜索成功后旧乘客缓存（`passengers.json`）会自动清除，若发现文件不存在，这是预期行为，不得用历史信息重建。

---

## 采购密钥（用户询问时）/ Procurement Keys (when user asks)

仅依据 [user-appkey-config.md](./references/user-appkey-config.md)：

- 引导用户在 [航路官网](https://www.flightroutes24.com/) 开通 API 采购；
- 在本机用户环境变量中配置 APPKEY、签名密钥、AES 密钥；
- 配置后重启 Agent 客户端；
- **禁止**向用户说明内部联调、跳过校验等维护配置。

For English users: guide them to register at [Flightroutes24](https://www.flightroutes24.com/), activate API procurement, and configure keys locally per [user-appkey-config.md](./references/user-appkey-config.md).

---

## 命令一览

| 命令 | 说明 |
|------|------|
| `{baseDir}/scripts/nl_to_search.py parse --text "..."` | 解析行程（自然语言） |
| `{baseDir}/scripts/nl_to_search.py build --intent-file <文件>` | 解析行程（GDS/PNR，intent JSON 含 `gdsText` 字段） |
| `{baseDir}/scripts/nl_to_search.py refine --text "..."` | 合并航司、起飞时段等条件（`清除航司筛选` 可去掉误识别或已指定的航司） |
| `{baseDir}/scripts/skill_search_client.py search --payload-file {baseDir}/.cache/pending_search.json` | 搜索（v2，默认不自动选价） |
| `{baseDir}/scripts/skill_search_client.py select --index 3` | 从缓存选第 3 条直飞（不重搜） |
| `{baseDir}/scripts/skill_search_client.py select --offer-id <id>` / `--flight SQ8617` / `--pick transfer` | 按报价ID、航班号或类别选价 |
| `{baseDir}/scripts/skill_booking_client.py parse-passengers --text "..."` | 乘客信息核对 |
| `{baseDir}/scripts/skill_booking_client.py verify --passenger-confirmed` | 校验报价 |
| `{baseDir}/scripts/skill_booking_client.py order --user-confirmed` | 生单 |
| `{baseDir}/scripts/config_keys.py set --appkey ... --sign-secret ... --aes-secret ...` | 配置采购密钥 |
| `{baseDir}/scripts/config_keys.py status` | 查看配置状态 |
| `{baseDir}/scripts/config_keys.py clear` | 清除本地密钥配置 |

---

## 业务限制 / Business Constraints

- 支持单程、往返；不支持多段缺口程。/ Supports one-way and round-trip; multi-city itineraries are not supported.
- 搜索接口（v2）必须配置采购密钥；未配置时返回 `307904`，应引导用户按「采购密钥」章节完成配置。/ The v2 search API requires procurement keys; without them `307904` is returned — guide the user to configure keys.
- 生单为真实订单，必须在用户明确确认后提交。/ Orders are real bookings and must only be submitted after explicit user confirmation.
