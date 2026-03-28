# =============================================================================
# AI Money Mentor — app.py
# A Streamlit-based personal finance advisor for Indian salaried individuals.
# =============================================================================

# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import streamlit as st


# -----------------------------------------------------------------------------
# EXCEPTIONS
# -----------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when user-supplied input fails validation checks."""
    pass


# -----------------------------------------------------------------------------
# DATACLASSES
# -----------------------------------------------------------------------------

@dataclass
class UserInput:
    """Validated financial inputs collected from the UI form."""
    annual_salary: float          # gross annual salary in INR
    deductions: float             # total 80C + HRA + other deductions
    investments: float            # additional investments (ELSS, PPF, etc.)
    age: int                      # current age in years
    monthly_income: float         # take-home monthly income
    monthly_expenses: float       # total monthly expenses
    current_savings: float        # existing corpus / savings
    goal_amount: float            # target financial goal in INR
    monthly_emi: float            # existing EMI obligations (for health score)
    emergency_fund_months: float  # months of expenses covered by liquid savings


@dataclass
class TaxResult:
    """Output of the Tax Wizard calculation."""
    old_regime_tax: float
    new_regime_tax: float
    savings_difference: float    # abs(old - new); positive = old regime costs more
    recommended_regime: str      # "Old" | "New"
    marginal_difference: bool    # True if |difference| < 5000
    old_taxable_income: float
    new_taxable_income: float


@dataclass
class FireResult:
    """Output of the FIRE Path Planner calculation."""
    savings_rate_pct: float          # monthly savings / monthly income * 100
    fire_corpus: float               # 25 × annual expenses
    required_sip: float              # monthly SIP to reach goal
    years_to_fire: float             # years to accumulate fire_corpus
    on_track: bool                   # True if current monthly surplus >= required_sip
    deficit: bool                    # True if expenses > income
    milestones: list[dict]           # [{year: int, projected_corpus: float}, ...]


@dataclass
class HealthResult:
    """Output of the Money Health Score calculation."""
    score: int                   # 0–100
    label: str                   # "Poor" | "Fair" | "Good" | "Excellent"
    breakdown: dict              # {"savings_rate": x, "dti": y, "emergency": z}
    top_factor: str              # factor with the lowest sub-score


@dataclass
class AdviceResponse:
    """Structured advice produced by the AI Agent."""
    summary: str
    calculations: str
    recommendations: str
    disclaimer: str
    ai_enhanced: bool            # False if LLM call failed; rule-based fallback used


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

DISCLAIMER = (
    "⚠️ Disclaimer: This output is AI-generated guidance for informational purposes only "
    "and does not constitute licensed financial, tax, or investment advice. "
    "Please consult a qualified financial advisor before making any financial decisions."
)

# Old Regime tax slabs (FY 2024-25) — list of (upper_limit, rate)
OLD_REGIME_SLABS = [
    (250_000, 0.00),
    (500_000, 0.05),
    (1_000_000, 0.20),
    (float("inf"), 0.30),
]

OLD_REGIME_STANDARD_DEDUCTION = 50_000
OLD_REGIME_REBATE_LIMIT = 500_000   # 87A rebate if taxable income <= 5L

# New Regime tax slabs (FY 2024-25)
NEW_REGIME_SLABS = [
    (300_000, 0.00),
    (600_000, 0.05),
    (900_000, 0.10),
    (1_200_000, 0.15),
    (1_500_000, 0.20),
    (float("inf"), 0.30),
]

NEW_REGIME_STANDARD_DEDUCTION = 75_000
NEW_REGIME_REBATE_LIMIT = 700_000   # 87A rebate if taxable income <= 7L

CESS_RATE = 0.04                    # Health & Education cess

MARGINAL_DIFFERENCE_THRESHOLD = 5_000  # INR

# FIRE constants
FIRE_MULTIPLIER = 25                # FIRE corpus = 25 × annual expenses
DEFAULT_ANNUAL_RETURN = 0.12

# Health score weights
SAVINGS_WEIGHT = 0.40
DTI_WEIGHT = 0.30
EMERGENCY_WEIGHT = 0.30

HEALTH_LABELS = [
    (40, "Poor"),
    (60, "Fair"),
    (80, "Good"),
    (101, "Excellent"),
]

LLM_MODELS = {
    "OpenAI": "gpt-4o-mini",
    "Google Gemini": "gemini-1.5-flash",
    "Anthropic Claude": "claude-3-haiku-20240307",
}


