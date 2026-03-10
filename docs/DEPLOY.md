# 🚀 部署指南

本文件介紹如何將美股自選股智能分析系統部署到伺服器。

## 📋 部署方案比較

| 方案 | 優點 | 缺點 | 推薦場景 |
|------|------|------|----------|
| **直接部署** | 簡單直接、無額外依賴 | 環境依賴、遷移麻煩 | 臨時測試 |
| **Systemd 服務** | 系統級管理、開機自啟 | 配置繁瑣 | 長期穩定運行 |
| **Supervisor** | 行程管理、自動重啟 | 需要額外安裝 | 多行程管理 |

---

## 🖥️ 方案一：直接部署

### 1. 安裝 Python 環境

```bash
# 安裝 Python 3.10+
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip

# 建立虛擬環境
python3.10 -m venv /opt/stock-analyzer/venv
source /opt/stock-analyzer/venv/bin/activate
```

### 2. 安裝依賴

```bash
cd /opt/stock-analyzer
pip install -r requirements.txt
```

### 3. 配置環境變數

```bash
cp .env.example .env
vim .env  # 填入配置
```

### 4. 執行

```bash
# 單次執行
python main.py

# 定時任務模式（前台執行）
python main.py --schedule

# 背景執行（使用 nohup）
nohup python main.py --schedule > /dev/null 2>&1 &
```

---

## 🔧 方案二：Systemd 服務

建立 systemd 服務檔案實現開機自啟和自動重啟：

### 1. 建立服務檔案

```bash
sudo vim /etc/systemd/system/stock-analyzer.service
```

內容：
```ini
[Unit]
Description=美股自選股智能分析系統
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stock-analyzer
Environment="PATH=/opt/stock-analyzer/venv/bin"
ExecStart=/opt/stock-analyzer/venv/bin/python main.py --schedule
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### 2. 啟動服務

```bash
# 重載配置
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start stock-analyzer

# 開機自啟
sudo systemctl enable stock-analyzer

# 查看狀態
sudo systemctl status stock-analyzer

# 查看日誌
journalctl -u stock-analyzer -f
```

---

## ⚙️ 配置說明

### 必須配置項

| 配置項 | 說明 | 取得方式 |
|--------|------|----------|
| `GEMINI_API_KEY` | AI 分析必需 | [Google AI Studio](https://aistudio.google.com/) |
| `STOCK_LIST` | 自選股清單 | 逗號分隔的股票代碼 |

### 可選配置項

| 配置項 | 預設值 | 說明 |
|--------|--------|------|
| `SCHEDULE_ENABLED` | `false` | 是否啟用定時任務 |
| `SCHEDULE_TIME` | `22:00` | 每日執行時間 |
| `MARKET_REVIEW_ENABLED` | `true` | 是否啟用大盤復盤 |
| `TAVILY_API_KEYS` | - | 新聞搜索（可選） |

---

## 🌐 代理配置

如果伺服器需要代理才能存取 Gemini API：

### 直接部署方式

編輯 `main.py` 頂部：
```python
os.environ["http_proxy"] = "http://your-proxy:port"
os.environ["https_proxy"] = "http://your-proxy:port"
```

---

## 📊 監控與維護

### 日誌查看

```bash
tail -f /opt/stock-analyzer/logs/stock_analysis_*.log
```

### 健康檢查

```bash
# 檢查行程
ps aux | grep main.py

# 檢查最近的報告
ls -la /opt/stock-analyzer/reports/
```

### 定期維護

```bash
# 清理舊日誌（保留 7 天）
find /opt/stock-analyzer/logs -mtime +7 -delete

