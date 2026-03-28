"""
AI Money Mentor — FastAPI Backend (Enhanced)
- FIRE: month-by-month roadmap, asset allocation, insurance gaps
- Money Health Score: 6 dimensions
- Tax Wizard: missing deductions, ranked suggestions by risk profile
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import google.generativeai as genai
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# =============================================================================
# ⬇️  PASTE YOUR GEMINI API KEY HERE
# =============================================================================
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
GEMINI_MODEL = "gemini-1.5-flash"
# =============================================================================

app = FastAPI(title="AI Money Mentor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCLAIMER = (
    "⚠️ Disclaimer: This output is AI-generated guidance for informational purposes only "
    "and does not constitute licensed financial, tax, or investment advice. "
    "Please consult a qualified financial advisor before making any financial decisions."
)

# ── Tax slab constants ────────────────────────────────────────────────────────
OLD_REGIME_SLABS = [(250_000,0.00),(500_000,0.05),(1_000_000,0.20),(float("inf"),0.30)]
OLD_STD_DED = 50_000
OLD_REBATE_LIMIT = 500_000

NEW_REGIME_SLABS = [(300_000,0.00),(600_000,0.05),(900_000,0.10),
                    (1_200_000,0.15),(1_500_000,0.20),(float("inf"),0.30)]
NEW_STD_DED = 75_000
NEW_REBATE_LIMIT = 700_000
CESS = 0.04
MARGINAL_THRESHOLD = 5_000

# ── FIRE constants ────────────────────────────────────────────────────────────
FIRE_MULTIPLIER = 25
DEFAULT_RETURN = 0.12

# ── Health score weights (6 dimensions) ──────────────────────────────────────
DIM_WEIGHTS = {
    "emergency":      0.20,
    "insurance":      0.15,
    "diversification":0.15,
    "debt":           0.20,
    "tax_efficiency": 0.15,
    "retirement":     0.15,
}
HEALTH_LABELS = [(40,"Poor"),(60,"Fair"),(80,"Good"),(101,"Excellent")]

# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class AnalyseRequest(BaseModel):
    # ── Tax inputs ──
    annual_salary: float = Field(ge=0)
    deductions: float = Field(ge=0, description="Declared 80C+HRA+other deductions")
    # Extra deduction fields for missing-deduction analysis
    has_80c: bool = False
    has_nps: bool = False          # 80CCD(1B) ₹50k extra
    has_hra: bool = False
    has_home_loan: bool = False    # 80EE / 24(b)
    has_health_insurance: bool = False  # 80D
    risk_profile: str = "moderate"  # conservative / moderate / aggressive

    # ── FIRE inputs ──
    age: int = Field(ge=18, le=100)
    monthly_income: float = Field(gt=0)
    monthly_expenses: float = Field(ge=0)
    current_savings: float = Field(ge=0)
    goal_amount: float = Field(ge=0)
    retirement_age: int = Field(default=60, ge=30, le=80)

    # ── Health score extra inputs ──
    monthly_emi: float = Field(ge=0)
    emergency_fund_months: float = Field(ge=0)
    has_term_insurance: bool = False
    has_health_cover: bool = False
    health_cover_lakhs: float = Field(default=0, ge=0)
    num_asset_classes: int = Field(default=1, ge=1, le=6,
        description="How many asset classes invested in: equity, debt, gold, RE, intl, cash")
    annual_tax_saved: float = Field(default=0, ge=0,
        description="Actual tax saved via 80C/NPS/etc this year")
    has_retirement_account: bool = False   # NPS / EPF / PPF


class AnalyseResponse(BaseModel):
    # ── Tax ──
    tax_old: float
    tax_new: float
    tax_recommended: str
    tax_savings_diff: float
    tax_marginal: bool
    missing_deductions: list[dict]
    tax_suggestions: list[dict]

    # ── FIRE ──
    fire_savings_rate: float
    fire_corpus: float
    fire_required_sip: float
    fire_years: float
    fire_on_track: bool
    fire_deficit: bool
    fire_monthly_roadmap: list[dict]   # first 24 months
    fire_yearly_milestones: list[dict]
    fire_asset_allocation: list[dict]
    fire_insurance_gaps: list[str]

    # ── Health ──
    health_score: int
    health_label: str
    health_dimensions: dict
    health_top_factor: str

    # ── AI narrative ──
    summary: str
    recommendations: str
    disclaimer: str
    ai_enhanced: bool


# =============================================================================
# TAX WIZARD
# =============================================================================

def _apply_slabs(income: float, slabs: list) -> float:
    tax, prev = 0.0, 0.0
    for limit, rate in slabs:
        if income <= prev:
            break
        tax += (min(income, limit) - prev) * rate
        prev = limit
    return tax


@dataclass
class TaxResult:
    old_tax: float
    new_tax: float
    diff: float
    recommended: str
    marginal: bool
    old_taxable: float
    new_taxable: float
    missing_deductions: list
    suggestions: list


def _missing_deductions(req: AnalyseRequest) -> list[dict]:
    """Identify deductions the user hasn't declared."""
    gaps = []
    if not req.has_80c:
        gaps.append({"name": "Section 80C", "max_amount": 150_000,
                     "description": "ELSS, PPF, LIC, EPF, NSC — up to ₹1.5L deduction"})
    if not req.has_nps:
        gaps.append({"name": "NPS 80CCD(1B)", "max_amount": 50_000,
                     "description": "Additional ₹50k deduction over 80C limit via NPS Tier-1"})
    if not req.has_health_insurance:
        gaps.append({"name": "Section 80D", "max_amount": 25_000,
                     "description": "Health insurance premium — ₹25k self/family, ₹50k for senior parents"})
    if not req.has_home_loan:
        gaps.append({"name": "Section 24(b)", "max_amount": 200_000,
                     "description": "Home loan interest deduction up to ₹2L (self-occupied)"})
    return gaps


