import React, { useState } from "react";
import type { FormData } from "../types";
import { FileStack, Flame, ShieldAlert } from "lucide-react";

interface Props { onSubmit: (d: FormData) => void; loading: boolean; }

const INIT: FormData = {
  annual_salary: 3200000, deductions: 0, investments: 0,
  has_80c: true, has_nps: false, has_hra: true,
  has_home_loan: false, has_health_insurance: false,
  risk_profile: "moderate",
  age: 29, monthly_income: 0, monthly_expenses: 0,
  current_savings: 0, goal_amount: 0, retirement_age: 45,
  monthly_emi: 0, emergency_fund_months: 0,
  has_term_insurance: false, has_health_cover: false,
  health_cover_lakhs: 0, num_asset_classes: 1,
  annual_tax_saved: 0, has_retirement_account: false,
};

function Num({ label, name, value, onChange, min = 0, step = 1000, prefix = "₹" }: {
  label: string; name: keyof FormData; value: number;
  onChange: (n: keyof FormData, v: number) => void; min?: number; step?: number; prefix?: string;
}) {
  return (
    <div className="field">
      <div className="input-container" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '0.6rem 1rem' }}>
        <label htmlFor={name} className="field-label" style={{ marginBottom: '0.2rem' }}>{label}</label>
        <div style={{ display: 'flex', width: '100%', gap: '0.5rem', alignItems: 'center' }}>
          {prefix && <span className="input-prefix">{prefix}</span>}
          <input id={name} type="number" min={min} step={step} value={value || ""}
            onChange={e => onChange(name, parseFloat(e.target.value) || 0)} 
            placeholder="0" />
        </div>
      </div>
    </div>
  );
}

function Check({ label, name, value, onChange }: {
  label: string; name: keyof FormData; value: boolean;
  onChange: (n: keyof FormData, v: boolean) => void;
}) {
  return (
    <div className="toggle-wrapper">
      <span>{label}</span>
      <label className="toggle-label">
        <input type="checkbox" checked={value} onChange={e => onChange(name, e.target.checked)} />
        <div className="toggle-track"></div>
      </label>
    </div>
  );
}

export default function InputForm({ onSubmit, loading }: Props) {
  const [f, setF] = useState<FormData>(INIT);

  const setN = (n: keyof FormData, v: number) => setF(p => ({ ...p, [n]: v }));
  const setB = (n: keyof FormData, v: boolean) => setF(p => ({ ...p, [n]: v }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Inject sensible derivations for backend-required fields that are hidden for minimalism
    const payload = { ...f };
    payload.monthly_income = payload.annual_salary / 12 || 10000;
    payload.monthly_expenses = payload.monthly_income * 0.4; // Mock generic 40% expense ratio
    payload.deductions = 150000; // Mock 1.5L
    
    onSubmit(payload);
  };

  return (
    <form id="main-form" onSubmit={submit}>
      
      {/* Tax Configuration */}
      <div className="card">
        <div className="card-header">
          <h3>Tax Configuration</h3>
          <FileStack size={18} color="var(--text-secondary)" />
        </div>
        <div className="form-grid">
          <Num label="Gross Annual Income" name="annual_salary" value={f.annual_salary} onChange={setN} />
          
          <div style={{ marginTop: '0.5rem' }}>
            <div className="field-label" style={{ marginBottom: '0.5rem' }}>Deductions Claimed</div>
            <div style={{ background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)', padding: '0 1rem' }}>
              <Check label="80C (ELSS/PPF/LIC)" name="has_80c" value={f.has_80c} onChange={setB} />
              <Check label="HRA (House Rent Allowance)" name="has_hra" value={f.has_hra} onChange={setB} />
            </div>
          </div>
        </div>
      </div>

      {/* FIRE Planner */}
      <div className="card">
        <div className="card-header">
          <h3>FIRE Trajectory Planner</h3>
          <Flame size={18} color="var(--text-secondary)" />
        </div>
        <div className="form-grid">
          <div className="split-grid">
            <Num label="Current Age" name="age" prefix="" step={1} value={f.age} onChange={setN} />
            <Num label="Retire Age" name="retirement_age" prefix="" step={1} value={f.retirement_age} onChange={setN} />
          </div>
          <Num label="Target FIRE Corpus" name="goal_amount" value={f.goal_amount} onChange={setN} />
        </div>
      </div>

      {/* Financial Health Diagnostics */}
      <div className="card">
        <div className="card-header">
          <h3>Financial Health Diagnostics</h3>
          <ShieldAlert size={18} color="var(--text-secondary)" />
        </div>
        <div className="form-grid">
          <Num label="Total Liquid Assets" name="current_savings" value={f.current_savings} onChange={setN} />
          
          <div style={{ marginTop: '0.5rem' }}>
             <div className="field-label" style={{ marginBottom: '0.5rem' }}>Protection Status</div>
             <div style={{ background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)', padding: '0 1rem' }}>
               <Check label="Term Life Insurance" name="has_term_insurance" value={f.has_term_insurance} onChange={setB} />
               <Check label="Comprehensive Health Cover" name="has_health_cover" value={f.has_health_cover} onChange={setB} />
             </div>
          </div>
        </div>
      </div>

      <button type="submit" className="btn-report" disabled={loading} style={{ marginTop: '1.5rem', opacity: loading ? 0.6 : 1 }}>
        {loading ? "PROCESSING..." : "GENERATE REPORT"}
      </button>

    </form>
  );
}