# -----------------------------------------------------------------------------
# PURE CALCULATION FUNCTIONS
# -----------------------------------------------------------------------------

def _apply_slabs(taxable_income: float, slabs: list) -> float:
    """Compute tax by applying progressive slab rates to taxable_income."""
    tax = 0.0
    prev_limit = 0.0
    for upper_limit, rate in slabs:
        if taxable_income <= prev_limit:
            break
        slab_income = min(taxable_income, upper_limit) - prev_limit
        tax += slab_income * rate
        prev_limit = upper_limit
    return tax


def calculate_tax(salary: float, deductions: float) -> TaxResult:
    """Calculate income tax under Old and New regimes (FY 2024-25)."""
    # --- Old Regime ---
    old_taxable = max(0.0, salary - OLD_REGIME_STANDARD_DEDUCTION - deductions)
    old_tax = _apply_slabs(old_taxable, OLD_REGIME_SLABS)
    # 87A rebate: zero out tax if taxable income <= 5L
    if old_taxable <= OLD_REGIME_REBATE_LIMIT:
        old_tax = 0.0
    old_tax_with_cess = old_tax * (1 + CESS_RATE)

    # --- New Regime ---
    new_taxable = max(0.0, salary - NEW_REGIME_STANDARD_DEDUCTION)
    new_tax = _apply_slabs(new_taxable, NEW_REGIME_SLABS)
    # 87A rebate: zero out tax if taxable income <= 7L
    if new_taxable <= NEW_REGIME_REBATE_LIMIT:
        new_tax = 0.0
    new_tax_with_cess = new_tax * (1 + CESS_RATE)

    # --- Comparison ---
    diff = abs(old_tax_with_cess - new_tax_with_cess)
    # Recommend the regime with lower tax; default to New if equal
    if old_tax_with_cess < new_tax_with_cess:
        recommended = "Old"
    else:
        recommended = "New"

    return TaxResult(
        old_regime_tax=old_tax_with_cess,
        new_regime_tax=new_tax_with_cess,
        savings_difference=diff,
        recommended_regime=recommended,
        marginal_difference=diff < MARGINAL_DIFFERENCE_THRESHOLD,
        old_taxable_income=old_taxable,
        new_taxable_income=new_taxable,
    )


def calculate_fire(
    age: int,
    monthly_income: float,
    monthly_expenses: float,
    current_savings: float,
    goal_amount: float,
    annual_return: float = DEFAULT_ANNUAL_RETURN,
) -> FireResult:
    """Calculate FIRE path metrics."""
    # Savings rate: clamped to [0, 100]
    if monthly_income > 0:
        raw_rate = (monthly_income - monthly_expenses) / monthly_income * 100
        savings_rate_pct = max(0.0, min(100.0, raw_rate))
    else:
        savings_rate_pct = 0.0

    # Deficit flag
    deficit = monthly_expenses > monthly_income

    # FIRE corpus: 25 × annual expenses
    fire_corpus = monthly_expenses * 12 * FIRE_MULTIPLIER

    # Remaining amount needed
    fv = fire_corpus - current_savings

    r = annual_return / 12  # monthly rate

    if fv <= 0:
        # Already at or past FIRE corpus
        required_sip = 0.0
        years_to_fire = 0.0
        on_track = True
        milestones = []
    else:
        # Use a default horizon of 30 years (360 months) to solve for SIP
        n = 360
        # P = FV * r / (((1+r)^n - 1) * (1+r))
        required_sip = fv * r / (((1 + r) ** n - 1) * (1 + r))

        # Compute years_to_fire: find n such that SIP grows to fv
        # FV = P * (((1+r)^n - 1) / r) * (1+r)
        # Solve: (1+r)^n = fv * r / (P * (1+r)) + 1
        monthly_surplus = monthly_income - monthly_expenses
        sip_used = max(monthly_surplus, required_sip)  # use actual surplus if larger

        if sip_used <= 0:
            years_to_fire = float("inf")
        else:
            # (1+r)^n = fv*r/(sip_used*(1+r)) + 1
            ratio = fv * r / (sip_used * (1 + r)) + 1
            if ratio <= 1:
                years_to_fire = 0.0
            else:
                n_months = math.log(ratio) / math.log(1 + r)
                years_to_fire = n_months / 12

        on_track = (monthly_income - monthly_expenses) >= required_sip

        # Generate yearly milestones
        milestones = []
        corpus = float(current_savings)
        total_years = math.ceil(years_to_fire) if years_to_fire != float("inf") else 30
        total_years = max(1, min(total_years, 100))
        for yr in range(1, total_years + 1):
            for _ in range(12):
                corpus = corpus * (1 + r) + sip_used
            milestones.append({"year": yr, "projected_corpus": round(corpus, 2)})

    return FireResult(
        savings_rate_pct=savings_rate_pct,
        fire_corpus=fire_corpus,
        required_sip=required_sip,
        years_to_fire=years_to_fire,
        on_track=on_track,
        deficit=deficit,
        milestones=milestones,
    )


