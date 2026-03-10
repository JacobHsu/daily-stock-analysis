# Discord 機器人配置

## Discord 機器人
Discord 機器人接收訊息需要使用 Discord Developer Portal 建立機器人應用
https://discord.com/developers/applications

Discord 機器人支援兩種訊息發送方式：
1. **Webhook 模式**：配置簡單，權限低，適合只需要發送訊息的情境
2. **Bot API 模式**：權限高，支援接收指令，需要配置 Bot Token 和頻道 ID

## 建立 Discord 機器人

### 1. 登入 Discord Developer Portal
前往 https://discord.com/developers/applications 並使用你的 Discord 帳號登入

### 2. 建立應用
點擊「New Application」按鈕，輸入應用名稱（例如：股票智能分析機器人），然後點擊「Create」

### 3. 配置機器人
在左側導覽列中點擊「Bot」，然後點擊「Add Bot」按鈕，確認新增

### 4. 取得 Bot Token
在 Bot 頁面，點擊「Reset Token」按鈕，然後複製產生的 Token（這是你的 `DISCORD_BOT_TOKEN`）

### 5. 配置權限
在 Bot 頁面的「Privileged Gateway Intents」部分，開啟以下選項：
- Presence Intent
- Server Members Intent
- Message Content Intent

### 6. 新增到伺服器
1. 在左側導覽列中點擊「OAuth2」>「URL Generator」
2. 在「Scopes」中選擇：
   - `bot`
   - `applications.commands`
3. 在「Bot Permissions」中選擇：
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Use Slash Commands
4. 複製產生的 URL，在瀏覽器中開啟，選擇要新增機器人的伺服器

### 7. 取得頻道 ID
1. 在 Discord 用戶端中，開啟開發者模式：設定 > 進階 > 開發者模式
2. 右鍵點擊你想要機器人發送訊息的頻道，選擇「Copy ID」（這是你的 `DISCORD_MAIN_CHANNEL_ID`）

## 配置環境變數

將以下配置新增到你的 `.env` 檔案中：

```env
# Discord 機器人配置
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_MAIN_CHANNEL_ID=your-channel-id
DISCORD_WEBHOOK_URL=your-webhook-url （可選）
DISCORD_BOT_STATUS=股票智能分析 | /help
```

## Webhook 模式配置（可選）

如果你只想使用 Webhook 模式發送訊息，不需要 Bot Token，可以按照以下步驟配置：

1. 右鍵點擊頻道，選擇「編輯頻道」
2. 點擊「整合」>「Webhooks」>「新建 Webhook」
3. 配置 Webhook 名稱和頭像
4. 複製 Webhook URL（這是你的 `DISCORD_WEBHOOK_URL`）

## 支援的指令

Discord 機器人支援以下 Slash 指令：

1. `/analyze <stock_code> [full_report]` - 分析指定股票代碼
   - `stock_code`：股票代碼，如 SPY
   - `full_report`：可選，是否產生完整報告（含大盤）

2. `/market_review` - 取得大盤複盤報告

3. `/help` - 查看說明資訊

## 測試機器人

1. 確認機器人已成功新增到你的伺服器
2. 在頻道中輸入 `/help`，機器人會回傳說明資訊
3. 輸入 `/analyze SPY` 測試股票分析功能
4. 輸入 `/market_review` 測試大盤複盤功能

## 注意事項

1. 確認你的機器人有足夠的權限在頻道中發送訊息和使用 Slash 指令
2. 定期更新你的 Bot Token，確保安全性
3. 不要將你的 Bot Token 分享給任何人
4. 如果機器人沒有回應，請檢查：
   - Bot Token 是否正確
   - 頻道 ID 是否正確
   - 機器人是否在線
   - 機器人是否有訊息發送權限

## 故障排除

- **機器人不回應指令**：檢查 Bot Token 和頻道 ID 是否正確，確認機器人已新增到伺服器
- **Slash 指令不顯示**：等待一段時間（Discord 需要同步指令），或重新新增機器人
- **訊息發送失敗**：檢查頻道權限，確認機器人有發送訊息的權限

## 相關連結

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Discord Bot Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Discord Slash Commands](https://discord.com/developers/docs/interactions/application-commands)
