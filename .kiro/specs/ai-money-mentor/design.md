# Design Document: AI Money Mentor

## Overview

AI Money Mentor is a single-file Streamlit application written in Python. The user fills in one form; an AI Agent orchestrates two calculation modules (Tax Wizard and FIRE Path Planner), optionally computes a Money Health Score, and then calls an LLM (OpenAI / Gemini / Claude) to wrap the raw numbers into human-readable, actionable advice. All state lives in Streamlit session variables — no database is required.

The application targets Indian salaried individuals and follows Indian income-tax rules (FY 2024-25 slabs).

---

## Architecture

```mermaid
flowchart TD
    User([User]) -->|fills form| UI[Streamlit UI\napp.py]
    UI -->|validated inputs| Agent[AI Agent\norchestrate()]
    Agent -->|salary, deductions| TW[Tax Wizard\ncalculate_tax()]
    Agent -->|age, income, expenses, savings, goal| FP[FIRE Planner\ncalculate_fire()]
    Agent -->|income, savings, expenses| MH[Money Health Score\ncalculate_health_score()]
    TW -->|TaxResult| Agent
    FP -->|FireResult| Agent
    MH -->|HealthResult| Agent
    Agent -->|structured context| LLM[LLM API\nOpenAI / Gemini / Claude]
    LLM -->|narrative advice| Agent
    Agent -->|AdviceResponse| UI
    UI -->|renders sections| User
```

The entire application lives in **`app.py`**. Helper dataclasses and pure functions are defined in the same file, grouped by logical section with clear comments.

---

## Components and Interfaces

### 1. Input Layer (`render_input_form`)

Renders the Streamlit form and returns a validated `UserInput` dataclass. Raises `ValidationError` for invalid inputs before any calculation begins.

```python
@dataclass
class UserInput:
    annual_salary: float        # gross annual salary in INR
    deductions: float           # total 80C + HRA + other deductions
    investments: float          # additional investments (ELSS, PPF, etc.)
    age: int                    # current age in years
    monthly_income: float       # take-home monthly income
    monthly_expenses: float     # total monthly expenses
    current_savings: float      # existing corpus / savings
    goal_amount: float          # target financial goal in INR
    monthly_emi: float          # existing EMI obligations (for health score)
    emergency_fund_months: float  # months of expenses covered by liquid savings
```

### 2. Tax Wizard (`calculate_tax`)

Pure function — no side effects, no I/O.

```python
@dataclass
class TaxResult:
    old_regime_tax: float
    new_regime_tax: float
    savings_difference: float       # positive = old regime saves more
    recommended_regime: str         # "Old" | "New"
    marginal_difference: bool       # True if |difference| < 5000
    old_taxable_income: float
    new_taxable_income: float

def calculate_tax(salary: float, deductions: float) -> TaxResult: ...
```

**Old Regime slabs (FY 2024-25)**:
| Taxable Income | Rate |
|---|---|
| Up to ₹2,50,000 | 0% |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

Standard deduction: ₹50,000 (always applied for salaried).
Rebate u/s 87A: Full tax rebate if taxable income ≤ ₹5,00,000.

**New Regime slabs (FY 2024-25)**:
| Taxable Income | Rate |
|---|---|
| Up to ₹3,00,000 | 0% |
| ₹3,00,001 – ₹6,00,000 | 5% |
| ₹6,00,001 – ₹9,00,000 | 10% |
| ₹9,00,001 – ₹12,00,000 | 15% |
| ₹12,00,001 – ₹15,00,000 | 20% |
| Above ₹15,00,000 | 30% |

Standard deduction: ₹75,000 (new regime, FY 2024-25 budget).
Rebate u/s 87A: Full tax rebate if taxable income ≤ ₹7,00,000.

Health & Education Cess: 4% on computed tax (both regimes).

### 3. FIRE Path Planner (`calculate_fire`)

Pure function.

```python
@dataclass
class FireResult:
    savings_rate_pct: float         # monthly savings / monthly income * 100
    fire_corpus: float              # 25 × annual expenses
    required_sip: float             # monthly SIP to reach goal
    years_to_fire: float            # years to accumulate fire_corpus
    on_track: bool                  # True if current savings >= required_sip
    deficit: bool                   # True if expenses > income
    milestones: list[dict]          # [{year, projected_corpus}, ...]

def calculate_fire(
    age: int,
    monthly_income: float,
    monthly_expenses: float,
    current_savings: float,
    goal_amount: float,
    annual_return: float = 0.12
) -> FireResult: ...
```

**SIP formula** (future value of annuity):

```
FV = P × [((1 + r)^n - 1) / r] × (1 + r)
```

Where `r = annual_return / 12`, `n = months`, `P = monthly SIP`.

Solve for `P` given `FV = fire_corpus - current_savings`.

### 4. Money Health Score (`calculate_health_score`)

```python
@dataclass
class HealthResult:
    score: int                  # 0–100
    label: str                  # "Poor" | "Fair" | "Good" | "Excellent"
    breakdown: dict             # {"savings_rate": x, "dti": y, "emergency": z}
    top_factor: str             # factor with lowest sub-score

def calculate_health_score(
    monthly_income: float,
    monthly_savings: float,
    monthly_emi: float,
    emergency_fund_months: float
) -> HealthResult: ...
```

**Scoring weights**:
- Savings rate (40%): score = min(savings_rate_pct / 30 × 100, 100)
- Debt-to-income (30%): score = max(100 - (emi / income × 200), 0)
- Emergency fund (30%): score = min(emergency_fund_months / 6 × 100, 100)

### 5. AI Agent (`orchestrate`)

```python
@dataclass
class AdviceResponse:
    summary: str
    calculations: str
    recommendations: str
    disclaimer: str
    ai_enhanced: bool           # False if LLM call failed

def orchestrate(user_input: UserInput, api_key: str, model: str) -> AdviceResponse: ...
```