def calculate_health_score(
    monthly_income: float,
    monthly_savings: float,
    monthly_emi: float,
    emergency_fund_months: float,
) -> HealthResult:
    """Compute the Money Health Score (0–100)."""
    # Savings rate sub-score
    savings_rate_pct = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0.0
    savings_sub = min(savings_rate_pct / 30 * 100, 100)

    # Debt-to-income sub-score
    dti_sub = max(100 - (monthly_emi / monthly_income * 200), 0) if monthly_income > 0 else 0.0

    # Emergency fund sub-score
    emergency_sub = min(emergency_fund_months / 6 * 100, 100)

    # Composite score
    composite = savings_sub * SAVINGS_WEIGHT + dti_sub * DTI_WEIGHT + emergency_sub * EMERGENCY_WEIGHT
    score = int(round(composite))
    score = max(0, min(100, score))

    # Label
    for threshold, label in HEALTH_LABELS:
        if score < threshold:
            break

    # Top factor: factor with the lowest sub-score
    sub_scores = {"savings_rate": savings_sub, "dti": dti_sub, "emergency": emergency_sub}
    top_factor = min(sub_scores, key=lambda k: sub_scores[k])

    return HealthResult(
        score=score,
        label=label,
        breakdown=sub_scores,
        top_factor=top_factor,
    )


def validate_inputs(user_input: UserInput) -> None:
    """Validate a UserInput instance; raises ValidationError on failure."""
    # Reject zero monthly income
    if user_input.monthly_income == 0:
        raise ValidationError("monthly_income must be greater than zero.")

    # Numeric fields that must be non-negative
    non_negative_fields = [
        ("annual_salary", user_input.annual_salary),
        ("deductions", user_input.deductions),
        ("investments", user_input.investments),
        ("monthly_income", user_input.monthly_income),
        ("monthly_expenses", user_input.monthly_expenses),
        ("current_savings", user_input.current_savings),
        ("goal_amount", user_input.goal_amount),
        ("monthly_emi", user_input.monthly_emi),
        ("emergency_fund_months", user_input.emergency_fund_months),
    ]
    for field_name, value in non_negative_fields:
        if value < 0:
            raise ValidationError(f"{field_name} must be non-negative, got {value}.")


# -----------------------------------------------------------------------------
# AI AGENT FUNCTIONS
# -----------------------------------------------------------------------------

