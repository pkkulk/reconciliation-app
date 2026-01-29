# 📊 ReconcilePro - Financial Reconciliation App

**ReconcilePro** is a full-stack web application designed to automate the reconciliation of financial transactions between a **Partner Statement** and a **Settlement Report**. It identifies matches, variances, and missing entries with high precision, replacing manual Excel processes.

## 🚀 Key Features
- **Automated Matching**: Matches thousands of transactions in seconds using fuzzy logic and exact ID matching beneath the surface.
- **Smart Parsing**: Handles different Excel formats, messy descriptions, and rigorous data cleaning (removing junk rows, normalizing IDs).
- **Variance Analysis**: Calculates `Estimated USD` from foreign currencies and flags discrepancies against settled amounts.
- **Interactive Dashboard**: A modern React-based UI to visualize results (Matched, Variance, Statement Only, Settlement Only).

---

## 🛠️ Tech Stack

### **Backend** (Python / FastAPI)
- **FastAPI**: High-performance API framework.
- **Pandas**: Powerhouse for data manipulation (Excel processing, merging, filtering).
- **Uvicorn**: ASGI server for production.

### **Frontend** (React / Vite)
- **React 19**: Modern component-based UI.
- **Tailwind CSS v4**: Utility-first styling for a premium, responsive design.
- **Framer Motion**: Smooth animations for better UX.
- **Axios**: HTTP client for API communication.

---

## 📂 Project Structure & Workflow

### **1. Backend (`/backend`)**
This is the brain of the operation.
- **`main.py`**: The API Gateway.
    - Exposes the `POST /reconcile` endpoint.
    - Handles file uploads (`multipart/form-data`) and CORS.
- **`services.py`**: The Core Logic Engine.
    - **`process_statement()`**: Reads Statement file, skips header junk (rows 1-9), cleans data, extracts IDs.
    - **`process_settlement()`**: Reads Settlement file, skips header junk (rows 1-2), normalizes IDs (removes `777` prefix).
    - **`reconcile_files()`**: The main algorithm. Performs an **Outer Join** on normalized `PartnerPin` to categorize every transaction.
- **`utils.py`**: Helper functions.
    - **`extract_partner_pin()`**: Smart regex to find the 8-12 digit Transaction ID from the end of messy description strings (handles `XXP` prefixes).

### **2. Frontend (`/frontend`)**
This is the user interface.
- **`src/components/UploadForm.jsx`**:
    - smart validation (ensures both files are selected).
    - Drag-and-drop support.
    - Sends files to `VITE_API_URL` (production) or localhost (dev).
- **`src/components/ResultsTable.jsx`**:
    - Displays data in paginated, searchable tables.
    - Different tabs for *Matched*, *Variance*, *Missing in Statement*, etc.
- **`src/components/SummaryCards.jsx`**:
    - Animated widgets showing high-level stats (e.g., "65 Matched").

---

## 📝 Reconciliation Logic / Workflow
The app follows a strict, verifiable set of rules:

1.  **Data Ingestion**:
    - **Statement File**: Rows 1-9 are deleted. `PartnerPin` is extracted from descriptions (e.g., `... XXP18356664 ...` -> `18356664`).
    - **Settlement File**: Rows 1-2 are deleted. `PartnerPin` is normalized (e.g., `77718356664` -> `18356664`).
2.  **Tagging**:
    - Duplicate entries in Statement are tagged: "Cancel" types are kept, "Dollar Received" types are ignored.
3.  **Matching**:
    - Records are matched on **PartnerPin**.
    - **Exact Match**: ID exists in both files.
    - **Variance**: ID matches, but `EstimatedUSD` (calculated from Rate & Payout) differs from `SettleAmt` by > $0.01.
    - **Statement Only**: ID exists in Statement but not Settlement.
    - **Settlement Only**: ID exists in Settlement but not Statement.

---

## ⚡ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Run Backend
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload
# Running on http://localhost:8000
```

### 2. Run Frontend
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173
```

## 🌍 Deployment
The app is configured for cloud deployment:
- **Backend (Render)**: Uses `Procfile` (`web: uvicorn backend.main:app ...`).
- **Frontend (Vercel)**: Uses `vercel.json` for routing.
- **CD**: Set up via GitHub integration.

---

## 🧪 Verification
To verify the logic against real data:
1.  Place `Statement.xlsx` and `Settlement.xlsx` in the root.
2.  Run the verification module:
    ```bash
    python -m backend.reproduce_reconciliation
    ```
