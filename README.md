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
2. **股票模組**
   - 內建自選股清單（Watchlist）。
   - 提供股票基本面資料展示。
3. **股票篩選引擎**
   - Rule-based 篩選系統，包含三大規則：
     - `net_income > 0`
     - `free_cash_flow > 0`
     - `revenue_growth > 0`
   - 顯示通過與未通過的股票，並列出具體失敗原因。
4. **AI 摘要模組**
   - 根據記帳資料自動生成財務摘要。
   - 根據股票基本面數據生成 AI 分析解說。
   - （目前使用 Template 實作，已預留 LLM 替換介面）

## 專案結構

```text
personal-finance-dashboard/
├── backend/                  # FastAPI 後端
│   ├── db/                   # 資料庫設定 (database.py)
│   ├── models/               # SQLAlchemy ORM 與 Pydantic Schema
│   ├── routers/              # API 路由 (expenses, stocks, dashboard, ai)
│   ├── services/             # 業務邏輯 (stock_filter, ai_summary)
│   ├── main.py               # FastAPI 主程式
│   ├── seed_data.py          # 測試資料填充腳本
│   └── requirements.txt      # 後端套件依賴
└── frontend/                 # Vue3 前端
    ├── src/
    │   ├── api/              # Axios API 封裝
    │   ├── components/       # 共用元件
    │   ├── pages/            # 頁面 (Dashboard, Expenses, Stocks)
    │   ├── stores/           # Pinia 狀態管理
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

> ⚠️ **注意**：本專案為 DEMO 用途，前端若不啟動開發伺服器，也可透過建置靜態檔案後由後端伺服器提供服務，但為求開發便利，目前保留了 Vite proxy 的配置。
