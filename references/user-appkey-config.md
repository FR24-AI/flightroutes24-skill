# 采购 APPKEY 配置（对用户说明用）

用户询问「如何配置 appkey / 采购密钥 / 开通预订」时，**只按本文回答**。  
**禁止**提及 `FR_NEWAPI_SKIP_*`、跳过白名单/签名、deve 联调、`setup-maintainer.md`。  
**禁止**在对话中让用户粘贴密钥明文；引导用户在本机自行配置。

## 前提

1. 已在 [航路官网](https://www.flightroutes24.com/) 注册并开通 API 采购，取得三项密钥：
   - **APPKEY**（采购编号）
   - **SHA512 签名密钥**
   - **AES 密钥**（16 字节，用于乘客信息加密）
2. 演示查价无需配置；仅 **采购搜索 + 预订** 需要。

## 推荐：Windows「用户环境变量」（图形界面）

1. `Win + R` → 输入 `sysdm.cpl` → 回车  
2. **高级** → **环境变量**  
3. 在 **用户变量** 中 **新建** 三条（值由用户在航路后台复制，勿在聊天里发送）：

| 变量名 | 说明 |
|--------|------|
| `FR_NEWAPI_APPKEY` | 采购 APPKEY |
| `FR_NEWAPI_SIGN_SECRET` | SHA512 签名密钥 |
| `FR_NEWAPI_AES_SECRET` | 16 字节 AES 密钥 |

4. 全部 **确定** 保存后，**完全退出并重新打开 Claude Code**（或重启电脑），环境变量才会被 Skill 读到。

## 备选：PowerShell（用户变量，永久）

在用户自己的 PowerShell 中执行（将引号内替换为真实值，**勿发给 Agent**）：

```powershell
[System.Environment]::SetEnvironmentVariable("FR_NEWAPI_APPKEY", "你的APPKEY", "User")
[System.Environment]::SetEnvironmentVariable("FR_NEWAPI_SIGN_SECRET", "你的SHA512签名密钥", "User")
[System.Environment]::SetEnvironmentVariable("FR_NEWAPI_AES_SECRET", "你的16字节AES密钥", "User")
```

执行后同样需要 **重启 Claude Code**。

## 验证（用户可在本机执行）

在 Skill 目录（如 `~/.claude/skills/fr-newapi-search`）打开**新**终端：

```powershell
python -c "import config; print('configured:', config.is_newapi_configured()); print('booking_ready:', config.is_booking_ready())"
```

| 输出 | 含义 |
|------|------|
| `configured: True` | 已识别 APPKEY（及签名或联调模式，以本机为准） |
| `booking_ready: True` | 三项密钥齐全，可预订 |

若为 `False`，检查变量是否在 **用户变量**、名称是否拼写正确、是否已重启 Claude Code。

## Agent 禁止事项

- 不要输出「跳过 IP 白名单 / 跳过签名验证」及 `FR_NEWAPI_SKIP_*` 相关命令  
- 不要让用户把密钥发到对话里「帮你设置」  
- 不要引用 `setup-maintainer.md`（维护者文档）