The agent:
1. Always runs Tax_Wizard and FIRE_Planner.
2. Runs Money_Health_Score if `monthly_emi` and `emergency_fund_months` are provided.
3. Builds a structured prompt containing all raw results.
4. Calls the selected LLM to generate narrative advice.
5. On LLM failure, falls back to a rule-based template that formats the raw numbers.

### 6. UI Renderer (`render_results`)

Renders `AdviceResponse` into three `st.expander` sections (Summary, Calculations, Recommendations) plus a disclaimer footer.

---

## Data Models

All models are Python `dataclass` instances. No persistence layer is needed — data lives in `st.session_state` for the duration of the browser session.

```python
# Lifecycle
st.session_state["user_input"]   : UserInput | None
st.session_state["advice"]       : AdviceResponse | None
st.session_state["loading"]      : bool
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Tax liability is non-negative
*For any* valid salary and deduction values, the computed tax under both the Old Regime and New Regime SHALL be greater than or equal to zero.
**Validates: Requirements 2.1, 2.2**

Property 2: Recommended regime has lower or equal tax
*For any* valid salary and deduction values, the recommended regime SHALL have a tax liability less than or equal to the non-recommended regime.
**Validates: Requirements 2.4, 2.5**

Property 3: Tax savings difference is consistent
*For any* valid salary and deduction values, `savings_difference` SHALL equal `|old_regime_tax - new_regime_tax|`.
**Validates: Requirements 2.3**

Property 4: Marginal difference flag is accurate
*For any* valid salary and deduction values, `marginal_difference` SHALL be True if and only if `|old_regime_tax - new_regime_tax| < 5000`.
**Validates: Requirements 7.1**

Property 5: Zero-deduction standard deduction still applied
*For any* salary with zero declared deductions, the Old Regime taxable income SHALL equal `salary - 50000` (standard deduction), not `salary`.
**Validates: Requirements 7.2**

Property 6: Below-exemption income yields zero tax
*For any* salary where taxable income falls below the basic exemption limit, the computed tax SHALL be zero for the respective regime.
**Validates: Requirements 7.3**

Property 7: FIRE corpus equals 25× annual expenses
*For any* valid monthly expenses value, `fire_corpus` SHALL equal `monthly_expenses × 12 × 25`.
**Validates: Requirements 3.3**

Property 8: Savings rate is bounded
*For any* valid monthly income and expenses, `savings_rate_pct` SHALL be in the range [0, 100].
**Validates: Requirements 3.1**

Property 9: On-track flag is consistent with SIP comparison
*For any* valid inputs, `on_track` SHALL be True if and only if `(monthly_income - monthly_expenses) >= required_sip`.
**Validates: Requirements 3.5**

Property 10: Money Health Score is bounded
*For any* valid income, savings, EMI, and emergency fund values, `score` SHALL be an integer in the range [0, 100].
**Validates: Requirements 6.1**

Property 11: Health score label matches score range
*For any* computed health score, the label SHALL be "Poor" for 0–39, "Fair" for 40–59, "Good" for 60–79, and "Excellent" for 80–100.
**Validates: Requirements 6.2**

---

## Error Handling

| Scenario | Handling |
|---|---|
| Empty required field | Streamlit form validation error; analysis blocked |
| Non-numeric input | Caught by `st.number_input`; type-safe by default |
| Negative numeric input | Post-submit validation raises `ValidationError` with field name |
| Monthly expenses > income | `FireResult.deficit = True`; UI shows warning banner |
| LLM API key missing | Warning shown; falls back to rule-based summary |
| LLM API call fails (timeout, rate limit, etc.) | Caught with `try/except`; `AdviceResponse.ai_enhanced = False`; rule-based fallback used |
| Tax income below exemption | Returns `tax = 0` without error |

---

## Testing Strategy

### Unit Tests (`test_app.py`)

Focus on specific examples and edge cases:
- Tax calculation for known salary/deduction combinations (spot-check against published slab tables)
- FIRE corpus formula with known inputs
- Health score boundary values (score = 0, 39, 40, 59, 60, 79, 80, 100)
- Validation rejection of negative and zero-income inputs
- Marginal difference flag at exactly ₹4,999 and ₹5,000 difference

### Property-Based Tests (using `hypothesis`)

Each property from the Correctness Properties section is implemented as a single `@given` test with a minimum of 100 examples.

Tag format: `# Feature: ai-money-mentor, Property N: <property_text>`

- **Property 1** — `@given(salary, deductions)` → assert `tax >= 0` for both regimes
- **Property 2** — `@given(salary, deductions)` → assert recommended regime tax ≤ other regime tax
- **Property 3** — `@given(salary, deductions)` → assert `savings_difference == abs(old - new)`
- **Property 4** — `@given(salary, deductions)` → assert `marginal_difference == (abs(old - new) < 5000)`
- **Property 5** — `@given(salary)` with deductions=0 → assert old taxable income == salary - 50000
- **Property 6** — `@given(salary below exemption)` → assert tax == 0
- **Property 7** — `@given(monthly_expenses)` → assert fire_corpus == monthly_expenses * 12 * 25
- **Property 8** — `@given(income, expenses)` → assert 0 <= savings_rate_pct <= 100
- **Property 9** — `@given(income, expenses, sip)` → assert on_track consistency
- **Property 10** — `@given(income, savings, emi, emergency)` → assert 0 <= score <= 100
- **Property 11** — `@given(score in 0..100)` → assert label matches range

**Library**: `hypothesis` (pip install hypothesis)
**Minimum iterations**: 100 per property (Hypothesis default; increase with `settings(max_examples=200)` for critical properties)