def _tax_suggestions(req: AnalyseRequest, tax: TaxResult) -> list[dict]:
    """Ranked tax-saving investment suggestions by risk profile."""
    profile = req.risk_profile.lower()
    all_options = [
        {"name": "PPF", "risk": "conservative", "liquidity": "low",
         "return_pct": 7.1, "section": "80C",
         "description": "15-year lock-in, sovereign guarantee, tax-free returns"},
        {"name": "ELSS Mutual Fund", "risk": "aggressive", "liquidity": "medium",
         "return_pct": 12.0, "section": "80C",
         "description": "3-year lock-in, equity exposure, historically 10-14% returns"},
        {"name": "NPS Tier-1", "risk": "moderate", "liquidity": "low",
         "return_pct": 9.5, "section": "80CCD(1B)",
         "description": "Extra ₹50k deduction, partial equity, locked till 60"},
        {"name": "NSC", "risk": "conservative", "liquidity": "low",
         "return_pct": 7.7, "section": "80C",
         "description": "5-year post office scheme, guaranteed returns"},
        {"name": "Tax-Saver FD", "risk": "conservative", "liquidity": "low",
         "return_pct": 7.0, "section": "80C",
         "description": "5-year bank FD, DICGC insured"},
        {"name": "Health Insurance (80D)", "risk": "conservative", "liquidity": "high",
         "return_pct": 0, "section": "80D",
         "description": "Premium deduction + health protection — essential for everyone"},
    ]
    rank_order = {"conservative": 0, "moderate": 1, "aggressive": 2}
    profile_rank = rank_order.get(profile, 1)

    def score(opt):
        risk_rank = rank_order.get(opt["risk"], 1)
        return abs(risk_rank - profile_rank) * 10 - opt["return_pct"]

    return sorted(all_options, key=score)[:4]


def calculate_tax(req: AnalyseRequest) -> TaxResult:
    old_taxable = max(0.0, req.annual_salary - OLD_STD_DED - req.deductions)
    old_tax = _apply_slabs(old_taxable, OLD_REGIME_SLABS)
    if old_taxable <= OLD_REBATE_LIMIT:
        old_tax = 0.0
    old_tax *= (1 + CESS)

    new_taxable = max(0.0, req.annual_salary - NEW_STD_DED)
    new_tax = _apply_slabs(new_taxable, NEW_REGIME_SLABS)
    if new_taxable <= NEW_REBATE_LIMIT:
        new_tax = 0.0
    new_tax *= (1 + CESS)

    diff = abs(old_tax - new_tax)
    recommended = "Old" if old_tax < new_tax else "New"
    result = TaxResult(old_tax, new_tax, diff, recommended,
                       diff < MARGINAL_THRESHOLD, old_taxable, new_taxable, [], [])
    result.missing_deductions = _missing_deductions(req)
    result.suggestions = _tax_suggestions(req, result)
    return result


# =============================================================================
# FIRE PATH PLANNER (enhanced)
# =============================================================================

