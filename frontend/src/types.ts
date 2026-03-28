export interface FormData {
  // Tax
  annual_salary: number;
  deductions: number;
  investments: number;
  has_80c: boolean;
  has_nps: boolean;
  has_hra: boolean;
  has_home_loan: boolean;
  has_health_insurance: boolean;
  risk_profile: string;
  // FIRE
  age: number;
  monthly_income: number;
  monthly_expenses: number;
  current_savings: number;
  goal_amount: number;
  retirement_age: number;
  // Health
  monthly_emi: number;
  emergency_fund_months: number;
  has_term_insurance: boolean;
  has_health_cover: boolean;
  health_cover_lakhs: number;
  num_asset_classes: number;
  annual_tax_saved: number;
  has_retirement_account: boolean;
}

export interface AnalyseResponse {
  tax_old: number;
  tax_new: number;
  tax_recommended: string;
  tax_savings_diff: number;
  tax_marginal: boolean;
  missing_deductions: { name: string; max_amount: number; description: string }[];
  tax_suggestions: { name: string; risk: string; liquidity: string; return_pct: number; section: string; description: string }[];

  fire_savings_rate: number;
  fire_corpus: number;
  fire_required_sip: number;
  fire_years: number;
  fire_on_track: boolean;
  fire_deficit: boolean;
  fire_monthly_roadmap: { month: number; corpus: number; sip: number; equity_pct: number }[];
  fire_yearly_milestones: { year: number; age: number; projected_corpus: number }[];
  fire_asset_allocation: { asset: string; pct: number }[];
  fire_insurance_gaps: string[];

  health_score: number;
  health_label: string;
  health_dimensions: Record<string, number>;
  health_top_factor: string;

  summary: string;
  recommendations: string;
  disclaimer: string;
  ai_enhanced: boolean;
}
