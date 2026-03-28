# Implementation Plan: AI Money Mentor

## Overview

Implement the AI Money Mentor Streamlit application incrementally, starting with the pure calculation core, then the AI agent layer, then the UI, and finally wiring everything together. Each step is independently testable.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `app.py` with section scaffolding (imports, dataclasses, constants, functions, UI)
  - Create `requirements.txt` with: `streamlit`, `openai`, `google-generativeai`, `anthropic`, `hypothesis`, `pytest`
  - Define all dataclasses: `UserInput`, `TaxResult`, `FireResult`, `HealthResult`, `AdviceResponse`
  - Define the `ValidationError` exception class
  - _Requirements: 1.1, 4.1_

- [x] 2. Implement Tax Wizard
  - [x] 2.1 Implement `calculate_tax(salary, deductions) -> TaxResult`
    - Apply Old Regime slabs (FY 2024-25) with ₹50,000 standard deduction and 87A rebate (≤₹5L)
    - Apply New Regime slabs (FY 2024-25) with ₹75,000 standard deduction and 87A rebate (≤₹7L)
    - Apply 4% health & education cess on both
    - Compute `savings_difference`, `recommended_regime`, `marginal_difference` (< ₹5,000 threshold)
    - Handle below-exemption income → tax = 0
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 7.1, 7.2, 7.3_

  - [ ]* 2.2 Write property tests for Tax Wizard
    - **Property 1: Tax liability is non-negative** — `@given(salary, deductions)` assert both regime taxes ≥ 0
    - **Validates: Requirements 2.1, 2.2**
    - **Property 2: Recommended regime has lower or equal tax** — assert recommended tax ≤ other tax
    - **Validates: Requirements 2.4, 2.5**
    - **Property 3: Tax savings difference is consistent** — assert `savings_difference == abs(old - new)`
    - **Validates: Requirements 2.3**
    - **Property 4: Marginal difference flag is accurate** — assert `marginal_difference == (abs(old - new) < 5000)`
    - **Validates: Requirements 7.1**
    - **Property 5: Zero-deduction standard deduction still applied** — assert old taxable income == salary - 50000 when deductions=0
    - **Validates: Requirements 7.2**
    - **Property 6: Below-exemption income yields zero tax** — assert tax == 0 for salary below exemption limit
    - **Validates: Requirements 7.3**

- [x] 3. Implement FIRE Path Planner
  - [x] 3.1 Implement `calculate_fire(age, monthly_income, monthly_expenses, current_savings, goal_amount, annual_return=0.12) -> FireResult`
    - Compute savings rate: `(income - expenses) / income * 100`, clamped to [0, 100]
    - Compute FIRE corpus: `monthly_expenses * 12 * 25`
    - Solve for required SIP using FV annuity formula: `P = FV * r / (((1+r)^n - 1) * (1+r))`
    - Compute `years_to_fire`, set `on_track` and `deficit` flags
    - Generate yearly milestone list `[{year, projected_corpus}]`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 3.2 Write property tests for FIRE Planner
    - **Property 7: FIRE corpus equals 25× annual expenses** — `@given(monthly_expenses)` assert `fire_corpus == monthly_expenses * 12 * 25`
    - **Validates: Requirements 3.3**
    - **Property 8: Savings rate is bounded** — `@given(income, expenses)` assert `0 <= savings_rate_pct <= 100`
    - **Validates: Requirements 3.1**
    - **Property 9: On-track flag is consistent with SIP comparison** — assert `on_track == ((income - expenses) >= required_sip)`
    - **Validates: Requirements 3.5**

- [x] 4. Checkpoint — Ensure all tests pass
  - Run `pytest test_app.py -v` and confirm all property and unit tests pass. Ask the user if any questions arise.

