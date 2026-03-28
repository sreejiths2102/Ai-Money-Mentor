# Requirements Document

## Introduction

AI Money Mentor is a Streamlit-based web application that provides personalized financial guidance to Indian users. The system collects user financial data, runs intelligent analysis through an AI agent, and delivers actionable advice across two core modules: a Tax Wizard (comparing old vs new Indian tax regimes) and a FIRE Path Planner (calculating savings rate and SIP targets for financial independence). An optional Money Health Score provides a holistic snapshot of the user's financial wellness.

## Glossary

- **Tax_Wizard**: The module that computes income tax under both Indian tax regimes and recommends the better option.
- **FIRE_Planner**: The module that calculates the savings rate, SIP amount, and years to financial independence.
- **AI_Agent**: The orchestration layer that interprets user input, invokes the appropriate modules, and synthesises results into human-readable advice.
- **Money_Health_Score**: A composite numeric score (0–100) reflecting the user's overall financial wellness.
- **SIP**: Systematic Investment Plan — a fixed monthly investment into a mutual fund or similar instrument.
- **Old_Regime**: The Indian income-tax regime that allows deductions (e.g., 80C, HRA, standard deduction).
- **New_Regime**: The Indian income-tax regime with lower slab rates but fewer deductions.
- **FIRE**: Financial Independence, Retire Early — the goal of accumulating enough wealth to live off investment returns.
- **UI**: The Streamlit user interface presented to the user in a web browser.
- **Disclaimer**: A mandatory notice that the output is AI-generated guidance and not licensed financial advice.

---

## Requirements

### Requirement 1: User Input Collection

**User Story:** As a user, I want to enter my financial details in a single form, so that the system can analyse my situation without requiring multiple screens.

#### Acceptance Criteria

1. THE UI SHALL display a single input form containing fields for: annual salary, total deductions (80C, HRA, etc.), investment amounts, age, monthly expenses, current savings, and financial goals.
2. WHEN a user submits the form with one or more required fields left empty, THE UI SHALL display a descriptive validation error and prevent analysis from proceeding.
3. WHEN a user enters a non-numeric value in any numeric field, THE UI SHALL display a descriptive validation error and prevent analysis from proceeding.
4. WHEN a user enters a negative value in any field that requires a non-negative number, THE UI SHALL display a descriptive validation error and prevent analysis from proceeding.
5. THE UI SHALL provide a clearly labelled "Generate Financial Plan" button that triggers the analysis pipeline.

---

### Requirement 2: Tax Wizard — Regime Comparison

**User Story:** As a salaried Indian taxpayer, I want to compare my tax liability under both the old and new tax regimes, so that I can choose the option that minimises my tax outgo.

#### Acceptance Criteria

1. WHEN a user submits valid salary and deduction data, THE Tax_Wizard SHALL calculate income tax payable under the Old_Regime using the applicable Indian tax slabs and the provided deductions.
2. WHEN a user submits valid salary and deduction data, THE Tax_Wizard SHALL calculate income tax payable under the New_Regime using the applicable Indian tax slabs without deductions.
3. WHEN both regime calculations are complete, THE Tax_Wizard SHALL compute the tax savings difference between the two regimes.
4. WHEN both regime calculations are complete, THE Tax_Wizard SHALL recommend the regime with the lower tax liability.
5. IF the tax liability under both regimes is equal, THEN THE Tax_Wizard SHALL recommend the New_Regime as the default.
6. THE Tax_Wizard SHALL apply a standard deduction of ₹50,000 under the Old_Regime for salaried individuals.
7. THE Tax_Wizard SHALL apply the health and education cess of 4% on the computed tax under both regimes.

---

### Requirement 3: FIRE Path Planner

**User Story:** As a user planning for financial independence, I want to know how much I need to invest monthly and how many years it will take to reach my goal, so that I can build a concrete savings plan.

#### Acceptance Criteria

