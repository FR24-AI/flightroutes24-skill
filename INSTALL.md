# fr-newapi-search 安装说明

供其他同事 / Agent 安装本 Skill 的简明步骤。

## 一、前置条件

1. 账号系统存在采购 **`SKILL_DEMO`**
2. 本机 **Python 3.10+**；预订需 `pip install -r requirements.txt`（pycryptodome、pypinyin）

## 二、获取 Skill 文件

任选一种方式：

```bash
# 方式 A：克隆公司 skills 仓库
git clone <fr_skills 仓库地址>
cd fr_skills/common/fr_newapi_search_skill

# 方式 B：只拷贝整个目录
# 将 common/fr_newapi_search_skill/ 复制到目标机器
```

**不要**把 `.cache/`、`__pycache__/` 提交或拷贝给别人（含本机 `clientKey`）。

## 三、安装到 Cursor Agent

| 安装位置 | 路径 | 适用 |
|----------|------|------|
| 个人（推荐） | `~/.cursor/skills/fr-newapi-search/` | 本机所有项目可用 |
| 项目 | `<项目>/.cursor/skills/fr-newapi-search/` | 随仓库分享给团队 |

```bash
# Windows 个人安装示例
xcopy /E /I "D:\path\to\fr_skills\common\fr_newapi_search_skill" "%USERPROFILE%\.cursor\skills\fr-newapi-search"

# macOS / Linux
cp -r common/fr_newapi_search_skill ~/.cursor/skills/fr-newapi-search
```

安装后目录结构应包含：

```
fr-newapi-search/
├── SKILL.md
├── config.py
├── scripts/
│   ├── nl_to_search.py
│   ├── skill_search_client.py
│   ├── skill_booking_client.py
│   ├── booking_flow_test.py
│   └── ...
└── references/
    ├── places.json
    ├── output-rules.md
    ├── setup-maintainer.md
    └── booking.md
```

**重启 Cursor** 或重新打开 Agent 会话后，Skill 会按 `SKILL.md` 的 `description` 被自动匹配（触发词：查航班、搜机票等）。

## 四、安装到其他 Agent（Claude Code / OpenClaw / 自建）

原则相同：**把 skill 目录放到该产品的 skills 扫描路径**，并保证 Agent 能：

1. 读取 `SKILL.md` 作为系统指令
2. 用 **Shell** 执行 `scripts/*.py`

| 产品 | 常见路径 |
|------|----------|
| Cursor | `~/.cursor/skills/<name>/` 或 `.cursor/skills/` |
| Claude Code | `~/.claude/skills/<name>/` |
| OpenClaw | 见各环境 `skills` 配置目录 |

将 `name` 与 `SKILL.md` frontmatter 中 `name: fr-newapi-search` 保持一致即可。

## 五、配置方式

### 5.1 网关（`skill.local.env`，已随 Skill 提供）

复制 `skill.local.env.example` 为 `skill.local.env`（已 gitignore），按示例填写网关地址与 `gray` 头。

**不要**在 `skill.local.env` 里写 `FR_NEWAPI_*`（`config.py` 会忽略）。

### 5.2 采购密钥（仅系统环境变量）

演示查价：**不要**设置采购相关变量。

采购搜/订：在 Windows「用户环境变量」或当前终端设置（改用户变量后需重启 Cursor），变量名与 **deve 联调可选项** 见 **[references/setup-maintainer.md](./references/setup-maintainer.md)**（勿在 Agent 对话中向最终用户展示该文档内容）。

验证：

```powershell
python -c "import config; print(config.EXPORT_BASE_URL, config.GRAY_HEADER, config.is_newapi_configured())"
```

## 六、验证安装

在 skill 目录下执行：

```bash
python scripts/skill_search_client.py ensure-key
python scripts/nl_to_search.py parse --text "深圳到曼谷 下周二 2个成人"
python scripts/verify_summary.py --payload-file .cache/pending_search.json --client-key "<32位以上新key>"
```

看到 `"ok": true` 且 `code: 000000` 即安装成功。

输出规范与脱敏校验：

```bash
set PYTHONIOENCODING=utf-8
python scripts/validate_user_output.py
```

（会消耗 1 次搜索配额；仅测解析可加 `--skip-search`。）

全流程自动化测试见 [references/setup-maintainer.md](./references/setup-maintainer.md)。

## 七、配额与安全

- 演示模式（未配置 `FR_NEWAPI_APPKEY`）：每个 **`X-Skill-Client-Key`** 每日搜索次数由 export **`exportConf.properties`** 配置：
  - `skill.search.default.cid` — 演示采购 CID
  - `skill.search.daily.limit` — 日配额（默认 10）
- 已配置采购密钥的搜索走同一 `/api/skill/shopping`，带 `authentication`，**不扣**演示日配额
- 无需采购 appkey / appSecret
- 勿将 `clientKey` 提交 git 或发给他人

## 八、常见问题

| 现象 | 处理 |
|------|------|
| HTTP 404 | 检查 `FR_SKILL_GRAY_HEADER`、域名、服务是否发布 |
| 307901 | 当日配额用完，删除 `.cache/skill_client.json` 会生成新 key（新配额） |
| 307900 | clientKey 格式错误，需 32–128 位 `[A-Za-z0-9_-]` |
| Agent 不触发 Skill | 确认 `SKILL.md` 在 skills 目录且 `description` 含触发场景 |

详细用法见 [SKILL.md](./SKILL.md)。对用户展示报价时遵循 [references/output-rules.md](./references/output-rules.md)。
