# 💰 AI Money Mentor

Personalised financial guidance for Indian salaried individuals — powered by Google Gemini AI.

## Features

- **Tax Wizard** — Compares Old vs New regime (FY 2024-25), identifies missing deductions (80C, NPS, 80D, home loan), and ranks tax-saving investments by your risk profile
- **FIRE Path Planner** — Month-by-month financial roadmap, SIP targets, glide-path asset allocation, and insurance gap detection
- **Money Health Score** — Comprehensive wellness score across 6 dimensions: emergency preparedness, insurance coverage, investment diversification, debt health, tax efficiency, and retirement readiness

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | FastAPI (Python) |
| AI | Google Gemini 1.5 Flash |
| Styling | Plain CSS |

## Project Structure

```
├── backend/
│   ├── main.py          # FastAPI app — all calculation + AI logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── InputForm.tsx
│   │   │   └── Results.tsx
│   │   ├── types.ts
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── app.py               # Original Streamlit prototype
└── test_app.py          # Property-based + unit tests (pytest + hypothesis)
```

## Getting Started

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

Open `backend/main.py` and paste your Gemini API key on line 16:

```python
GEMINI_API_KEY = "your-key-here"
```

Then start the server:

```bash
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`. The Vite dev server proxies `/analyse` to the backend automatically.

### 3. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a free API key
3. Paste it in `backend/main.py`

Without a key the app still works — it falls back to rule-based analysis.

## Running Tests

```bash
pip install pytest hypothesis
pytest test_app.py -v
```

76 tests covering all calculation logic with property-based testing via Hypothesis.

## Tax Calculation Details

**Old Regime (FY 2024-25)**
- Standard deduction: ₹50,000
- 87A rebate: full rebate if taxable income ≤ ₹5L
- Slabs: 0% / 5% / 20% / 30%
- 4% health & education cess

**New Regime (FY 2024-25)**
- Standard deduction: ₹75,000
- 87A rebate: full rebate if taxable income ≤ ₹7L
- Slabs: 0% / 5% / 10% / 15% / 20% / 30%
- 4% health & education cess

## Disclaimer

This tool provides AI-generated guidance for informational purposes only. It does not constitute licensed financial, tax, or investment advice. Please consult a qualified financial advisor before making any financial decisions.