- [x] 5. Implement Money Health Score
  - [x] 5.1 Implement `calculate_health_score(monthly_income, monthly_savings, monthly_emi, emergency_fund_months) -> HealthResult`
    - Savings rate sub-score: `min(savings_rate_pct / 30 * 100, 100)` × 0.40
    - DTI sub-score: `max(100 - (emi / income * 200), 0)` × 0.30
    - Emergency fund sub-score: `min(emergency_fund_months / 6 * 100, 100)` × 0.30
    - Compute composite score (0–100 integer), assign label, identify `top_factor`
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 5.2 Write property tests for Money Health Score
    - **Property 10: Money Health Score is bounded** — `@given(income, savings, emi, emergency)` assert `0 <= score <= 100`
    - **Validates: Requirements 6.1**
    - **Property 11: Health score label matches score range** — `@given(score in 0..100)` assert label matches defined ranges
    - **Validates: Requirements 6.2**

- [x] 6. Implement input validation
  - [x] 6.1 Implement `validate_inputs(user_input: UserInput) -> None` (raises `ValidationError`)
    - Reject negative values for all numeric fields
    - Reject zero monthly income
    - Return descriptive error messages identifying the offending field
    - _Requirements: 1.2, 1.4_

  - [ ]* 6.2 Write unit tests for input validation
    - Test rejection of negative salary, negative expenses, zero income
    - Test acceptance of valid boundary values (e.g., salary = 0 deductions = 0)
    - _Requirements: 1.2, 1.4_

- [x] 7. Implement AI Agent orchestration
  - [x] 7.1 Implement `build_prompt(tax: TaxResult, fire: FireResult, health: HealthResult | None) -> str`
    - Construct a structured prompt with all raw calculation results
    - Include instructions to produce Summary, Calculations, Recommendations sections
    - Include the disclaimer instruction
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 7.2 Implement `call_llm(prompt: str, api_key: str, model: str) -> str`
    - Support OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`), and Anthropic Claude (`claude-3-haiku`)
    - Wrap in `try/except`; return `None` on failure
    - _Requirements: 4.4_

  - [x] 7.3 Implement `build_rule_based_response(tax: TaxResult, fire: FireResult, health: HealthResult | None) -> AdviceResponse`
    - Format raw numbers into Summary, Calculations, Recommendations strings
    - Include at least two actionable suggestions in Recommendations
    - Always populate `disclaimer` field
    - Set `ai_enhanced = False`
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [x] 7.4 Implement `orchestrate(user_input: UserInput, api_key: str, model: str) -> AdviceResponse`
    - Call `calculate_tax`, `calculate_fire`, optionally `calculate_health_score`
    - Call `call_llm`; on failure use `build_rule_based_response`
    - Parse LLM response into `AdviceResponse` sections
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8. Checkpoint — Ensure all tests pass
  - Run `pytest test_app.py -v` and confirm all tests pass. Ask the user if any questions arise.

- [x] 9. Implement Streamlit UI
  - [x] 9.1 Implement `render_input_form() -> UserInput | None`
    - Render all input fields using `st.number_input` and `st.text_input` inside `st.form`
    - Add "Generate Financial Plan" submit button
    - Call `validate_inputs` on submit; display `st.error` on `ValidationError`
    - Show `st.spinner` while analysis runs
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 5.5_

  - [x] 9.2 Implement `render_results(advice: AdviceResponse) -> None`
    - Render three `st.expander` sections: Summary, Calculations, Recommendations
    - Render disclaimer in `st.info` at the bottom
    - If `not advice.ai_enhanced`, show `st.warning` that AI advice is unavailable
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 9.3 Wire the main app entry point
    - Add LLM provider selector (`st.selectbox`) and API key input (`st.text_input`, type="password") in `st.sidebar`
    - Call `render_input_form()`, then `orchestrate()`, then `render_results()` in sequence
    - Store results in `st.session_state`
    - _Requirements: 1.5, 4.1, 5.1_

- [x] 10. Final checkpoint — Ensure all tests pass and app runs
  - Run `pytest test_app.py -v` and confirm all tests pass.
  - Verify the app starts with `streamlit run app.py` (run manually in terminal).
  - Ask the user if any questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use the `hypothesis` library with `@given` decorators
- The LLM call is always wrapped in try/except — the app works fully without an API key via rule-based fallback
- Run tests with: `pytest test_app.py -v`
- Run the app with: `streamlit run app.py`