def build_prompt(
    tax: TaxResult,
    fire: FireResult,
    health: Optional[HealthResult],
) -> str:
    """Build a structured LLM prompt from calculation results."""
    lines = [
        "You are an expert Indian personal finance advisor. Using the calculation results below, "
        "produce a response with exactly three sections labelled '## Summary', '## Calculations', "
        "and '## Recommendations'. In the Recommendations section provide at least two specific, "
        "actionable suggestions (e.g. 'Increase 80C investments by ₹X to reduce tax'). "
        "End the response with the following disclaimer verbatim:\n"
        "**Disclaimer: This is AI-generated guidance and not licensed financial advice. "
        "Please consult a qualified financial advisor before making investment decisions.**\n",

        "--- TAX WIZARD RESULTS ---",
        f"Old Regime Tax:        ₹{tax.old_regime_tax:,.2f}",
        f"New Regime Tax:        ₹{tax.new_regime_tax:,.2f}",
        f"Recommended Regime:    {tax.recommended_regime}",
        f"Tax Savings Difference:₹{tax.savings_difference:,.2f}",
        f"Marginal Difference:   {'Yes — either regime is acceptable' if tax.marginal_difference else 'No'}",
        f"Old Taxable Income:    ₹{tax.old_taxable_income:,.2f}",
        f"New Taxable Income:    ₹{tax.new_taxable_income:,.2f}",

        "\n--- FIRE PATH PLANNER RESULTS ---",
        f"Monthly Savings Rate:  {fire.savings_rate_pct:.2f}%",
        f"FIRE Corpus Target:    ₹{fire.fire_corpus:,.2f}",
        f"Required Monthly SIP:  ₹{fire.required_sip:,.2f}",
        f"Years to FIRE:         {fire.years_to_fire:.1f}",
        f"On Track:              {'Yes' if fire.on_track else 'No'}",
        f"Deficit (expenses > income): {'Yes' if fire.deficit else 'No'}",
    ]

    if health is not None:
        lines += [
            "\n--- MONEY HEALTH SCORE ---",
            f"Score:      {health.score}/100 ({health.label})",
            f"Breakdown:  savings_rate={health.breakdown.get('savings_rate', 0):.1f}, "
            f"dti={health.breakdown.get('dti', 0):.1f}, "
            f"emergency={health.breakdown.get('emergency', 0):.1f}",
            f"Top Factor Needing Improvement: {health.top_factor}",
        ]

    lines.append(
        "\nNow write the ## Summary, ## Calculations, and ## Recommendations sections "
        "followed by the disclaimer."
    )

    return "\n".join(lines)


def call_llm(prompt: str, api_key: str, model: str) -> Optional[str]:
    """Call the selected LLM API; returns None on failure."""
    try:
        if model.startswith("gpt-"):
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        elif model.startswith("gemini-"):
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            response = genai.GenerativeModel(model).generate_content(prompt)
            return response.text

        elif model.startswith("claude-"):
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        return None
    except Exception:
        return None


def build_rule_based_response(
    tax: TaxResult,
    fire: FireResult,
    health: Optional[HealthResult],
) -> AdviceResponse:
    """Generate a rule-based AdviceResponse when LLM is unavailable."""
    # --- Summary ---
    regime_note = (
        f"Both regimes are nearly equivalent (difference ₹{tax.savings_difference:,.0f}), "
        f"but the {tax.recommended_regime} Regime is recommended."
        if tax.marginal_difference
        else f"The {tax.recommended_regime} Regime is recommended, saving you ₹{tax.savings_difference:,.0f} in tax."
    )
    fire_note = (
        "You are currently on track to reach your FIRE goal."
        if fire.on_track
        else (
            "Your monthly expenses exceed your income — address the deficit before investing."
            if fire.deficit
            else f"You need to increase your monthly SIP to ₹{fire.required_sip:,.0f} to reach FIRE in {fire.years_to_fire:.1f} years."
        )
    )
    health_note = (
        f" Your Money Health Score is {health.score}/100 ({health.label})."
        if health is not None
        else ""
    )
    summary = (
        f"{regime_note} "
        f"Your FIRE corpus target is ₹{fire.fire_corpus:,.0f} and your current savings rate is {fire.savings_rate_pct:.1f}%. "
        f"{fire_note}{health_note}"
    )

    # --- Calculations ---
    calc_lines = [
        "Tax Wizard:",
        f"  Old Regime Tax:         ₹{tax.old_regime_tax:,.2f}  (taxable income ₹{tax.old_taxable_income:,.0f})",
        f"  New Regime Tax:         ₹{tax.new_regime_tax:,.2f}  (taxable income ₹{tax.new_taxable_income:,.0f})",
        f"  Tax Savings Difference: ₹{tax.savings_difference:,.2f}",
        f"  Recommended Regime:     {tax.recommended_regime}"
        + (" (marginal — either regime is acceptable)" if tax.marginal_difference else ""),
        "",
        "FIRE Path Planner:",
        f"  Monthly Savings Rate:   {fire.savings_rate_pct:.2f}%",
        f"  FIRE Corpus Target:     ₹{fire.fire_corpus:,.2f}",
        f"  Required Monthly SIP:   ₹{fire.required_sip:,.2f}",
        f"  Years to FIRE:          {fire.years_to_fire:.1f}",
        f"  On Track:               {'Yes' if fire.on_track else 'No'}",
        f"  Deficit:                {'Yes' if fire.deficit else 'No'}",
    ]
    if health is not None:
        calc_lines += [
            "",
            "Money Health Score:",
            f"  Score:                  {health.score}/100 ({health.label})",
            f"  Savings Rate Sub-score: {health.breakdown.get('savings_rate', 0):.1f}",
            f"  DTI Sub-score:          {health.breakdown.get('dti', 0):.1f}",
            f"  Emergency Fund Sub-score: {health.breakdown.get('emergency', 0):.1f}",
            f"  Top Factor to Improve:  {health.top_factor}",
        ]
    calculations = "\n".join(calc_lines)

    # --- Recommendations ---
    recs = []

    # Tax-based recommendations
    if tax.recommended_regime == "Old" and not tax.marginal_difference:
        recs.append(
            f"Maximise your Section 80C investments (up to ₹1,50,000) to reduce your Old Regime "
            f"taxable income and save up to ₹{tax.savings_difference:,.0f} compared to the New Regime."
        )
    elif tax.recommended_regime == "New" and not tax.marginal_difference:
        recs.append(
            f"Switch to the New Regime to save ₹{tax.savings_difference:,.0f} in tax — "
            "it offers lower slab rates without requiring you to track deductions."
        )
    else:
        recs.append(
            "Both regimes produce a similar tax outcome. Review your deduction eligibility "
            "each year and choose the regime that gives you the lower liability."
        )

    # FIRE / savings-based recommendations
    if fire.deficit:
        recs.append(
            "Your monthly expenses exceed your income. Focus on reducing discretionary spending "
            "to create a positive monthly surplus before starting any SIP investments."
        )
    elif not fire.on_track:
        shortfall = fire.required_sip - (
            fire.required_sip  # placeholder; actual surplus not passed in
        )
        recs.append(
            f"Increase your monthly SIP to at least ₹{fire.required_sip:,.0f} to reach your "
            f"FIRE corpus of ₹{fire.fire_corpus:,.0f} in approximately {fire.years_to_fire:.1f} years."
        )
    else:
        recs.append(
            f"You are on track for FIRE. Consider stepping up your SIP by 10% annually "
            f"to reach your corpus of ₹{fire.fire_corpus:,.0f} even sooner."
        )

    # Health-score-based recommendation (if available)
    if health is not None and health.top_factor == "emergency":
        recs.append(
            "Build your emergency fund to cover at least 6 months of expenses "
            "before increasing equity investments."
        )
    elif health is not None and health.top_factor == "dti":
        recs.append(
            "Your debt-to-income ratio is high. Prioritise prepaying high-interest loans "
            "to free up cash flow for investments."
        )

    recommendations = "\n".join(f"• {r}" for r in recs)

    return AdviceResponse(
        summary=summary,
        calculations=calculations,
        recommendations=recommendations,
        disclaimer=DISCLAIMER,
        ai_enhanced=False,
    )


