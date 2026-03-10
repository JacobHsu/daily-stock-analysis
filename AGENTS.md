# AGENTS.md

本檔案定義在本倉庫中執行開發、Issue 分析、PR 審查時的統一行為準則。  

## 1. 通用協作原則

- 語言與棧：Python 3.10+，遵循倉庫現有架構與目錄邊界。
- 配置約束：統一使用 `.env`（參見 `.env.example`）。
- 程式碼質量：優先保證可執行、可迴歸驗證、可追蹤（日誌/錯誤資訊清晰）。
- 風格約束：
  - 行寬 120
  - `black` + `isort` + `flake8`
  - 關鍵變更需至少做語法檢查（`py_compile`）或對應測試驗證。
  - 新增或修改的程式碼註釋必須使用英文。
- Git 約束：
  - 未經明確確認，不執行 `git commit`。
  - commit message 不新增 `Co-Authored-By`。
  - 後續所有 commit message 必須使用英文。

## 2. Issue 分析原則

每個 Issue 必須先回答 3 個問題：

1. 是否合理（Reasonable）
- 是否描述了真實影響（功能錯誤、資料錯誤、效能/穩定性問題、體驗退化）。
- 是否有可驗證證據（日誌、截圖、復現步驟、版本資訊）。
- 是否與專案目標相關（股票分析、資料來源、通知、API/WebUI、部署鏈路）。

2. 是否是 Issue（Valid Issue）
- 屬於缺陷/功能缺失/迴歸/文件錯誤之一，而非純諮詢或環境誤用。
- 能定位到倉庫責任邊界；若是三方服務波動，也需判斷是否需要倉庫側兜底。
- 如果是使用問題，應轉為文件改進或 FAQ，而不是程式碼缺陷。

3. 是否好解決（Solvability）
- 可否穩定復現。
- 依賴是否可控（第三方 API、網路、許可權、金鑰）。
- 變更範圍與風險等級（低/中/高）。
- 是否存在臨時緩解方案（降級、兜底、開關、重試、回退策略）。

### Issue 結論模板

- 結論：`成立 / 部分成立 / 不成立`
- 分類：`bug / feature / docs / question / external`
- 優先順序：`P0 / P1 / P2 / P3`
- 難度：`easy / medium / hard`
- 建議：`立即修復 / 排期修復 / 文件澄清 / 關閉`

## 3. PR 分析原則

每個 PR 需按以下順序審查：

1. 必要性（Necessity）
- 是否解決明確問題，或提供明確業務價值。
- 是否避免“為了改而改”的重構。

2. 關聯性（Traceability）
- 是否關聯對應 Issue（建議必須有：`Fixes #xxx` 或 `Refs #xxx`）。
- 若無 Issue，PR 描述必須給出動機、場景與驗收標準。

3. 型別判定（Type）
- 明確標註：`fix / feat / refactor / docs / chore / test`。
- 對“fix/bug”類 PR：必須說明原問題、根因、修復點、迴歸風險。

4. 描述完整性（Description Completeness）
- 必須包含：
  - 背景與問題
  - 變更範圍（改了哪些模組）
  - 驗證方式與結果（命令、關鍵輸出）
  - 相容性與破壞性變更說明（如有）
  - 回滾方案（至少一句）
  - 若為 issue 修復：在 PR description 中顯式寫明關閉語句（如 `Fixes #241` / `Closes #241`）

5. 合入判定（Merge Readiness）
- 可直接合入（Ready to Merge）條件：
  - 目標明確且必要
  - 有 Issue 或同等質量的問題描述
  - 變更與描述一致，無隱藏副作用
  - 關鍵驗證已透過（語法/測試/關鍵鏈路）
  - 無阻斷性風險（安全、資料損壞、明顯效能回退）
- 不可直接合入（Not Ready）條件：
  - 描述不完整，無法確認動機和影響
  - 無驗證證據
  - 引入明顯風險且無回滾策略
  - 與倉庫方向無關或重複實現

## 4. 交付與釋出同步原則

- 功能開發、缺陷修復完成後，必須同步更新文件：
  - `README.md`（使用者可見能力、使用方式、配置項變化）
  - `docs/CHANGELOG.md`（版本變更記錄、影響範圍、相容性說明）
- 自動版本標籤預設**不觸發**，需在提交說明中顯式新增對應標籤才會建立 tag：
  - `#patch`：修復類、小改動（+0.0.1）
  - `#minor`：新增可用功能、向後相容（+0.1.0）
  - `#major`：破壞性變更或重大架構調整（+1.0.0）
  - 不新增任何標籤：預設不建立 tag
- 若改動用於解決已有 issue，commit 或 PR description 必須宣告關閉該 issue（`Fixes #xxx` / `Closes #xxx`），避免修復完成後 issue 懸掛。

### Tag 與 Release 規範

**Tag 必須使用 annotated tag（帶 `-m` 註釋），禁止使用輕量 tag。**

```bash
# 正確：annotated tag，-m 內容即 GitHub Release 的正文
git tag -a v3.x.x -m "Bug fixes:
- fix(xxx): 描述 (#issue)

Features:
- feat(xxx): 描述 (#issue)"
git push origin v3.x.x
```

- CI（`docker-publish.yml`）會校驗 tag 是否有非空註釋，輕量 tag 會直接失敗。
- `.github/workflows/create-release.yml` 會在 tag 推送後**自動以註釋內容建立 GitHub Release**，無需手動編輯。

**GitHub Release 的 "What's Changed" 自動生成規則（`.github/release.yml`）：**

- 內容來源：兩個 tag 之間**合併的 PR**，按 PR label 分類。
- 直接 `git commit` 推送的提交**不會出現**在自動生成內容中。
- 因此，團隊規範：
  - 對使用者可見的功能/修復，優先透過 **PR** 合入，並打好 label（`bug` / `enhancement` / `data-source` 等）。
  - 若直接推送了 commit（如緊急修復），需在 tag 的 `-m` 註釋中**手動補充**這些變更，確保 Release Notes 完整。

**`docs/CHANGELOG.md` 維護規則：**

- 新增版本條目時，將 `[Unreleased]` 下的內容移入 `## [X.Y.Z] - YYYY-MM-DD` 並重置 `[Unreleased]` 為空。
- 打 tag 前不強制要求 CHANGELOG 同步（CI 已改為校驗 tag 註釋），但建議保持同步。

## 5. 建議評審輸出格式

### Issue 評審輸出

- `是否合理`：是/否 + 理由
- `是否是 issue`：是/否 + 理由
- `是否好解決`：是/否 + 難點
- `建議動作`：修復/排期/文件/關閉

### PR 評審輸出

- `必要性`：透過/不透過
- `是否有對應 issue`：有/無（編號）
- `PR 型別`：fix/feat/...
- `description 完整性`：完整/不完整（缺失項）
- `是否可直接合入`：可/不可 + 必改項

## 6. 快速檢查命令（可選）

```bash
./test.sh syntax
python -m py_compile main.py src/*.py data_provider/*.py
flake8 main.py src/ --max-line-length=120
```