@dataclass
class FireResult:
    savings_rate_pct: float
    fire_corpus: float
    required_sip: float
    years_to_fire: float
    on_track: bool
    deficit: bool
    monthly_roadmap: list   # first 24 months
    yearly_milestones: list
    asset_allocation: list
    insurance_gaps: list


def _asset_allocation(age: int, years_to_fire: float) -> list[dict]:
    """Glide-path allocation: more equity when young/far from FIRE."""
    horizon = min(years_to_fire, 30)
    equity_pct = max(20, min(80, int(100 - age * 0.6 + horizon * 1.2)))
    debt_pct = max(10, 90 - equity_pct - 10)
    gold_pct = 10
    return [
        {"asset": "Equity (Large/Mid-cap MF)", "pct": equity_pct},
        {"asset": "Debt (PPF/Bonds/FD)",        "pct": debt_pct},
        {"asset": "Gold (SGB/Gold ETF)",         "pct": gold_pct},
    ]


def _insurance_gaps(req: AnalyseRequest) -> list[str]:
    gaps = []
    annual_income = req.monthly_income * 12
    if not req.has_term_insurance:
        cover = round(annual_income * 10 / 100_000) * 100_000
        gaps.append(f"No term insurance detected. Recommended cover: ₹{cover:,.0f} "
                    f"(10× annual income). Pure term plans cost ~₹8–15k/year.")
    if not req.has_health_cover:
        gaps.append("No health insurance detected. Minimum ₹10L family floater recommended.")
    elif req.health_cover_lakhs < 10:
        gaps.append(f"Health cover ₹{req.health_cover_lakhs:.0f}L is low. "
                    f"Upgrade to ₹10–25L given rising medical costs.")
    if req.age > 40 and not req.has_retirement_account:
        gaps.append("No NPS/EPF/PPF retirement account detected. "
                    "Start NPS Tier-1 immediately for tax benefit + retirement corpus.")
    return gaps


def calculate_fire(req: AnalyseRequest) -> FireResult:
    monthly_income = req.monthly_income
    monthly_expenses = req.monthly_expenses
    current_savings = req.current_savings
    age = req.age
    annual_return = DEFAULT_RETURN

    savings_rate_pct = max(0.0, min(100.0,
        (monthly_income - monthly_expenses) / monthly_income * 100)) if monthly_income > 0 else 0.0
    deficit = monthly_expenses > monthly_income
    fire_corpus = monthly_expenses * 12 * FIRE_MULTIPLIER
    fv = fire_corpus - current_savings
    r = annual_return / 12

    if fv <= 0:
        alloc = _asset_allocation(age, 0)
        gaps = _insurance_gaps(req)
        return FireResult(savings_rate_pct, fire_corpus, 0.0, 0.0, True, deficit, [], [], alloc, gaps)

    n = 360
    required_sip = fv * r / (((1 + r) ** n - 1) * (1 + r))
    monthly_surplus = monthly_income - monthly_expenses
    sip_used = max(monthly_surplus, required_sip)

    if sip_used <= 0:
        years_to_fire = float("inf")
    else:
        ratio = fv * r / (sip_used * (1 + r)) + 1
        years_to_fire = 0.0 if ratio <= 1 else math.log(ratio) / math.log(1 + r) / 12

    on_track = monthly_surplus >= required_sip

    # Month-by-month roadmap (first 24 months)
    monthly_roadmap = []
    corpus = float(current_savings)
    for m in range(1, 25):
        corpus = corpus * (1 + r) + sip_used
        yr = (age * 12 + m) // 12
        alloc = _asset_allocation(yr, max(0, years_to_fire - m / 12))
        monthly_roadmap.append({
            "month": m,
            "corpus": round(corpus, 0),
            "sip": round(sip_used, 0),
            "equity_pct": alloc[0]["pct"],
        })

    # Yearly milestones
    yearly_milestones = []
    corpus = float(current_savings)
    total_years = math.ceil(years_to_fire) if years_to_fire != float("inf") else 30
    total_years = max(1, min(total_years, 60))
    for yr in range(1, total_years + 1):
        for _ in range(12):
            corpus = corpus * (1 + r) + sip_used
        yearly_milestones.append({"year": yr, "age": age + yr,
                                   "projected_corpus": round(corpus, 0)})

    alloc = _asset_allocation(age, years_to_fire)
    gaps = _insurance_gaps(req)
    return FireResult(savings_rate_pct, fire_corpus, required_sip, years_to_fire,
                      on_track, deficit, monthly_roadmap, yearly_milestones, alloc, gaps)


