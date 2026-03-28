import React, { useState } from "react";
import type { FormData } from "../types";

interface Props { onSubmit: (d: FormData) => void; loading: boolean; }

const INIT: FormData = {
  annual_salary: 0, deductions: 0, investments: 0,
  has_80c: false, has_nps: false, has_hra: false,
  has_home_loan: false, has_health_insurance: false,
  risk_profile: "moderate",
  age: 30, monthly_income: 0, monthly_expenses: 0,
  current_savings: 0, goal_amount: 0, retirement_age: 60,
  monthly_emi: 0, emergency_fund_months: 0,
  has_term_insurance: false, has_health_cover: false,
  health_cover_lakhs: 0, num_asset_classes: 1,
  annual_tax_saved: 0, has_retirement_account: false,
};

function Num({ label, name, value, onChange, min = 0, step = 1000 }: {
  label: string; name: keyof FormData; value: number;
  onChange: (n: keyof FormData, v: number) => void; min?: number; step?: number;
}) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input id={name} type="number" min={min} step={step} value={value}
        onChange={e => onChange(name, parseFloat(e.target.value) || 0)} />
    </div>
  );
}

function Check({ label, name, value, onChange }: {
  label: string; name: keyof FormData; value: boolean;
  onChange: (n: keyof FormData, v: boolean) => void;
}) {
  return (
    <label className="check-label">
      <input type="checkbox" checked={value}
        onChange={e => onChange(name, e.target.checked)} />
      {label}
    </label>
  );
}

export default function InputForm({ onSubmit, loading }: Props) {
  const [f, setF] = useState<FormData>(INIT);
  const [err, setErr] = useState("");

  const setN = (n: keyof FormData, v: number) => setF(p => ({ ...p, [n]: v }));
  const setB = (n: keyof FormData, v: boolean) => setF(p => ({ ...p, [n]: v }));
  const setS = (n: keyof FormData, v: string) => setF(p => ({ ...p, [n]: v }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    if (f.monthly_income <= 0) { setErr("Monthly income must be > 0."); return; }
    onSubmit(f);
  };

  return (
    <form onSubmit={submit}>
      {/* ── Tax ── */}
      <div className="card">
        <h2>🧾 Tax Details</h2>
        <div className="form-grid">
          <Num label="Annual Salary (₹)" name="annual_salary" value={f.annual_salary} onChange={setN} />
          <Num label="Declared Deductions (₹)" name="deductions" value={f.deductions} onChange={setN} />
          <Num label="Additional Investments (₹)" name="investments" value={f.investments} onChange={setN} />
          <Num label="Tax Saved This Year (₹)" name="annual_tax_saved" value={f.annual_tax_saved} onChange={setN} />
        </div>
        <div className="check-group">
          <p className="check-title">Deductions already claimed:</p>
          <Check label="80C (ELSS/PPF/LIC)" name="has_80c" value={f.has_80c} onChange={setB} />
          <Check label="NPS 80CCD(1B)" name="has_nps" value={f.has_nps} onChange={setB} />
          <Check label="HRA" name="has_hra" value={f.has_hra} onChange={setB} />
          <Check label="Home Loan Interest 24(b)" name="has_home_loan" value={f.has_home_loan} onChange={setB} />
          <Check label="Health Insurance 80D" name="has_health_insurance" value={f.has_health_insurance} onChange={setB} />
        </div>
        <div className="field" style={{ marginTop: "0.75rem" }}>
          <label>Risk Profile</label>
          <select value={f.risk_profile} onChange={e => setS("risk_profile", e.target.value)}>
            <option value="conservative">Conservative</option>
            <option value="moderate">Moderate</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </div>
      </div>

      {/* ── FIRE ── */}
      <div className="card">
        <h2>🔥 FIRE Path Planner</h2>
        <div className="form-grid">
          <Num label="Current Age" name="age" value={f.age} onChange={setN} min={18} step={1} />
          <Num label="Target Retirement Age" name="retirement_age" value={f.retirement_age} onChange={setN} min={30} step={1} />
          <Num label="Monthly Take-Home Income (₹)" name="monthly_income" value={f.monthly_income} onChange={setN} />
          <Num label="Monthly Expenses (₹)" name="monthly_expenses" value={f.monthly_expenses} onChange={setN} step={500} />
          <Num label="Current Savings / Corpus (₹)" name="current_savings" value={f.current_savings} onChange={setN} step={10000} />
          <Num label="Financial Goal Amount (₹)" name="goal_amount" value={f.goal_amount} onChange={setN} step={10000} />
        </div>
      </div>

      {/* ── Health ── */}
      <div className="card">
        <h2>💊 Financial Health</h2>
        <div className="form-grid">
          <Num label="Monthly EMI (₹)" name="monthly_emi" value={f.monthly_emi} onChange={setN} step={500} />
          <Num label="Emergency Fund (months)" name="emergency_fund_months" value={f.emergency_fund_months} onChange={setN} step={0.5} />
          <Num label="Health Cover (₹ Lakhs)" name="health_cover_lakhs" value={f.health_cover_lakhs} onChange={setN} step={1} />
          <Num label="Asset Classes Invested In (1–6)" name="num_asset_classes" value={f.num_asset_classes} onChange={setN} min={1} step={1} />
        </div>
        <div className="check-group">
          <Check label="Have Term Insurance" name="has_term_insurance" value={f.has_term_insurance} onChange={setB} />
          <Check label="Have Health Insurance" name="has_health_cover" value={f.has_health_cover} onChange={setB} />
          <Check label="Have NPS / EPF / PPF account" name="has_retirement_account" value={f.has_retirement_account} onChange={setB} />
        </div>
      </div>

      {err && <div className="error-box">{err}</div>}
      <button className="btn-primary" type="submit" disabled={loading}>
        {loading ? "Analysing…" : "💡 Generate Financial Plan"}
      </button>
    </form>
  );
}
