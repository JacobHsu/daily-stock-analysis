# 📖 完整配置與部署指南

本文檔包含美股智慧分析系統的完整配置說明，適合需要進階功能或特殊部署方式的用戶。

> 💡 快速上手請參考 [README.md](../README.md)，本文檔為進階配置。

## 📁 專案結構

```
daily_stock_analysis/
├── main.py              # 主程式入口
├── src/                 # 核心業務邏輯
│   ├── analyzer.py      # AI 分析器
│   ├── config.py        # 配置管理
│   ├── notification.py  # 訊息推送
│   └── ...
├── data_provider/       # 資料來源適配器
├── bot/                 # 機器人互動模組
├── api/                 # FastAPI 後端服務
├── apps/dsa-web/        # React 前端
├── docs/                # 專案文件
└── .github/workflows/   # GitHub Actions
```

## 📑 目錄

- [專案結構](#專案結構)
- [GitHub Actions 詳細配置](#github-actions-詳細配置)
- [環境變數完整列表](#環境變數完整列表)
- [本地執行詳細配置](#本地執行詳細配置)
- [定時任務配置](#定時任務配置)
- [通知管道詳細配置](#通知管道詳細配置)
- [資料來源配置](#資料來源配置)
- [進階功能](#進階功能)
- [回測功能](#回測功能)
- [FastAPI API 服務](#fastapi-api-服務)

---

## GitHub Actions 詳細配置

### 1. Fork 本倉庫

點擊右上角 `Fork` 按鈕

### 2. 配置 Secrets

進入你 Fork 的倉庫 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

#### AI 模型配置（二選一）

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) 取得免費 Key | ✅* |
| `OPENAI_API_KEY` | OpenAI 相容 API Key（支援 DeepSeek 等） | 可選 |
| `OPENAI_BASE_URL` | OpenAI 相容 API 地址（如 `https://api.deepseek.com/v1`） | 可選 |
| `OPENAI_MODEL` | 模型名稱（如 `gemini-3.1-pro-preview`、`deepseek-chat`） | 可選 |

> *注：`GEMINI_API_KEY` 和 `OPENAI_API_KEY` 至少配置一個

#### 通知管道配置（可同時配置多個，全部推送）

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（@BotFather 取得） | 可選 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可選 |
| `TELEGRAM_MESSAGE_THREAD_ID` | Telegram Topic ID（用於發送到子話題） | 可選 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可選 |
| `DISCORD_BOT_TOKEN` | Discord Bot Token（與 Webhook 二選一） | 可選 |
| `DISCORD_CHANNEL_ID` | Discord Channel ID（使用 Bot 時需要） | 可選 |
| `EMAIL_SENDER` | 寄件人信箱 | 可選 |
| `EMAIL_PASSWORD` | 信箱授權碼（非登入密碼） | 可選 |
| `EMAIL_RECEIVERS` | 收件人信箱（多個用逗號分隔，留空則發給自己） | 可選 |
| `EMAIL_SENDER_NAME` | 寄件人顯示名稱（預設：美股分析助手） | 可選 |
| `PUSHOVER_USER_KEY` | Pushover 用戶 Key | 可選 |
| `PUSHOVER_API_TOKEN` | Pushover API Token | 可選 |
| `PUSHPLUS_TOKEN` | PushPlus Token（[取得地址](https://www.pushplus.plus)） | 可選 |
| `SERVERCHAN3_SENDKEY` | Server 醬³ Sendkey（[取得地址](https://sc3.ft07.com/)） | 可選 |
| `CUSTOM_WEBHOOK_URLS` | 自訂 Webhook（多個用逗號分隔） | 可選 |
| `CUSTOM_WEBHOOK_BEARER_TOKEN` | 自訂 Webhook 的 Bearer Token | 可選 |
| `WEBHOOK_VERIFY_SSL` | Webhook HTTPS 憑證校驗（預設 true）。設為 false 可支援自簽憑證。警告：關閉有嚴重安全風險（MITM），僅限可信內網 | 可選 |

> *注：至少配置一個管道，配置多個則同時推送

#### 推送行為配置

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `SINGLE_STOCK_NOTIFY` | 單股推送模式：設為 `true` 則每分析完一支股票立即推送 | 可選 |
| `REPORT_TYPE` | 報告類型：`simple`（精簡）或 `full`（完整） | 可選 |
| `REPORT_SUMMARY_ONLY` | 僅分析結果摘要：設為 `true` 時只推送彙總，不含個股詳情 | 可選 |
| `ANALYSIS_DELAY` | 個股分析和大盤分析之間的延遲（秒），避免 API 限流，如 `10` | 可選 |
| `MERGE_EMAIL_NOTIFICATION` | 個股與大盤復盤合併推送（預設 false），減少郵件數量 | 可選 |
| `MARKDOWN_TO_IMAGE_CHANNELS` | 將 Markdown 轉為圖片發送的管道（逗號分隔）：telegram,custom,email | 可選 |
| `MARKDOWN_TO_IMAGE_MAX_CHARS` | 超過此長度不轉圖片（預設 15000） | 可選 |
| `MD2IMG_ENGINE` | 轉圖引擎：`wkhtmltoimage`（預設）或 `markdown-to-file` | 可選 |

#### 其他配置

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `STOCK_LIST` | 自選股代碼，如 `AAPL,TSLA,NVDA` | ✅ |
| `TAVILY_API_KEYS` | [Tavily](https://tavily.com/) 搜尋 API（新聞搜尋） | 推薦 |
| `BRAVE_API_KEYS` | [Brave Search](https://brave.com/search/api/) API（美股優化） | 可選 |
| `SERPAPI_API_KEYS` | [SerpAPI](https://serpapi.com/) 備用搜尋 | 可選 |

#### ✅ 最小配置範例

最少需要配置以下項：

1. **AI 模型**：`AIHUBMIX_KEY`、`GEMINI_API_KEY` 或 `OPENAI_API_KEY`
2. **通知管道**：至少配置一個，如 `EMAIL_SENDER` + `EMAIL_PASSWORD`
3. **股票列表**：`STOCK_LIST`（必填）
4. **搜尋 API**：`TAVILY_API_KEYS`（強烈推薦）

> 💡 配置完以上 4 項即可開始使用！

### 3. 啟用 Actions

1. 進入你 Fork 的倉庫
2. 點擊頂部的 `Actions` 標籤
3. 如果看到提示，點擊 `I understand my workflows, go ahead and enable them`

### 4. 手動測試

1. 進入 `Actions` 標籤
2. 左側選擇 `每日股票分析` workflow
3. 點擊右側的 `Run workflow` 按鈕
4. 選擇執行模式
5. 點擊綠色的 `Run workflow` 確認

### 5. 完成！

預設每個工作日 **22:00（台灣時間）** 自動執行。

---

## 環境變數完整列表

### AI 模型配置

| 變數名 | 說明 | 預設值 | 必填 |
|--------|------|--------|:----:|
| `AIHUBMIX_KEY` | AIHubmix API Key，一 Key 切換使用全系模型 | - | 可選 |
| `GEMINI_API_KEY` | Google Gemini API Key | - | 可選 |
| `GEMINI_MODEL` | 主模型名稱 | `gemini-3-flash-preview` | 否 |
| `GEMINI_MODEL_FALLBACK` | 備選模型 | `gemini-2.5-flash` | 否 |
| `OPENAI_API_KEY` | OpenAI 相容 API Key | - | 可選 |
| `OPENAI_BASE_URL` | OpenAI 相容 API 地址 | - | 可選 |
| `OPENAI_MODEL` | OpenAI 模型名稱 | `gpt-5.2` | 可選 |
| `ANTHROPIC_API_KEY` | Anthropic Claude API Key | - | 可選 |
| `ANTHROPIC_MODEL` | Claude 模型名稱 | `claude-3-5-sonnet-20241022` | 可選 |
| `ANTHROPIC_TEMPERATURE` | Claude 溫度參數（0.0-1.0） | `0.7` | 可選 |
| `ANTHROPIC_MAX_TOKENS` | Claude 回應最大 token 數 | `8192` | 可選 |

> *注：`AIHUBMIX_KEY`、`GEMINI_API_KEY`、`ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY` 至少配置一個。

### 通知管道配置

| 變數名 | 說明 | 必填 |
|--------|------|:----:|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 可選 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可選 |
| `TELEGRAM_MESSAGE_THREAD_ID` | Telegram Topic ID | 可選 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可選 |
| `DISCORD_BOT_TOKEN` | Discord Bot Token（與 Webhook 二選一） | 可選 |
| `DISCORD_CHANNEL_ID` | Discord Channel ID（使用 Bot 時需要） | 可選 |
| `DISCORD_MAX_WORDS` | Discord 最大字數限制（預設 2000） | 可選 |
| `EMAIL_SENDER` | 寄件人信箱 | 可選 |
| `EMAIL_PASSWORD` | 信箱授權碼（非登入密碼） | 可選 |
| `EMAIL_RECEIVERS` | 收件人信箱（逗號分隔，留空發給自己） | 可選 |
| `EMAIL_SENDER_NAME` | 寄件人顯示名稱 | 可選 |
| `STOCK_GROUP_N` / `EMAIL_GROUP_N` | 股票分組發往不同信箱，如 `STOCK_GROUP_1=AAPL,TSLA` 與 `EMAIL_GROUP_1=user1@example.com` 配對 | 可選 |
| `CUSTOM_WEBHOOK_URLS` | 自訂 Webhook（逗號分隔） | 可選 |
| `CUSTOM_WEBHOOK_BEARER_TOKEN` | 自訂 Webhook Bearer Token | 可選 |
| `WEBHOOK_VERIFY_SSL` | Webhook HTTPS 憑證校驗（預設 true） | 可選 |
| `PUSHOVER_USER_KEY` | Pushover 用戶 Key | 可選 |
| `PUSHOVER_API_TOKEN` | Pushover API Token | 可選 |
| `PUSHPLUS_TOKEN` | PushPlus Token | 可選 |
| `SERVERCHAN3_SENDKEY` | Server 醬³ Sendkey | 可選 |

### 搜尋服務配置

| 變數名 | 說明 | 必填 |
|--------|------|:----:|
| `TAVILY_API_KEYS` | Tavily 搜尋 API Key（推薦） | 推薦 |
| `BOCHA_API_KEYS` | 博查搜尋 API Key | 可選 |
| `BRAVE_API_KEYS` | Brave Search API Key（美股優化） | 可選 |
| `SERPAPI_API_KEYS` | SerpAPI 備用搜尋 | 可選 |
| `NEWS_MAX_AGE_DAYS` | 新聞最大時效（天） | 預設 `3` |
| `BIAS_THRESHOLD` | 乖離率閾值（%），超過提示不追高 | 預設 `5.0` |

### 資料來源配置

| 變數名 | 說明 | 預設值 | 必填 |
|--------|------|--------|:----:|
| `ENABLE_REALTIME_QUOTE` | 啟用即時行情（關閉後使用歷史收盤價分析） | `true` | 可選 |
| `ENABLE_REALTIME_TECHNICAL_INDICATORS` | 盤中即時技術面：啟用時用即時價計算 MA5/MA10/MA20 | `true` | 可選 |
| `ENABLE_CHIP_DISTRIBUTION` | 啟用籌碼分佈分析（不穩定，雲端部署建議關閉） | `true` | 可選 |
| `REALTIME_SOURCE_PRIORITY` | 即時行情資料來源優先級 | `yfinance` | 可選 |

### 其他配置

| 變數名 | 說明 | 預設值 |
|--------|------|--------|
| `STOCK_LIST` | 自選股代碼（逗號分隔） | - |
| `ADMIN_AUTH_ENABLED` | Web 登入：設為 `true` 啟用密碼保護；忘記密碼執行 `python -m src.auth reset_password` | `false` |
| `TRUST_X_FORWARDED_FOR` | 反向代理部署時設為 `true` | `false` |
| `MAX_WORKERS` | 並發執行緒數 | `3` |
| `MARKET_REVIEW_ENABLED` | 啟用大盤復盤 | `true` |
| `MARKET_REVIEW_REGION` | 大盤復盤市場區域：`us`（美股） | `us` |
| `TRADING_DAY_CHECK_ENABLED` | 交易日檢查：非交易日跳過執行；設為 `false` 或使用 `--force-run` 可強制執行 | `true` |
| `SCHEDULE_ENABLED` | 啟用定時任務 | `false` |
| `SCHEDULE_TIME` | 定時執行時間（台灣時間） | `22:00` |
| `LOG_DIR` | 日誌目錄 | `./logs` |

---

## 本地執行詳細配置

### 安裝依賴

```bash
# Python 3.10+ 推薦
pip install -r requirements.txt

# 或使用 conda
conda create -n stock python=3.10
conda activate stock
pip install -r requirements.txt
```

### 命令列參數

```bash
python main.py                        # 完整分析（個股 + 大盤復盤）
python main.py --market-review        # 僅大盤復盤
python main.py --no-market-review     # 僅個股分析
python main.py --stocks AAPL,TSLA     # 指定股票
python main.py --dry-run              # 僅取得資料，不 AI 分析
python main.py --no-notify            # 不發送推送
python main.py --schedule             # 定時任務模式
python main.py --force-run            # 非交易日也強制執行
python main.py --debug                # 除錯模式（詳細日誌）
python main.py --workers 5            # 指定並發數
```

---

## 定時任務配置

### GitHub Actions 定時

編輯 `.github/workflows/daily_analysis.yml`:

```yaml
schedule:
  # UTC 時間，台灣時間 = UTC + 8
  - cron: '0 14 * * 1-5'   # 週一到週五 22:00（台灣時間）
```

常用時間對照：

| 台灣時間 | UTC cron 表示式 |
|---------|----------------|
| 16:00 | `'0 8 * * 1-5'` |
| 18:00 | `'0 10 * * 1-5'` |
| 20:00 | `'0 12 * * 1-5'` |
| 22:00 | `'0 14 * * 1-5'` |

#### GitHub Actions 非交易日手動執行

`daily_analysis.yml` 支援兩種控制方式：

- `TRADING_DAY_CHECK_ENABLED`：倉庫級配置，預設 `true`
- `workflow_dispatch.force_run`：手動觸發時的單次開關，預設 `false`

| 配置組合 | 非交易日行為 |
|---------|-------------|
| `TRADING_DAY_CHECK_ENABLED=true` + `force_run=false` | 跳過執行（預設行為） |
| `TRADING_DAY_CHECK_ENABLED=true` + `force_run=true` | 本次強制執行 |
| `TRADING_DAY_CHECK_ENABLED=false` | 始終執行 |

手動觸發步驟：

1. 開啟 `Actions → 每日股票分析 → Run workflow`
2. 選擇 `mode`（`full` / `market-only` / `stocks-only`）
3. 若當天為非交易日且希望仍執行，將 `force_run` 設為 `true`
4. 點擊 `Run workflow`

### 本地定時任務

#### 命令列方式

```bash
# 啟動定時模式（啟動時立即執行一次，隨後每天 22:00 執行）
python main.py --schedule

# 啟動定時模式（啟動時不執行，僅等待下次定時觸發）
python main.py --schedule --no-run-immediately
```

#### 環境變數方式

| 變數名 | 說明 | 預設值 | 範例 |
|--------|------|:-------:|:-----:|
| `SCHEDULE_ENABLED` | 是否啟用定時任務 | `false` | `true` |
| `SCHEDULE_TIME` | 每日執行時間 (HH:MM)，台灣時間 | `22:00` | `20:00` |
| `SCHEDULE_RUN_IMMEDIATELY` | 啟動服務時是否立即執行一次 | `true` | `false` |
| `TRADING_DAY_CHECK_ENABLED` | 交易日檢查 | `true` | `false` |

#### 交易日判斷

預設根據美股交易日曆（含節假日）判斷是否為交易日：
- 使用 `exchange-calendars` 判斷美股交易日
- 非交易日時整體跳過執行
- 覆蓋方式：`TRADING_DAY_CHECK_ENABLED=false` 或命令列 `--force-run`

#### 使用 Crontab

```bash
crontab -e
# 新增：0 22 * * 1-5 cd /path/to/project && python main.py
```

---

## 通知管道詳細配置

### Telegram

1. 與 @BotFather 對話建立 Bot
2. 取得 Bot Token
3. 取得 Chat ID（可透過 @userinfobot）
4. 設定 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`
5. （可選）如需發送到 Topic，設定 `TELEGRAM_MESSAGE_THREAD_ID`

### 電子郵件

1. 開啟信箱的 SMTP 服務
2. 取得授權碼（非登入密碼）
3. 設定 `EMAIL_SENDER`、`EMAIL_PASSWORD`、`EMAIL_RECEIVERS`

支援的信箱：
- Gmail：smtp.gmail.com:587
- Outlook：smtp.office365.com:587
- 163 信箱：smtp.163.com:465

**股票分組發往不同信箱**（可選）：

```bash
STOCK_GROUP_1=AAPL,TSLA
EMAIL_GROUP_1=user1@example.com
STOCK_GROUP_2=NVDA,MSFT
EMAIL_GROUP_2=user2@example.com
```

### 自訂 Webhook

支援任意 POST JSON 的 Webhook，包括：
- Discord Webhook
- Slack Webhook
- Bark（iOS 推送）
- 自建服務

設定 `CUSTOM_WEBHOOK_URLS`，多個用逗號分隔。

### Discord

**方式一：Webhook（推薦，簡單）**

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
```

**方式二：Bot API**

```bash
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
```

### Pushover（iOS/Android 推送）

```bash
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_API_TOKEN=your_api_token
```

### Markdown 轉圖片（可選）

配置 `MARKDOWN_TO_IMAGE_CHANNELS` 可將報告以圖片形式發送至不支援 Markdown 的管道。

**依賴安裝**：

1. **wkhtmltopdf**（預設引擎）：
   - macOS：`brew install wkhtmltopdf`
   - Debian/Ubuntu：`apt install wkhtmltopdf`
2. **markdown-to-file**（可選，emoji 支援更好）：`npm i -g markdown-to-file`，並設定 `MD2IMG_ENGINE=markdown-to-file`

---

## 資料來源配置

### YFinance（預設）

- 免費，無需配置
- 支援美股歷史資料與即時行情
- 美股歷史資料與即時行情均統一使用 YFinance

---

## 進階功能

### ETF 與指數分析

針對指數跟蹤型 ETF 和美股指數（如 VOO、QQQ、SPY、SPX、DJI、IXIC），分析僅關注**指數走勢、跟蹤誤差、市場流動性**，不納入基金管理人的公司層面風險。

### 多模型切換

```bash
# Gemini（主力）
GEMINI_API_KEY=xxx
GEMINI_MODEL=gemini-3-flash-preview

# OpenAI 相容（備選）
OPENAI_API_KEY=xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### LiteLLM 直接整合（多模型 + 多 Key 負載均衡）

**多 Key + 跨模型降級配置範例**：

```env
# 主模型：3 個 Gemini Key 輪換
GEMINI_API_KEYS=key1,key2,key3
LITELLM_MODEL=gemini/gemini-3-flash-preview

# 跨模型降級：主模型全部 Key 均失敗時，按序嘗試 Claude → GPT
LITELLM_FALLBACK_MODELS=anthropic/claude-3-5-sonnet-20241022,openai/gpt-4o-mini
```

### 除錯模式

```bash
python main.py --debug
```

日誌檔案位置：
- 常規日誌：`logs/stock_analysis_YYYYMMDD.log`
- 除錯日誌：`logs/stock_analysis_debug_YYYYMMDD.log`

---

## 回測功能

回測模組自動對歷史 AI 分析記錄進行事後驗證，評估分析建議的準確性。

### 工作原理

1. 選取已過冷卻期（預設 14 天）的 `AnalysisHistory` 記錄
2. 取得分析日之後的日線資料（前向 K 線）
3. 根據操作建議推斷預期方向，與實際走勢對比
4. 評估止盈/止損命中情況，模擬執行收益
5. 彙總為整體和單股兩個維度的表現指標

### 操作建議對應

| 操作建議 | 倉位推斷 | 預期方向 | 勝利條件 |
|---------|---------|---------|---------|
| 買入/加倉/strong buy | long | up | 漲幅 ≥ 中性帶 |
| 賣出/減倉/strong sell | cash | down | 跌幅 ≥ 中性帶 |
| 持有/hold | long | not_down | 未顯著下跌 |
| 觀望/等待/wait | cash | flat | 價格在中性帶內 |

### 配置

| 變數 | 預設值 | 說明 |
|------|-------|------|
| `BACKTEST_ENABLED` | `true` | 是否在每日分析後自動執行回測 |
| `BACKTEST_EVAL_WINDOW_DAYS` | `10` | 評估窗口（交易日數） |
| `BACKTEST_MIN_AGE_DAYS` | `14` | 僅回測 N 天前的記錄 |
| `BACKTEST_ENGINE_VERSION` | `v1` | 引擎版本號 |
| `BACKTEST_NEUTRAL_BAND_PCT` | `2.0` | 中性區間閾值（%） |

### 評估指標

| 指標 | 說明 |
|------|------|
| `direction_accuracy_pct` | 方向預測準確率 |
| `win_rate_pct` | 勝率 |
| `avg_stock_return_pct` | 平均股票收益率 |
| `avg_simulated_return_pct` | 平均模擬執行收益率 |
| `stop_loss_trigger_rate` | 止損觸發率 |
| `take_profit_trigger_rate` | 止盈觸發率 |

---

## FastAPI API 服務

### 啟動方式

| 命令 | 說明 |
|------|------|
| `python main.py --serve` | 啟動 API 服務 + 執行一次完整分析 |
| `python main.py --serve-only` | 僅啟動 API 服務，手動觸發分析 |
| `python main.py --webui` | 啟動 Web 介面 + 定時分析 |
| `python main.py --webui-only` | 僅啟動 Web 介面，不自動執行分析 |

### API 介面

| 介面 | 方法 | 說明 |
|------|------|------|
| `/api/v1/analysis/analyze` | POST | 觸發股票分析 |
| `/api/v1/analysis/tasks` | GET | 查詢任務列表 |
| `/api/v1/analysis/status/{task_id}` | GET | 查詢任務狀態 |
| `/api/v1/history` | GET | 查詢分析歷史 |
| `/api/v1/backtest/run` | POST | 觸發回測 |
| `/api/v1/backtest/results` | GET | 查詢回測結果（分頁） |
| `/api/v1/backtest/performance` | GET | 取得整體回測表現 |
| `/api/v1/backtest/performance/{code}` | GET | 取得單股回測表現 |
| `/api/v1/stocks/extract-from-image` | POST | 從圖片提取股票代碼 |
| `/api/health` | GET | 健康檢查 |
| `/docs` | GET | API Swagger 文件 |

**呼叫範例**：
```bash
# 健康檢查
curl http://127.0.0.1:8000/api/health

# 觸發分析
curl -X POST http://127.0.0.1:8000/api/v1/analysis/analyze \
  -H 'Content-Type: application/json' \
  -d '{"stock_code": "AAPL"}'

# 查詢整體回測表現
curl http://127.0.0.1:8000/api/v1/backtest/performance

# 查詢單股回測表現
curl http://127.0.0.1:8000/api/v1/backtest/performance/AAPL
```

### 支援的股票代碼格式

| 類型 | 格式 | 範例 |
|------|------|------|
| 美股 | 1-5 字母（可選 .X 後綴） | `AAPL`、`TSLA`、`BRK.B` |
| 美股指數 | SPX/DJI/IXIC 等 | `SPX`、`DJI`、`NASDAQ`、`VIX` |

---

## 常見問題

### Q: 資料取得失敗？
A: YFinance 偶爾會有連線問題，系統已配置重試機制，一般等待幾分鐘後重試即可。

### Q: 如何新增自選股？
A: 修改 `STOCK_LIST` 環境變數，多個代碼用逗號分隔。

### Q: GitHub Actions 沒有執行？
A: 檢查是否啟用了 Actions，以及 cron 表示式是否正確（注意是 UTC 時間）。

### Q: 如何只看 Web 介面不自動分析？
A: 使用 `python main.py --webui-only`，手動從介面觸發分析。