# =============================================================================
# MONEY HEALTH SCORE (6 dimensions)
# =============================================================================

@dataclass
class HealthResult:
    score: int
    label: str
    dimensions: dict   # name -> sub_score (0-100)
    top_factor: str


def calculate_health_score(req: AnalyseRequest) -> HealthResult:
    monthly_income = req.monthly_income
    monthly_savings = monthly_income - req.monthly_expenses

    # 1. Emergency preparedness (0-100)
    emergency = min(req.emergency_fund_months / 6 * 100, 100)

    # 2. Insurance coverage (0-100)
    ins = 0
    if req.has_term_insurance:
        ins += 50
    if req.has_health_cover:
        cover_score = min(req.health_cover_lakhs / 10 * 50, 50)
        ins += cover_score
    insurance = min(ins, 100)

    # 3. Investment diversification (0-100): 1 class=20, 2=40, 3=60, 4=80, 5+=100
    diversification = min(req.num_asset_classes * 20, 100)

    # 4. Debt health (0-100): DTI-based
    dti_ratio = req.monthly_emi / monthly_income if monthly_income > 0 else 1.0
    debt = max(0, 100 - dti_ratio * 200)

    # 5. Tax efficiency (0-100): based on actual tax saved vs potential
    max_potential_saving = 150_000 * 0.30  # rough max at 30% slab
    tax_eff = min(req.annual_tax_saved / max(max_potential_saving, 1) * 100, 100)

    # 6. Retirement readiness (0-100)
    ret = 0
    if req.has_retirement_account:
        ret += 50
    savings_rate = monthly_savings / monthly_income * 100 if monthly_income > 0 else 0
    ret += min(savings_rate / 20 * 50, 50)  # 20% savings rate = full 50 pts
    retirement = min(ret, 100)

    dims = {
        "emergency":       round(emergency, 1),
        "insurance":       round(insurance, 1),
        "diversification": round(diversification, 1),
        "debt":            round(debt, 1),
        "tax_efficiency":  round(tax_eff, 1),
        "retirement":      round(retirement, 1),
    }

    composite = sum(dims[k] * DIM_WEIGHTS[k] for k in dims)
    score = max(0, min(100, int(round(composite))))

    label = "Poor"
    for threshold, lbl in HEALTH_LABELS:
        if score < threshold:
            label = lbl
            break

    top_factor = min(dims, key=lambda k: dims[k])
    return HealthResult(score, label, dims, top_factor)


# =============================================================================
# GEMINI LLM
# =============================================================================

def _build_prompt(req: AnalyseRequest, tax: TaxResult,
                  fire: FireResult, health: HealthResult) -> str:
    missing = ", ".join(d["name"] for d in tax.missing_deductions) or "None"
    top_suggestions = "; ".join(
        f"{s['name']} ({s['section']}, ~{s['return_pct']}% p.a.)" for s in tax.suggestions[:3]
    )
    gaps = "; ".join(fire.insurance_gaps) or "None"
    alloc = ", ".join(f"{a['asset']} {a['pct']}%" for a in fire.asset_allocation)

    return f"""You are an expert Indian personal finance advisor. Analyse the data below and write:
## Summary  (3-4 sentences covering tax, FIRE, and health score)
## Recommendations  (at least 5 specific, numbered, actionable suggestions)

DATA:
TAX: Old ₹{tax.old_tax:,.0f} | New ₹{tax.new_tax:,.0f} | Recommended: {tax.recommended} | Diff ₹{tax.diff:,.0f}
Missing deductions: {missing}
Top tax-saving options for {req.risk_profile} profile: {top_suggestions}

FIRE: Savings rate {fire.savings_rate_pct:.1f}% | Corpus target ₹{fire.fire_corpus:,.0f}
Required SIP ₹{fire.required_sip:,.0f}/mo | Years to FIRE {fire.years_to_fire:.1f}
On track: {'Yes' if fire.on_track else 'No'} | Deficit: {'Yes' if fire.deficit else 'No'}
Suggested allocation: {alloc}
Insurance gaps: {gaps}

HEALTH SCORE: {health.score}/100 ({health.label})
Dimensions: {health.dimensions}
Weakest area: {health.top_factor}

End with: **Disclaimer: AI-generated guidance, not licensed financial advice.**"""


def call_gemini(prompt: str) -> Optional[str]:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt).text
    except Exception:
        return None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.post("/analyse", response_model=AnalyseResponse)
