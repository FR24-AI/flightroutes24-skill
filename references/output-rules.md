# 输出规则（对用户展示与下载）/ Output Rules

脚本 stdout 含 **`userView`**（给用户）与 **`agentOnly`**（仅 Agent 内部续跑）。  
**对用户聊天、表格、附件、导出文件时，只使用 `userView` 与顶层 `message`，禁止引用 `agentOnly` 或整段原始 stdout。**

## 语言 / Language

- 全程跟随用户语言回复（中文或英文）。
- When responding in English: use "direct flight" / "connecting flight" (not 直飞/中转), "Quote ID" (not 报价ID), "refund" / "change fee" for refundText/changeText.
- Confirm phrases in English: **"passenger info confirmed"** and **"confirm order"** are equivalent to the Chinese phrases.
- Script output `userView.message` may contain Chinese labels. **Do not copy them verbatim** when responding in English — rephrase them in English using the structured fields.
- `passengerConfirmPromptEn` / `confirmPhraseEn` / `orderConfirmPromptEn` are the English equivalents in `userView`. Use these when the user is English-speaking.

### 字段翻译参考 / Field label translation (for English responses)

| Script label | English |
|---|---|
| 直飞最低 / Direct (lowest) | Lowest direct fare |
| 中转最低 / Connecting (lowest) | Lowest connecting fare |
| 退票/Refund | Refund policy |
| 改期/Change | Change fee |
| 姓名/Name | Name |
| 性别/Gender | Gender |
| 出生日期/DOB | Date of birth |
| 证件类型/DocType | Document type |
| 证件号/DocNo | Document number |
| 证件有效期/Expiry | Expiry date |
| 国籍/Nationality | Nationality |
| 乘客类型/PaxType | Passenger type |
| 联系人/Contact | Contact name |
| 手机/Phone | Phone |
| 邮箱/Email | Email |
| 单程 (One-way) | One-way |
| 往返 (Round-trip) | Round-trip |

## 查价 parse 后（未搜索）

- 用表格确认：`userView` 中的行程、日期、人数、舱位（`intentSummary` / `legs`）
- **禁止**向用户展示：`payload`、`payloadFile`、本机路径、Python 命令行

## 搜索 search 成功后

### 直飞报价（directOptions）

- `userView.directOptions` 返回多少条，**必须完整展示全部条目，不得省略、截断或合并任何一条**
- 每条**必须**包含以下所有字段：

| 字段 | 来源 | 说明 |
|------|------|------|
| 序号 | 列表顺序 | 从 1 开始 |
| 航班号 | `flights` | 完整航班号，不得缩写 |
| 完整航线 | `route` 或 `segments` | 含出发/到达机场代码（如 HKG→DMK） |
| 各航段起飞→到达时间 | `segments[].depTime` / `arrTime` | 每段都展示，跨日注明"次日" |
| 人均成人价 | `totalPrice` + `currency` | 采购模式不加"演示价"标注 |
| 退票/改期摘要 | `refundChange.refundText` / `changeText` | **必须逐条展示实际退改规则，不得用"以航司政策为准"等通用话术替代** |
| 行李摘要 | `baggage`（每段） | 每段行李额都展示 |
| 完整报价ID | `quoteId` | **不得截断，必须完整展示** |

### 中转报价（transferLowest）

- 展示最低价中转方案，字段要求同上
- 各段航班号、机场、时间均须完整展示

### 通用规则

- 可展示 **今日剩余搜索次数**（`remainingQuota` / `dailyLimit`）（如有）
- 多条可订时，请用户选择序号、航班号或「中转」
- **禁止**：自行判断哪些字段"不重要"而省略；禁止截断 quoteId；禁止用通用话术替代具体退改规则

## 用户要改航司 / 起飞时间

- 须 **refine → 再 search**（见 SKILL.md），不要只复述旧报价
- 可展示 `searchFilters` / 筛选条件摘要；无匹配时说明「未找到符合条件」并建议放宽

## 搜索失败（307904 / 未配置采购密钥）

- 使用 `userView.message` / 顶层 `message` 引导用户配置采购密钥
- 可展示 `registerPortalUrl` 链接（[航路官网](https://www.flightroutes24.com/)）
- 用户问具体配置步骤时，按 [user-appkey-config.md](./user-appkey-config.md) 回答
- **不要**提示「明日再试」或「演示配额已用完」（v2 接口无演示配额）

## 预订

- **parse-passengers**：只展示 `passengerDisplay`、`contactDisplay` 与确认话术
- **verify / order**：展示 `orderPreview`（行程、退改、乘客回显）、**报价ID**（`quoteId`）及订单号等业务字段
- **禁止**向用户展示：证件明文 API 结构、`passengerRawMappings`、`contactRaw`

## 禁止写入用户下载 / 对外展示

| 类别 | 示例 |
|------|------|
| 链路调试 | `traceId`、`processingTime` |
| 内部状态 | `code`、`searchMode`、`workflowSteps`、`workflowStep` |
| 密钥与路径 | `clientKey`、`payloadFile`、`.cache/` 路径、完整 `payload` |
| 原始 API | 完整 `ApiSearchRs`、`data.offers` 全量列表 |
| 预订内部 ID | `verifyOfferId`、`offerId`（用 `quoteId` 报价ID 代替，用户可看到） |
| 内部测试与维护材料 | 测试报告、维护文档全文、非生产网关说明 |
| 环境变量名 | 勿向用户列出采购/网关相关的系统变量名 |
| 示例姓名 | 中文语境用 **张三**（儿童：**张小三**）；英文语境用 **John Doe**（child: **Jane Doe**） |

## Agent 内部（可读 `agentOnly`）

- 续跑命令所需：`payload`、`offerId`、`verifyOfferId`、`passengers` 等见 `agentOnly` 或 `.cache/`
- 排障：将 `agentOnly.traceId` 提供给运维时**勿**粘贴到用户可见文档

## 用户问配置 appkey / 采购密钥

- **只**按 [user-appkey-config.md](./user-appkey-config.md) 回答
- **禁止**：说明内部联调、跳过校验/白名单等非用户配置项
- **禁止**：让用户在聊天里提交密钥明文，或代用户在对话中执行环境变量配置命令

## 流程禁止

- 未确认意图就 `search`（扣配额）
- 未确认乘客就 `verify`
- 未确认就 `order`
- 把脚本 stdout 整段保存为用户「下载文件」