def orchestrate(user_input: UserInput, api_key: str, model: str) -> AdviceResponse:
    """Orchestrate all modules and return a complete AdviceResponse."""
    # 1. Always run Tax Wizard and FIRE Planner
    tax = calculate_tax(user_input.annual_salary, user_input.deductions)
    fire = calculate_fire(
        user_input.age,
        user_input.monthly_income,
        user_input.monthly_expenses,
        user_input.current_savings,
        user_input.goal_amount,
    )

    # 2. Always run Money Health Score (all fields are available)
    monthly_savings = user_input.monthly_income - user_input.monthly_expenses
    health = calculate_health_score(
        user_input.monthly_income,
        monthly_savings,
        user_input.monthly_emi,
        user_input.emergency_fund_months,
    )

    # 3. Build prompt
    prompt = build_prompt(tax, fire, health)

    # 4. Try LLM; fall back to rule-based if api_key is empty or call fails
    llm_response: Optional[str] = None
    if api_key:
        llm_response = call_llm(prompt, api_key, model)

    if llm_response is None:
        return build_rule_based_response(tax, fire, health)

    # 5. Parse LLM response into sections
    try:
        text = llm_response

        # Extract Summary: between "## Summary" and "## Calculations"
        summary = ""
        if "## Summary" in text and "## Calculations" in text:
            start = text.index("## Summary") + len("## Summary")
            end = text.index("## Calculations")
            summary = text[start:end].strip()

        # Extract Calculations: between "## Calculations" and "## Recommendations"
        calculations = ""
        if "## Calculations" in text and "## Recommendations" in text:
            start = text.index("## Calculations") + len("## Calculations")
            end = text.index("## Recommendations")
            calculations = text[start:end].strip()

        # Extract Recommendations: after "## Recommendations" (up to disclaimer)
        recommendations = ""
        if "## Recommendations" in text:
            start = text.index("## Recommendations") + len("## Recommendations")
            remainder = text[start:].strip()
            # Strip trailing disclaimer if present
            disclaimer_marker = "**Disclaimer:"
            if disclaimer_marker in remainder:
                remainder = remainder[: remainder.index(disclaimer_marker)].strip()
            recommendations = remainder

        # Require all three sections to be non-empty
        if not summary or not calculations or not recommendations:
            return build_rule_based_response(tax, fire, health)

        return AdviceResponse(
            summary=summary,
            calculations=calculations,
            recommendations=recommendations,
            disclaimer=DISCLAIMER,
            ai_enhanced=True,
        )
    except Exception:
        return build_rule_based_response(tax, fire, health)