def analyse(req: AnalyseRequest):
    tax   = calculate_tax(req)
    fire  = calculate_fire(req)
    health = calculate_health_score(req)

    ai_summary = ""
    ai_recs = ""
    ai_enhanced = False

    if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        llm_text = call_gemini(_build_prompt(req, tax, fire, health))
        if llm_text:
            ai_enhanced = True
            # parse summary
            if "## Summary" in llm_text and "## Recommendations" in llm_text:
                s = llm_text.index("## Summary") + len("## Summary")
                e = llm_text.index("## Recommendations")
                ai_summary = llm_text[s:e].strip()
                r_start = e + len("## Recommendations")
                remainder = llm_text[r_start:].strip()
                if "**Disclaimer:" in remainder:
                    remainder = remainder[:remainder.index("**Disclaimer:")].strip()
                ai_recs = remainder

    if not ai_summary:
        regime_note = (
            f"Both regimes differ by only ₹{tax.diff:,.0f} — {tax.recommended} Regime recommended."
            if tax.marginal else
            f"{tax.recommended} Regime saves ₹{tax.diff:,.0f} in tax."
        )
        fire_note = (
            "Already at FIRE corpus." if fire.years_to_fire == 0 else
            "Expenses exceed income — fix deficit first." if fire.deficit else
            f"Need ₹{fire.required_sip:,.0f}/mo SIP to reach FIRE in {fire.years_to_fire:.1f} yrs."
        )
        ai_summary = (
            f"{regime_note} {fire_note} "
            f"Money Health Score: {health.score}/100 ({health.label}). "
            f"Weakest dimension: {health.top_factor.replace('_',' ').title()}."
        )

    if not ai_recs:
        recs = []
        if tax.recommended == "Old" and not tax.marginal:
            recs.append(f"Switch to Old Regime — saves ₹{tax.diff:,.0f}/year.")
        else:
            recs.append(f"Stay on New Regime — saves ₹{tax.diff:,.0f}/year.")
        if tax.missing_deductions:
            names = ", ".join(d["name"] for d in tax.missing_deductions[:2])
            recs.append(f"Claim missing deductions: {names} to reduce taxable income.")
        if tax.suggestions:
            s = tax.suggestions[0]
            recs.append(f"Top tax-saving investment: {s['name']} ({s['section']}) — {s['description']}")
        if fire.deficit:
            recs.append("Reduce monthly expenses to create a positive surplus before investing.")
        elif not fire.on_track:
            recs.append(f"Increase SIP to ₹{fire.required_sip:,.0f}/mo to reach FIRE corpus of ₹{fire.fire_corpus:,.0f}.")
        else:
            recs.append("You're on track for FIRE — step up SIP 10% annually.")
        if fire.insurance_gaps:
            recs.append(fire.insurance_gaps[0])
        if health.top_factor == "emergency":
            recs.append("Build emergency fund to 6 months of expenses.")
        elif health.top_factor == "diversification":
            recs.append("Diversify across equity, debt, and gold to reduce portfolio risk.")
        elif health.top_factor == "retirement":
            recs.append("Open NPS Tier-1 account for retirement savings + ₹50k extra tax deduction.")
        ai_recs = "\n".join(f"{i+1}. {r}" for i, r in enumerate(recs))

    return AnalyseResponse(
        tax_old=round(tax.old_tax, 2),
        tax_new=round(tax.new_tax, 2),
        tax_recommended=tax.recommended,
        tax_savings_diff=round(tax.diff, 2),
        tax_marginal=tax.marginal,
        missing_deductions=tax.missing_deductions,
        tax_suggestions=tax.suggestions,

        fire_savings_rate=round(fire.savings_rate_pct, 2),
        fire_corpus=round(fire.fire_corpus, 0),
        fire_required_sip=round(fire.required_sip, 0),
        fire_years=round(fire.years_to_fire, 1) if fire.years_to_fire != float("inf") else 99.0,
        fire_on_track=fire.on_track,
        fire_deficit=fire.deficit,
        fire_monthly_roadmap=fire.monthly_roadmap,
        fire_yearly_milestones=fire.yearly_milestones,
        fire_asset_allocation=fire.asset_allocation,
        fire_insurance_gaps=fire.insurance_gaps,

        health_score=health.score,
        health_label=health.label,
        health_dimensions=health.dimensions,
        health_top_factor=health.top_factor,

        summary=ai_summary,
        recommendations=ai_recs,
        disclaimer=DISCLAIMER,
        ai_enhanced=ai_enhanced,
    )