1. WHEN a user submits valid age, income, monthly expenses, savings, and goal data, THE FIRE_Planner SHALL calculate the user's current monthly savings rate as a percentage of monthly income.
2. WHEN the savings rate is calculated, THE FIRE_Planner SHALL estimate the monthly SIP amount required to reach the stated financial goal within a reasonable timeframe, assuming a default annual return of 12%.
3. WHEN the SIP amount is calculated, THE FIRE_Planner SHALL estimate the number of years required to achieve financial independence based on the 25× annual expenses rule (FIRE corpus = 25 × annual expenses).
4. WHEN the FIRE corpus target is computed, THE FIRE_Planner SHALL produce a month-by-month or year-by-year investment milestone plan.
5. IF the user's current monthly savings already exceed the required SIP amount, THEN THE FIRE_Planner SHALL indicate that the user is on track and display the projected FIRE date.
6. IF the user's monthly expenses exceed monthly income, THEN THE FIRE_Planner SHALL flag a deficit and recommend expense reduction before investing.

---

### Requirement 4: AI Agent Orchestration

**User Story:** As a user, I want the system to automatically decide which analysis to run and combine the results into clear, actionable advice, so that I do not need to navigate separate tools.

#### Acceptance Criteria

1. WHEN a user submits the form, THE AI_Agent SHALL determine which modules (Tax_Wizard, FIRE_Planner, or both) are applicable based on the provided inputs.
2. WHEN module results are available, THE AI_Agent SHALL synthesise the outputs into a single human-readable response covering: Summary, Calculations, and Recommendations sections.
3. WHEN generating recommendations, THE AI_Agent SHALL provide at least two actionable suggestions (e.g., "Increase 80C investments by ₹X to reduce tax") rather than only presenting numbers.
4. WHEN the AI model API call fails or returns an error, THE AI_Agent SHALL fall back to a rule-based summary generated from the raw calculation results and notify the user that AI-enhanced advice is unavailable.
5. THE AI_Agent SHALL include the Disclaimer in every generated response.

---

### Requirement 5: Output Display

**User Story:** As a user, I want the analysis results displayed in clearly labelled sections, so that I can quickly find the information most relevant to me.

#### Acceptance Criteria

1. WHEN analysis is complete, THE UI SHALL display results in three distinct sections: "Summary", "Calculations", and "Recommendations".
2. WHEN the Tax_Wizard results are displayed, THE UI SHALL show tax payable under both regimes, the savings difference, and the recommended regime.
3. WHEN the FIRE_Planner results are displayed, THE UI SHALL show the savings rate, required SIP amount, FIRE corpus target, and estimated years to financial independence.
4. WHEN results are displayed, THE UI SHALL render the Disclaimer prominently at the bottom of the output.
5. WHEN the analysis is running, THE UI SHALL display a loading indicator to inform the user that processing is in progress.

---

### Requirement 6: Money Health Score (Optional Enhancement)

**User Story:** As a user, I want a single score that summarises my financial health, so that I can quickly gauge how well I am managing my money.

#### Acceptance Criteria

1. WHERE the Money Health Score feature is enabled, THE Money_Health_Score SHALL be computed as a weighted composite of: savings rate (40%), debt-to-income ratio (30%), and emergency fund coverage in months (30%), scaled to a range of 0–100.
2. WHERE the Money Health Score feature is enabled, THE UI SHALL display the score alongside a qualitative label: "Poor" (0–39), "Fair" (40–59), "Good" (60–79), or "Excellent" (80–100).
3. WHERE the Money Health Score feature is enabled, THE UI SHALL display a brief explanation of the factors that most influenced the score.

---

### Requirement 7: Edge Case — Dual-Regime Benefit

**User Story:** As a user with a complex salary structure, I want the system to correctly handle the scenario where both regimes produce a similar tax outcome, so that I receive an accurate recommendation.

#### Acceptance Criteria

1. WHEN the tax difference between the Old_Regime and New_Regime is less than ₹5,000, THE Tax_Wizard SHALL flag the result as "marginal difference" and present both options with a note that either regime is acceptable.
2. WHEN a user has zero declared deductions, THE Tax_Wizard SHALL still apply the standard deduction of ₹50,000 under the Old_Regime before computing tax.
3. WHEN a user's taxable income falls below the basic exemption limit (₹2,50,000 for Old_Regime; ₹3,00,000 for New_Regime), THE Tax_Wizard SHALL return a tax liability of ₹0 for the respective regime.