# 清理舊報告（保留 30 天）
find /opt/stock-analyzer/reports -mtime +30 -delete
```

---

## ❓ 常見問題

### 1. API 存取逾時

檢查代理配置，確保伺服器能存取 Gemini API。

### 2. 資料庫鎖定

```bash
# 停止服務後刪除 lock 檔案
rm /opt/stock-analyzer/data/*.lock
```

---

## 🔄 快速遷移

從一台伺服器遷移到另一台：

```bash
# 來源伺服器：打包
cd /opt/stock-analyzer
tar -czvf stock-analyzer-backup.tar.gz .env data/ logs/ reports/

# 目標伺服器：部署
mkdir -p /opt/stock-analyzer
cd /opt/stock-analyzer
git clone <your-repo-url> .
tar -xzvf stock-analyzer-backup.tar.gz
```

---

## ☁️ 方案三：GitHub Actions 部署（免伺服器）

**最簡單的方案！** 無需伺服器，利用 GitHub 免費運算資源。

### 優勢
- ✅ **完全免費**（每月 2000 分鐘）
- ✅ **無需伺服器**
- ✅ **自動定時執行**
- ✅ **零維護成本**

### 限制
- ⚠️ 無狀態（每次執行是新環境）
- ⚠️ 定時可能有幾分鐘延遲
- ⚠️ 無法提供 HTTP API

### 部署步驟

#### 1. 建立 GitHub 倉庫

```bash
# 初始化 git（如果還沒有）
cd /path/to/daily-stock-analysis
git init
git add .
git commit -m "Initial commit"

# 建立 GitHub 倉庫並推送
git remote add origin https://github.com/你的帳號/daily-stock-analysis.git
git branch -M main
git push -u origin main
```

#### 2. 配置 Secrets（重要！）

開啟倉庫頁面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

新增以下 Secrets：

| Secret 名稱 | 說明 | 必填 |
|------------|------|------|
| `GEMINI_API_KEY` | Gemini AI API Key | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 可選* |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | 可選* |
| `TELEGRAM_MESSAGE_THREAD_ID` | Telegram Topic ID | 可選* |
| `EMAIL_SENDER` | 寄件人信箱 | 可選* |
| `EMAIL_PASSWORD` | 信箱授權碼 | 可選* |
| `CUSTOM_WEBHOOK_URLS` | 自訂 Webhook（多個逗號分隔） | 可選* |
| `STOCK_LIST` | 自選股清單，如 `AAPL,TSLA` | ✅ |
| `TAVILY_API_KEYS` | Tavily 搜索 API Key | 推薦 |
| `SERPAPI_API_KEYS` | SerpAPI Key | 可選 |
| `GEMINI_MODEL` | 模型名稱（預設 gemini-2.0-flash） | 可選 |

> *注：通知渠道至少配置一個，支援多渠道同時推送

#### 3. 驗證 Workflow 檔案

確保 `.github/workflows/daily_analysis.yml` 存在且已提交：

```bash
git add .github/workflows/daily_analysis.yml
git commit -m "Add GitHub Actions workflow"
git push
```

#### 4. 手動測試執行

1. 開啟倉庫頁面 → **Actions** 標籤
2. 選擇 **「每日股票分析」** workflow
3. 點擊 **「Run workflow」** 按鈕
4. 選擇執行模式：
   - `full` - 完整分析（股票 + 大盤）
   - `market-only` - 僅大盤復盤
   - `stocks-only` - 僅股票分析
5. 點擊綠色 **「Run workflow」** 按鈕

#### 5. 查看執行日誌

- Actions 頁面可以看到執行歷史
- 點擊具體的執行記錄查看詳細日誌
- 分析報告會作為 Artifact 保存 30 天

### 定時說明

預設配置：**週一到週五，台灣時間 22:00** 自動執行

修改時間：編輯 `.github/workflows/daily_analysis.yml` 中的 cron 表達式：

```yaml
schedule:
  - cron: '0 14 * * 1-5'  # UTC 時間，+8 = 台灣時間
```

常用 cron 範例：
| 表達式 | 說明 |
|--------|------|
| `'0 14 * * 1-5'` | 週一到週五 22:00（台灣時間） |
| `'30 7 * * 1-5'` | 週一到週五 15:30（台灣時間） |
| `'0 14 * * *'` | 每天 22:00（台灣時間） |
| `'0 2 * * 1-5'` | 週一到週五 10:00（台灣時間） |

### 修改自選股

方法一：修改倉庫 Secret `STOCK_LIST`

方法二：直接修改程式碼後推送：
```bash
# 修改 .env.example 或在程式碼中設定預設值
git commit -am "Update stock list"
git push
```

### 常見問題

**Q：為什麼定時任務沒有執行？**
A：GitHub Actions 定時任務可能有 5-15 分鐘延遲，且僅在倉庫有活動時才觸發。長時間無 commit 可能導致 workflow 被停用。

**Q：如何查看歷史報告？**
A：Actions → 選擇執行記錄 → Artifacts → 下載 `analysis-reports-xxx`

**Q：免費額度夠用嗎？**
A：每次執行約 2-5 分鐘，一個月 22 個工作日 = 44-110 分鐘，遠低於 2000 分鐘限制。

---

**祝部署順利！🎉**
