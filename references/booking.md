# 预订流程（纯 Skill 脚本，无 MCP）

## 环境变量（NewApi 预订）

```bash
set FR_SKILL_EXPORT_BASE_URL=https://flight-deve.flightroutes24.com
set FR_SKILL_GRAY_HEADER=ww
set FR_NEWAPI_APPKEY=你的采购APPKEY
set FR_NEWAPI_SIGN_SECRET=SHA512签名密钥
set FR_NEWAPI_AES_SECRET=16字节AES密钥
set FR_NEWAPI_SKIP_IP_WHITELIST=1
```

未配置 `FR_NEWAPI_*` 时仅 Skill 查价（`/api/skill/shopping`）。

## 标准顺序

| 步骤 | 命令 | 用户确认 |
|------|------|----------|
| 1 | `nl_to_search.py parse` → `skill_search_client.py search --selection direct` | 选直飞/中转 |
| 2 | `skill_booking_client.py parse-passengers --text "..."` | 「乘客信息确认无误」 |
| 3 | `skill_booking_client.py verify --passenger-confirmed` | — |
| 4 | 向用户展示 `data.orderPreview` | 「确认生单」 |
| 5 | `skill_booking_client.py order --user-confirmed` | — |

## 命令示例

```bash
cd fr_newapi_search_skill
set PYTHONIOENCODING=utf-8

python scripts/nl_to_search.py parse --text "深圳到曼谷 6月2日"
python scripts/skill_search_client.py search --payload-file .cache/pending_search.json --selection direct

python scripts/skill_booking_client.py parse-passengers --text "魏威 男 1990-01-15 护照E123，2030-12-31到期 国籍CN。联系人：ZHANG/SAN 手机13800138000 邮箱 a@b.com"

python scripts/skill_booking_client.py verify --passenger-confirmed

python scripts/skill_booking_client.py order --user-confirmed
```

缓存文件：

- `.cache/pending_search.json` — 搜索请求体
- `.cache/booking_context.json` — 搜索 trace、选定 offer
- `.cache/passengers.json` — 已解析乘客与联系人

## 乘客自然语言示例

```
乘客：ZHANG/SAN，男，1990-01-15，护照 E12345678，2030-12-31 到期，国籍 CN。
联系人：ZHANG/SAN，手机 13800138000，邮箱 zhangsan@example.com
```

解析输出 `passengerDisplay`：展示「魏威 → WEI/WEI（拼音 weiwei）」等字段对照。

## 联调

```bash
set FR_BOOKING_TEST_ORDER=1
python scripts/booking_flow_test.py
```
