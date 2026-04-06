# Personal Finance Dashboard (v0.6.1)

這是一個完整且精簡的個人財務管理系統 DEMO 專案，結合了記帳系統、預算管理、真實股票行情同步、股票篩選引擎以及 AI 財務建議模組。

## 🚀 版本更新：v0.6.1 (API Path Fixes, Stock Autofill & Code Cleanup)
- **API 路徑修正**：修正前端 API 模組與頁面中的冗餘 `/api` 前綴，確保路徑一致性。
- **股票名稱自動填寫**：後端股票服務新增自動填寫股票名稱功能，提升使用者體驗。
- **冗餘代碼移除**：移除後端 `stock_data_service.py` 中不再使用的 `get_mock_price` 函數。
- **代碼清理與註釋優化**：清理前後端所有檔案中的開發註釋，使代碼更簡潔。
- **用戶數據隔離驗證**：確保所有 API 接口都已正確實施用戶數據隔離。

## 🚀 版本更新：v0.6.0 (Budget System & AI Advice)
- **預算管理系統**：新增每月預算限額設定，自動追蹤各類別支出使用率與超支警示。
- **AI 財務建議**：根據收支與預算執行進度，由 AI (Template-based) 產生個人化理財與預算建議。
- **Dashboard 強化**：儀表板新增預算分析建議區塊。
- **穩定性修正 (v0.5.2)**：修正股票同步訊息、清理開發註解、優化 Loading 狀態管理。

## 📂 專案結構
```text
personal-finance-dashboard/
├── backend/                # FastAPI 後端
│   ├── db/                 # 資料庫連線與初始化
│   ├── models/             # SQLAlchemy ORM 與 Pydantic 模型 (User, Expense, Stock, Budget)
│   ├── routers/            # API 路由 (Auth, Expenses, Stocks, Budgets, Dashboard, AI)
│   ├── services/           # 業務邏輯 (Auth, StockData, StockFilter, AISummary)
│   ├── main.py             # 程式入口
│   └── seed_data.py        # 測試資料填充腳本
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # Axios API 呼叫封裝 (Auth, Expenses, Stocks, Budgets)
│   │   ├── stores/         # Pinia 狀態管理 (Auth, Expense, Stock, Dashboard)
│   │   ├── pages/          # 頁面元件 (Login, Register, Dashboard, Expenses, Stocks, Budgets)
│   │   └── constants/      # 全域常數 (版本號等)
│   └── vite.config.js      # Vite 配置 (含 API Proxy)
└── README.md
```

## 🛠️ 快速啟動

### 1. 後端啟動
```bash
cd backend
# 安裝依賴 (建議使用虛擬環境)
pip install -r requirements.txt
# 初始化資料庫與測試資料
python seed_data.py
# 啟動伺服器
uvicorn main:app --reload
```

### 2. 前端啟動
```bash
cd frontend
# 安裝依賴
pnpm install
# 啟動開發伺服器
pnpm dev
```

## 🔐 測試帳號
- **Email**: `demo@example.com`
- **Password**: `demo1234`

## 📈 股票資料說明 (Stock Data)
- **真實資料**：目前「最新價格」、「成交量」與「最後更新日期」均透過 `yfinance` 抓取真實市場行情。
- **台股支援**：輸入 4 位數台股代碼（如 `2330`）系統會自動補全為 `2330.TW` 進行抓取。
- **同步機制**：使用者可手動點擊「同步最新價格」觸發更新，抓取失敗時會回傳錯誤提示。
- **Mock 流程**：股票篩選引擎的基本面數據與 AI 股票解說目前仍為 Demo/Mock 流程。

## 📝 版本更新日誌 (Release Notes)
- **v0.6.1**：修正 API 路徑、自動填寫股票名稱、移除冗餘代碼、清理註釋及確保用戶隔離。
- **v0.6.0**：正式導入預算管理系統與 AI 預算建議功能。
- **v0.5.2**：穩定性修正。優化股票同步訊息、清理開發註解、優化 Loading 狀態管理。
- **v0.5.1**：優化 API 回傳處理、台股代碼辨識、移除 alert 改用頁面提示。
- **v0.5.0**：正式導入真實股票資料流程 (yfinance) 與 Watchlist 完整 CRUD。
- **v0.4.1**：認證流程穩定性優化與 API 結構重整。
- **v0.4.0**：引入 JWT 認證系統與使用者資料隔離。

## ⚠️ 限制與說明
- 本專案為 DEMO 用途，不建議直接用於生產環境。
- AI 摘要與建議目前使用預設 Template 生成，可於 `backend/services/ai_summary.py` 中替換為真實 LLM API。
- 股票資料抓取受限於 yfinance 的穩定性與網路環境。
- 預算統計以「自然月」為單位進行計算。