# -----------------------------------------------------------------------------
# STREAMLIT UI FUNCTIONS
# -----------------------------------------------------------------------------

def render_input_form() -> Optional[UserInput]:
    """Render the financial input form and return validated UserInput."""
    with st.form("input_form"):
        st.subheader("Tax Details")
        annual_salary = st.number_input("Annual Salary (₹)", min_value=0.0, value=0.0, step=1000.0)
        deductions = st.number_input("Total Deductions - 80C, HRA, etc. (₹)", min_value=0.0, value=0.0, step=1000.0)
        investments = st.number_input("Additional Investments (₹)", min_value=0.0, value=0.0, step=1000.0)

        st.subheader("Personal & Income Details")
        age = st.number_input("Current Age", min_value=18, max_value=100, value=30, step=1)
        monthly_income = st.number_input("Monthly Take-Home Income (₹)", min_value=1.0, value=1.0, step=1000.0)
        monthly_expenses = st.number_input("Monthly Expenses (₹)", min_value=0.0, value=0.0, step=500.0)
        current_savings = st.number_input("Current Savings / Corpus (₹)", min_value=0.0, value=0.0, step=10000.0)
        goal_amount = st.number_input("Financial Goal Amount (₹)", min_value=0.0, value=0.0, step=10000.0)

        st.subheader("Debt & Emergency Fund")
        monthly_emi = st.number_input("Monthly EMI Obligations (₹)", min_value=0.0, value=0.0, step=500.0)
        emergency_fund_months = st.number_input("Emergency Fund Coverage (months)", min_value=0.0, value=0.0, step=0.5)

        submitted = st.form_submit_button("Generate Financial Plan")

    if submitted:
        user_input = UserInput(
            annual_salary=annual_salary,
            deductions=deductions,
            investments=investments,
            age=int(age),
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            current_savings=current_savings,
            goal_amount=goal_amount,
            monthly_emi=monthly_emi,
            emergency_fund_months=emergency_fund_months,
        )
        try:
            validate_inputs(user_input)
        except ValidationError as e:
            st.error(str(e))
            return None

        with st.spinner("Analysing your finances…"):
            return user_input

    return None


def render_results(advice: AdviceResponse) -> None:
    """Render the AdviceResponse in three expander sections."""
    if not advice.ai_enhanced:
        st.warning("AI-enhanced advice is unavailable. Showing rule-based analysis.")

    with st.expander("📊 Summary", expanded=True):
        st.markdown(advice.summary)

    with st.expander("🔢 Calculations"):
        st.code(advice.calculations)

    with st.expander("💡 Recommendations"):
        st.markdown(advice.recommendations)

    st.info(advice.disclaimer)


# -----------------------------------------------------------------------------
# MAIN ENTRY POINT
# -----------------------------------------------------------------------------

def main() -> None:
    """Main Streamlit app entry point."""
    st.set_page_config(page_title="AI Money Mentor", page_icon="💰", layout="wide")
    st.title("💰 AI Money Mentor")
    st.caption("Personalised financial guidance for Indian salaried individuals")

    with st.sidebar:
        st.header("AI Settings")
        provider = st.selectbox("LLM Provider", list(LLM_MODELS.keys()))
        api_key = st.text_input("API Key", type="password", placeholder="Enter your API key")
        model = LLM_MODELS[provider]

    user_input = render_input_form()
    if user_input is not None:
        advice = orchestrate(user_input, api_key, model)
        st.session_state["advice"] = advice

    if "advice" in st.session_state:
        render_results(st.session_state["advice"])


main()
