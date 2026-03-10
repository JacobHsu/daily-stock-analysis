<div align="center">

# 股票智能分析系統

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Ready-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)


**基於 AI 大模型的美股智能分析系統**

自動分析自選股 → 生成決策儀表盤 → 多渠道推送（Telegram / Discord / 郵件）

**零成本部署** · GitHub Actions 免費運行 · 無需伺服器

[**功能特性**](#-功能特性) · [**快速開始**](#-快速開始) · [**推送效果**](#-推送效果) · [**完整指南**](full-guide.md) · [**常見問題**](FAQ.md) · [**更新日誌**](CHANGELOG.md)


</div>

## 💖 贊助商 (Sponsors)

<div align="center">
  <a href="https://serpapi.com/baidu-search-api?utm_source=github_daily_stock_analysis" target="_blank">
    <img src="../sources/serpapi_banner_zh.png" alt="輕鬆抓取搜尋引擎上的即時金融新聞數據 - SerpApi" height="160">
  </a>
</div>
<br>

## ✨ 功能特性

| 模組 | 功能 | 說明 |
|------|------|------|
| AI | 決策儀表盤 | 一句話核心結論 + 精確買賣點位 + 操作檢查清單 |
| 分析 | 多維度分析 | 技術面 + 籌碼分布 + 輿情情報 + 實時行情 |
| 市場 | 美股市場 | 專注美股，支援個股、ETF 及美股指數 |
| 復盤 | 大盤復盤 | 每日美股市場概覽、板塊漲跌 |
| 回測 | AI 回測驗證 | 自動評估歷史分析準確率，方向勝率、止盈止損命中率 |
| **Agent 問股** | **策略對話** | **多輪策略問答，支援 11 種內建策略（Web/Bot/API）** |
| 推送 | 多渠道通知 | Telegram、Discord、郵件 |
| 自動化 | 定時運行 | GitHub Actions 定時執行，無需伺服器 |

### 技術棧與數據來源

| 類型 | 支援 |
|------|------|
| AI 模型 | AIHubMix（推薦）、Gemini、OpenAI 兼容、DeepSeek、Claude |
| 行情數據 | YFinance（美股主力）、AkShare |
| 新聞搜索 | Tavily（推薦）、Brave、SerpAPI |

### 內建交易紀律

| 規則 | 說明 |
|------|------|
| 嚴禁追高 | 乖離率 > 5% 自動提示風險 |
| 趨勢交易 | MA5 > MA10 > MA20 多頭排列 |
| 精確點位 | 買入價、止損價、目標價 |
| 檢查清單 | 每項條件以「符合 / 注意 / 不符合」標記 |

## 🚀 快速開始

### 方式一：GitHub Actions（推薦）

**無需伺服器，每天自動運行！**

#### 1. Fork 本倉庫

點擊右上角 `Fork` 按鈕（順便點個 Star 支持一下）

#### 2. 配置 Secrets

進入你 Fork 的倉庫 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

**AI 模型配置（至少配置一個）**

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `AIHUBMIX_KEY` | [AIHubMix](https://aihubmix.com/) API Key，一個 Key 可用 GPT/Claude/Gemini 等全系模型 | 推薦 |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) 免費 Key | 可選 |
| `OPENAI_API_KEY` | OpenAI 兼容 API Key | 可選 |
| `OPENAI_BASE_URL` | OpenAI 兼容 API 地址（使用 AIHubMix 時無需填寫） | 可選 |
| `OPENAI_MODEL` | 模型名稱（如 `gpt-4o-mini`） | 可選 |

<details>
<summary><b>通知渠道配置</b>（點擊展開，至少配置一個）</summary>

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（@BotFather 獲取） | 可選 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可選 |
| `TELEGRAM_MESSAGE_THREAD_ID` | Telegram Topic ID（用於發送到子話題） | 可選 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可選 |
| `DISCORD_BOT_TOKEN` | Discord Bot Token（與 Webhook 二選一） | 可選 |
| `DISCORD_CHANNEL_ID` | Discord Channel ID（使用 Bot 時需要） | 可選 |
| `EMAIL_SENDER` | 發件人郵箱 | 可選 |
| `EMAIL_PASSWORD` | 郵箱授權碼（非登入密碼） | 可選 |
| `EMAIL_RECEIVERS` | 收件人郵箱（多個用逗號分隔，留空則發給自己） | 可選 |
| `CUSTOM_WEBHOOK_URLS` | 自定義 Webhook（支持 Discord、Slack 等，多個用逗號分隔） | 可選 |
| `SINGLE_STOCK_NOTIFY` | 單股推送模式：設為 `true` 則每分析完一支股票立即推送 | 可選 |
| `REPORT_TYPE` | 報告類型：`simple`（精簡）或 `full`（完整） | 可選 |
| `ANALYSIS_DELAY` | 個股分析之間的延遲（秒），避免 API 限流，如 `10` | 可選 |

> 至少配置一個渠道，配置多個則同時推送。更多配置請參考 [完整指南](full-guide.md)

</details>

**其他配置**

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `STOCK_LIST` | 自選股代碼，如 `AAPL,TSLA,DIS,VOO` | ✅ |
| `TAVILY_API_KEYS` | [Tavily](https://tavily.com/) 搜索 API（新聞搜索，免費 1000 次/月） | 推薦 |
| `BRAVE_API_KEYS` | [Brave Search](https://brave.com/search/api/) API（隱私優先，美股優化，免費 2000 次/月） | 可選 |
| `SERPAPI_API_KEYS` | [SerpAPI](https://serpapi.com/) 備用搜索 | 可選 |
| `MARKET_REVIEW_REGION` | 大盤復盤市場：設為 `us` 僅看美股 | 推薦 |
| `AGENT_MODE` | 啟用 Agent 策略問股模式（`true`/`false`，預設 `false`） | 可選 |
| `AGENT_MAX_STEPS` | Agent 最大推理步數（預設 `10`） | 可選 |

#### 3. 啟用 Actions

進入 `Actions` 標籤 → 點擊 `I understand my workflows, go ahead and enable them`

#### 4. 手動測試

`Actions` → `每日股票分析` → `Run workflow` → 選擇模式 → `Run workflow`

#### 5. 完成！

預設每個工作日 **22:00（台灣時間）/ 美東 10:00** 自動執行，可在 workflow 檔案中調整時區

### 方式二：本地運行 / Docker 部署

> 📖 本地運行、Docker 部署詳細步驟請參考 [完整配置指南](full-guide.md)

## 📱 推送效果

### 決策儀表板
```
🎯 2026-01-10 決策儀表板
共分析 3 支股票 | 🟢買入:1 🟡觀望:2 🔴賣出:0

🟢 買入 | Apple Inc.(AAPL)
📌 縮量回踩MA5支撐，乖離率1.2%處於最佳買點
💰 狙擊: 買入$215 | 止損$208 | 目標$228
✅多頭排列 ✅乖離安全 ✅量能配合

🟡 觀望 | Tesla(TSLA)
📌 乖離率7.8%超過5%警戒線，嚴禁追高
⚠️ 等待回調至MA5附近再考慮

---
報告生成時間: 2026-01-10 18:00:00
```

### 大盤復盤（美股）

```
🎯 2026-01-10 美股大盤復盤

📊 主要指數
- S&P 500: 5850.12 (🟢+0.85%)
- Nasdaq: 18521.36 (🟢+1.02%)
- Dow Jones: 43156.78 (🟢+0.45%)

🔥 板塊表現
領漲: 科技、通訊服務、非必需消費品
領跌: 公用事業、能源、金融
```

## 配置說明

> 📖 完整環境變數、定時任務配置請參考 [完整配置指南](full-guide.md)

## 🧩 FastAPI Web 服務（可選）

本地運行時，可啟用 FastAPI 服務來管理配置和觸發分析。

### 啟動方式

| 命令 | 說明 |
|------|------|
| `python main.py --serve` | 啟動 API 服務 + 執行一次完整分析 |
| `python main.py --serve-only` | 僅啟動 API 服務，手動觸發分析 |

- 訪問地址：`http://127.0.0.1:8000`
- API 文檔：`http://127.0.0.1:8000/docs`

### 功能特性

- 📝 **配置管理** - 查看/修改自選股列表
- 🚀 **快速分析** - 透過 API 介面觸發分析
- 📊 **實時進度** - 分析任務狀態實時更新，支援多任務並行
- 🤖 **Agent 策略對話** - 啟用 `AGENT_MODE=true` 後可在 `/chat` 進行多輪問答
- 📈 **回測驗證** - 評估歷史分析準確率，查詢方向勝率與模擬收益

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/v1/analysis/analyze` | POST | 觸發股票分析 |
| `/api/v1/analysis/tasks` | GET | 查詢任務列表 |
| `/api/v1/analysis/status/{task_id}` | GET | 查詢任務狀態 |
| `/api/v1/history` | GET | 查詢分析歷史記錄 |
| `/api/v1/backtest/run` | POST | 觸發回測 |
| `/api/v1/backtest/results` | GET | 查詢回測結果（分頁） |
| `/api/v1/backtest/performance` | GET | 獲取整體回測表現 |
| `/api/v1/backtest/performance/{code}` | GET | 獲取單股回測表現 |
| `/api/v1/agent/strategies` | GET | 取得可用策略清單（內建/自訂） |
| `/api/v1/agent/chat/stream` | POST (SSE) | Agent 多輪策略對話（流式） |
| `/api/health` | GET | 健康檢查 |

## 專案結構

```
daily_stock_analysis/
├── main.py              # 主程式入口
├── server.py            # FastAPI 服務入口
├── src/                 # 核心業務程式碼
│   ├── analyzer.py      # AI 分析器（Gemini）
│   ├── config.py        # 配置管理
│   ├── notification.py  # 訊息推送
│   ├── storage.py       # 資料存儲
│   └── ...
├── api/                 # FastAPI API 模組
├── bot/                 # 機器人模組
├── data_provider/       # 資料來源適配器
├── docker/              # Docker 配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                # 專案文件
│   ├── full-guide.md    # 完整配置指南
│   └── ...
└── .github/workflows/   # GitHub Actions
```

## 🗺️ Roadmap

> 📢 以下功能將視後續情況逐步完成，如果你有好的想法或建議，歡迎 [提交 Issue](https://github.com/ZhuLinsen/daily_stock_analysis/issues) 討論！

### 🔔 通知渠道
- [x] Telegram Bot
- [x] Discord（Webhook / Bot）
- [x] 郵件通知（SMTP）
- [x] 自定義 Webhook（支持 Slack、Bark 等）
- [x] iOS/Android 推送（Pushover）
### 🤖 AI 模型支援
- [x] Google Gemini（主力，免費額度）
- [x] OpenAI 兼容 API（支援 GPT-4/DeepSeek/通義千問/Claude/文心一言 等）
- [x] 本地模型（Ollama）

### 📊 數據源
- [x] YFinance（美股主力）
- [x] AkShare（輔助）

### 🎯 功能增強
- [x] 決策儀表板
- [x] 美股大盤復盤
- [x] 定時推送
- [x] GitHub Actions
- [x] Web 管理介面
- [x] 回測驗證
- [ ] 更多美股策略

## License
[MIT License](../LICENSE) © 2026 ZhuLinsen

如果你在專案中使用或基於本專案進行二次開發，
非常歡迎在 README 或文檔中註明來源並附上本倉庫連結。
這將有助於專案的持續維護和社群發展。

## 免責聲明

本項目僅供學習和研究使用，不構成任何投資建議。股市有風險，投資需謹慎。作者不對使用本項目產生的任何損失負責。


