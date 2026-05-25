# Skill 搜索参数说明（对应 ApiSearchRq）

## searchLegs[]

| 字段 | 必填 | 格式 |
|------|------|------|
| origin | 是 | IATA 三字码 |
| destination | 是 | IATA 三字码 |
| depDate | 是 | `YYYY-MM-DD` |
| typeO / typeD | 否 | `airportcode` 或 `airportgroup` |

## 行程类型

- 1 段 → 单程
- 2 段且 A→B、B→A → 往返
- 其他 → Skill 拒绝（307902）

## 乘客

- adultNum ≥ 1
- 成人+儿童 ≤ 9；儿童 ≤ 成人×2

## preferences

| 字段 | 默认 |
|------|------|
| cabin | Y |
| stops | 2（直飞填 0） |
| resultCtrl | 15（≤20） |
