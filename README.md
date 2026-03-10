<div align="center">

# 📈 股票智能分析系統

[![GitHub stars](https://img.shields.io/github/stars/JacobHsu/daily-stock-analysis?style=social)](https://github.com/JacobHsu/daily-stock-analysis/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Ready-2088FF?logo=github-actions&logoColor=white)](https://github.com/features/actions)


> 🤖 基於 AI 大模型的美股自選股智能分析系統，每日自動分析並推送「決策儀表板」到 Telegram / Discord / 郵件

[**功能特性**](#-功能特性) · [**快速開始**](#-快速開始) · [**推送效果**](#-推送效果) · [**完整指南**](docs/full-guide.md) · [**常見問題**](docs/FAQ.md) · [**更新日誌**](docs/CHANGELOG.md)

繁體中文 | [English](docs/README_EN.md)

</div>


## ✨ 功能特性

| 模組 | 功能 | 說明 |
|------|------|------|
| AI | 決策儀表板 | 一句話核心結論 + 精確買賣點位 + 操作檢查清單 |
| 分析 | 多維度分析 | 技術面（均線/多頭排列）+ 籌碼分布 + 輿情情報 + 實時行情 |
| 市場 | 美股市場 | 支援美股個股、ETF 及美股指數（SPX、DJI、IXIC 等） |
| 策略 | 市場策略系統 | 內建「Regime Strategy」，輸出 risk-on/neutral/risk-off 計劃 |
| 復盤 | 大盤復盤 | 每日美股市場概覽、板塊漲跌 |
| 圖片識別 | 從圖片新增 | 上傳自選股截圖，Vision AI 自動提取股票代碼 |
| 回測 | AI 回測驗證 | 自動評估歷史分析準確率，方向勝率、止盈止損命中率 |
| **Agent 問股** | **策略對話** | **多輪策略問答，支援 11 種內建策略，Web/Bot/API 全鏈路** |
| 推送 | 多渠道通知 | Telegram、Discord、郵件、Pushover |
| 自動化 | 定時運行 | GitHub Actions 定時執行，無需伺服器 |

### 技術棧與數據來源

| 類型 | 支援 |
|------|------|
| AI 模型 | [AIHubMix](https://aihubmix.com/?aff=CfMq)（推薦）、Gemini、OpenAI 兼容、DeepSeek、Claude（統一透過 [LiteLLM](https://github.com/BerriAI/litellm) 呼叫） |
| 行情數據 | YFinance（美股主力）、AkShare |
| 新聞搜索 | Tavily、SerpAPI、Brave |

### 內建交易紀律

| 規則 | 說明 |
|------|------|
| 嚴禁追高 | 乖離率超閾值（預設 5%）自動提示風險；強勢趨勢股自動放寬 |
| 趨勢交易 | MA5 > MA10 > MA20 多頭排列 |
| 精確點位 | 買入價、止損價、目標價 |
| 檢查清單 | 每項條件以「符合 / 注意 / 不符合」標記 |

## 🚀 快速開始

### 方式一：GitHub Actions（推薦）

> 5 分鐘完成部署，零成本，無需伺服器。

#### 1. Fork 本倉庫

點擊右上角 `Fork` 按鈕（順便點個 Star⭐ 支持一下）

#### 2. 配置 Secrets

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

**AI 模型配置（至少配置一個）**

> 💡 **推薦 [AIHubMix](https://aihubmix.com/?aff=CfMq)**：一個 Key 即可使用 Gemini、GPT、Claude、DeepSeek 等全球主流模型，無需科學上網，含免費模型。

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `AIHUBMIX_KEY` | [AIHubMix](https://aihubmix.com/?aff=CfMq) API Key | 推薦 |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) 免費 Key | 可選 |
| `ANTHROPIC_API_KEY` | [Anthropic Claude](https://console.anthropic.com/) API Key | 可選 |
| `OPENAI_API_KEY` | OpenAI 兼容 API Key | 可選 |
| `OPENAI_BASE_URL` | OpenAI 兼容 API 地址（使用 AIHubMix 時無需填寫） | 可選 |
| `OPENAI_MODEL` | 模型名稱（如 `gpt-4o-mini`） | 可選 |

> 注：AI 優先級 Gemini > Anthropic > OpenAI（含 AIHubMix），至少配置一個。

<details>
<summary><b>通知渠道配置</b>（點擊展開，至少配置一個）</summary>

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token（@BotFather 獲取） | 可選 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可選 |
| `TELEGRAM_MESSAGE_THREAD_ID` | Telegram Topic ID（用於發送到子話題） | 可選 |
| `EMAIL_SENDER` | 發件人郵箱 | 可選 |
| `EMAIL_PASSWORD` | 郵箱授權碼（非登入密碼） | 可選 |
| `EMAIL_RECEIVERS` | 收件人郵箱（多個用逗號分隔，留空則發給自己） | 可選 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL | 可選 |
| `DISCORD_BOT_TOKEN` | Discord Bot Token（與 Webhook 二選一） | 可選 |
| `DISCORD_MAIN_CHANNEL_ID` | Discord Channel ID（使用 Bot 時需要） | 可選 |
| `CUSTOM_WEBHOOK_URLS` | 自定義 Webhook（支持 Slack、Bark 等，多個用逗號分隔） | 可選 |
| `PUSHOVER_USER_KEY` | Pushover User Key | 可選 |
| `PUSHOVER_API_TOKEN` | Pushover API Token | 可選 |
| `SINGLE_STOCK_NOTIFY` | 單股推送模式：設為 `true` 則每分析完一支股票立即推送 | 可選 |
| `REPORT_TYPE` | 報告類型：`simple`（精簡）或 `full`（完整） | 可選 |
| `ANALYSIS_DELAY` | 個股分析之間的延遲（秒），避免 API 限流，如 `10` | 可選 |

> 至少配置一個渠道，配置多個則同時推送。

</details>

**其他配置**

| Secret 名稱 | 說明 | 必填 |
|------------|------|:----:|
| `STOCK_LIST` | 自選股代碼，如 `AAPL,TSLA,DIS,VOO` | ✅ |
| `TAVILY_API_KEYS` | [Tavily](https://tavily.com/) 搜索 API（新聞搜索，免費 1000 次/月） | 推薦 |
| `BRAVE_API_KEYS` | [Brave Search](https://brave.com/search/api/) API（美股優化，免費 2000 次/月） | 可選 |
| `SERPAPI_API_KEYS` | [SerpAPI](https://serpapi.com/) 備用搜索 | 可選 |
| `MARKET_REVIEW_REGION` | 大盤復盤市場，設為 `us` 僅看美股 | 推薦 |
| `TRADING_DAY_CHECK_ENABLED` | 交易日檢查（預設 `true`）：非交易日跳過執行；設為 `false` 強制執行 | 可選 |
| `AGENT_MODE` | 啟用 Agent 策略問股模式（`true`/`false`，預設 `false`） | 可選 |
| `AGENT_SKILLS` | 啟用的策略（逗號分隔），`all` 啟用全部 11 個 | 可選 |

#### 3. 啟用 Actions

`Actions` 標籤 → `I understand my workflows, go ahead and enable them`

#### 4. 手動測試

`Actions` → `每日股票分析` → `Run workflow` → `Run workflow`

#### 完成

預設每個**工作日 22:00（台灣時間）**自動執行，也可手動觸發。

> 💡 **跳過交易日檢查的兩種方式：**
> | 方式 | 設定 | 適用場景 |
> |------|------|----------|
> | `TRADING_DAY_CHECK_ENABLED=false` | 環境變數/Secrets | 測試環境、長期關閉 |
> | `force_run`（UI 勾選） | Actions 手動觸發時選擇 | 臨時在非交易日執行一次 |

### 方式二：本地運行 

```bash
# 複製專案
git clone https://github.com/JacobHsu/daily-stock-analysis.git && cd daily-stock-analysis

# 安裝依賴
pip install -r requirements.txt

# 配置環境變數
cp .env.example .env
# 編輯 .env 填入你的 API Keys

# 執行分析
python main.py
```

> Docker 部署、定時任務配置請參考 [完整指南](docs/full-guide.md)

## 📱 推送效果

### 決策儀表板
```
🎯 2026-03-08 決策儀表板
共分析 3 支股票 | 🟢買入:1 🟡觀望:2 🔴賣出:0

📊 分析結果摘要
🟢 Apple Inc.(AAPL): 買入 | 評分 78 | 看多
⚪ Tesla(TSLA): 觀望 | 評分 52 | 震盪
⚪ Vanguard S&P 500 ETF(VOO): 觀望 | 評分 61 | 看多

🟢 Apple Inc. (AAPL)
📰 重要資訊速覽
💭 輿情情緒: 市場對 Apple Intelligence 功能持樂觀態度，iPhone 升級週期預期強勁。
📊 業績預期: 下季財報預計 EPS $2.35，分析師預期上調。

🚨 風險警報:
- 風險點1：中美貿易摩擦可能影響供應鏈成本。
- 風險點2：Vision Pro 銷售低於預期，硬體多元化壓力。

✨ 利好催化:
- 利好1：AI 功能帶動 iPhone 升級需求，預計週期強勁。
- 利好2：服務收入持續高速增長，佔比提升。

📢 最新動態: Apple 宣布新一輪股票回購計劃，規模達 $900 億美元。

---
報告生成時間：2026-03-08 18:00:00
```

### 大盤復盤（美股）
```
🎯 2026-03-08 美股大盤復盤

📊 主要指數
- S&P 500: 5850.12 (🟢+0.85%)
- Nasdaq: 18521.36 (🟢+1.02%)
- Dow Jones: 43156.78 (🟢+0.45%)

🔥 板塊表現
領漲: 科技、通訊服務、非必需消費品
領跌: 公用事業、能源、金融
```

## ⚙️ 配置說明

> 📖 完整環境變數、定時任務配置請參考 [完整配置指南](docs/full-guide.md)


## 🖥️ Web 介面

![img.png](sources/fastapi_server.png)

包含完整的配置管理、任務監控和手動分析功能。

**可選密碼保護**：在 `.env` 中設置 `ADMIN_AUTH_ENABLED=true` 可啟用 Web 登入保護。詳見 [完整指南](docs/full-guide.md)。

### 從圖片新增股票

在 **設定 → 基礎設定** 中找到「從圖片新增」區塊，拖曳或選擇截圖，系統透過 Vision AI 自動識別股票代碼並加入自選清單。

**限制**：需配置支援 Vision 能力的模型；圖片最大 5MB，請求超時 60 秒。

### 🤖 Agent 策略問股

在 `.env` 中設置 `AGENT_MODE=true` 後啟動服務，訪問 `/chat` 頁面即可開始多輪策略問答。

- **選擇策略**：均線金叉、多頭趨勢、波浪理論等 11 種內建策略
- **自然語言提問**：如「用均線金叉分析 AAPL」，Agent 自動呼叫實時行情、技術指標、新聞等工具
- **流式進度回饋**：實時展示 AI 思考路徑
- **多輪對話**：支援追問上下文，對話歷史持久保存

### 啟動方式

```bash
python main.py               # 執行分析（產生資料）
python main.py --webui-only  # 啟動 Web 介面查看結果
python main.py --webui       # 執行分析 + 啟動 Web 介面（一次完成）
```

訪問 `http://127.0.0.1:8000` 即可使用。

### 🔌 API 端點

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

## 📁 專案結構

```text
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

查看已支援的功能和未來規劃：[更新日誌](docs/CHANGELOG.md)

> 有建議？歡迎 [提交 Issue](https://github.com/JacobHsu/daily-stock-analysis/issues)

---

## ---


## 📄 License
[MIT License](LICENSE) © 2026 ZhuLinsen, JacobHsu


## 致謝

本專案改寫自 [daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) by [@ZhuLinsen](https://github.com/ZhuLinsen)，依 MIT License 授權使用並進行修改。

## 免責聲明

本專案僅供學習和研究使用，不構成任何投資建議。股市有風險，投資需謹慎。作者不對使用本專案產生的任何損失負責。

---
