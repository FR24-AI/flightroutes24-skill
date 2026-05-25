# 预订流程（纯 Skill 脚本，无 MCP）

对用户展示、下载内容遵循 [output-rules.md](./output-rules.md)（仅用 `userView`）。  
环境变量与联调配置见 [setup-maintainer.md](./setup-maintainer.md)（**勿**展示给用户）。

未配置采购密钥时仅 Skill 查价（`/api/skill/shopping`）。

## 标准顺序

| 步骤 | 命令 | 用户确认 |
|------|------|----------|
| 1 | `nl_to_search.py parse` → `skill_search_client.py search --selection direct` | 选直飞/中转 |
| 2 | `skill_booking_client.py parse-passengers --text "..."` | 「乘客信息确认无误」 |
| 3 | `skill_booking_client.py verify --passenger-confirmed` | — |
| 4 | 向用户展示 `userView.orderPreview` | 「确认生单」 |
| 5 | `skill_booking_client.py order --user-confirmed` | — |

## 命令示例（Agent 内部）

```bash
cd fr_newapi_search_skill
set PYTHONIOENCODING=utf-8

python scripts/nl_to_search.py parse --text "深圳到曼谷 6月2日"
python scripts/skill_search_client.py search --payload-file .cache/pending_search.json --selection direct

python scripts/skill_booking_client.py parse-passengers --text "张三 男 1990-01-15 护照E12345678，2030-12-31到期 国籍CN。联系人：张三 手机13800138000 邮箱 zhangsan@example.com"

python scripts/skill_booking_client.py verify --passenger-confirmed

python scripts/skill_booking_client.py order --user-confirmed
```

缓存文件（勿提供给用户下载）：

- `.cache/pending_search.json` — 搜索请求体
- `.cache/booking_context.json` — 选定报价
- `.cache/passengers.json` — 已解析乘客与联系人

## 乘客自然语言示例（对用户说明时可引用）

```
乘客：张三，男，1990-01-15，护照 E12345678，2030-12-31 到期，国籍 CN。
联系人：张三，手机 13800138000，邮箱 zhangsan@example.com
```

解析输出 `passengerDisplay`：展示「张三 → ZHANG/SAN（拼音 zhangsan）」等字段对照。
