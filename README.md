# Personal Finance Dashboard

這是一個完整且精簡的個人財務儀表板 DEMO 專案，展示了前後端分離的系統架構與功能實作。

## 系統架構

- **前端**：Vue 3 + Vite + Pinia + Axios
- **後端**：Python FastAPI
- **資料庫**：SQLite (SQLAlchemy ORM)

## 功能模組

1. **記帳系統**
   - 支援新增收入與支出（金額、類別、類型、日期、備註）。
   - 提供列表查詢與依類型篩選功能。
2. **股票模組 (點 13: Mock 資料來源)**
   - 內建自選股清單（Watchlist）。
   - 提供股票基本面資料展示。
   - **注意**：本模組目前使用內建 Mock 資料，未串接真實證券 API。
3. **股票篩選引擎 (點 13: Mock 規則與中文提示)**
   - Rule-based 篩選系統，包含三大規則：
     - `net_income > 0` (淨利潤)
     - `free_cash_flow > 0` (自由現金流)
     - `revenue_growth > 0` (營收成長率)
   - 顯示通過與未通過的股票，並提供使用者可理解的中文失敗原因。
4. **AI 摘要模組**
   - 根據記帳資料自動生成財務摘要（具備無資料防呆提示）。
   - 根據股票基本面數據生成 AI 分析解說。
   - （目前使用 Template 實作，已預留 LLM 替換介面）

## 專案結構 (點 13: 修正與實際一致)

```text
personal-finance-dashboard/
├── backend/                  # FastAPI 後端
│   ├── db/                   # 資料庫設定 (database.py)
│   ├── models/               # SQLAlchemy ORM 與 Pydantic Schema (expense.py, stock.py)
│   ├── routers/              # API 路由 (expenses.py, stocks.py, dashboard.py, ai.py)
│   ├── services/             # 業務邏輯 (stock_filter.py, ai_summary.py)
│   ├── main.py               # FastAPI 主程式
│   ├── seed_data.py          # 測試資料填充腳本
│   └── requirements.txt      # 後端套件依賴
└── frontend/                 # Vue3 前端
    ├── src/
    │   ├── api/              # Axios API 封裝 (expenses.js, stocks.js, dashboard.js)
    │   ├── pages/            # 頁面 (Dashboard.vue, Expenses.vue, Stocks.vue)
    │   ├── stores/           # Pinia 狀態管理 (expenseStore.js, stockStore.js, dashboardStore.js)
    │   ├── router/           # Vue Router 設定
    │   ├── App.vue           # 根元件與導覽列
    │   └── main.js           # 前端入口
    ├── index.html
    ├── package.json          # 前端套件依賴
    └── vite.config.js        # Vite 設定 (含 API Proxy)
```

## 本地執行指南

### 1. 啟動後端 (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python seed_data.py  # 建立資料庫與寫入測試資料
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- API 文件：[http://localhost:8000/docs](http://localhost:8000/docs)

### 2. 啟動前端 (Vite)

```bash
cd frontend
npm install
npm run dev
```
- 預設執行於：[http://localhost:5173](http://localhost:5173)

---

> ⚠️ **注意**：本專案為 DEMO 用途。股票資料與篩選結果均為 Mock 數據。
