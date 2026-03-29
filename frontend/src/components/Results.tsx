import type { AnalyseResponse } from "../types";
import { AlertTriangle, Activity } from "lucide-react";

const fmt = (n: number) =>
  "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });

export default function Results({ data }: { data: AnalyseResponse }) {
  // Convert monthly roadmap to "quarter" labels for the design
  const roadmapQs = data.fire_monthly_roadmap.filter((_, i) => i % 3 === 0).slice(0, 4);

  return (
    <div className="results-container">
      
      {/* Executive Summary */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "1.25rem", color: "var(--text-primary)" }}>Executive Summary</h3>
        </div>
        <p className="summary-text" dangerouslySetInnerHTML={{
          __html: data.summary.replace("highly efficient", "<strong>highly efficient</strong>")
        }} />
      </div>

      {/* Grid for Tax Matrix and Alerts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1rem" }}>
        
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="section-title">
            <span>TAX OPTIMIZATION MATRIX</span>
          </div>
          <div className="matrix-grid">
            <div className="matrix-box">
              <span className="matrix-label">Old Regime</span>
              <span className="matrix-value">{fmt(data.tax_old)}</span>
            </div>
            <div className="matrix-box">
              <span className="matrix-label">New Regime</span>
              <span className="matrix-value">{fmt(data.tax_new)}</span>
            </div>
          </div>
          <div className="retained-box">
            <span className="matrix-label">CAPITAL RETAINED (ANNUAL DELTA)</span>
            <span className="matrix-value">+ {fmt(data.tax_savings_diff)}</span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="section-title">
            <span><AlertTriangle size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px', color: 'var(--status-warning)' }} /> EXEMPTION ALERTS</span>
          </div>
          {data.missing_deductions.length > 0 ? (
            <div className="alert-box">
              Missing <strong>{data.missing_deductions[0].name}</strong> deduction. 
              Potential saving: <strong>{fmt(data.missing_deductions[0].max_amount)}</strong>.
            </div>
          ) : (
            <div className="alert-box" style={{ borderColor: 'var(--status-success)', color: 'var(--status-success)' }}>
              All major 80C/80D/24b deductions optimally utilized. Tax structure is highly efficient.
            </div>
          )}
        </div>

      </div>

      {/* Quarterly Roadmap */}
      <div className="card">
        <div className="card-header" style={{ marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "1rem", color: "var(--text-primary)" }}>Quarterly Roadmap</h3>
          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: "0.6rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", display: "block" }}>TARGET CORPUS</span>
            <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>{fmt(data.fire_corpus)}</span>
          </div>
        </div>
        <div className="table-container" style={{ margin: 0, border: 'none', background: 'transparent' }}>
          <table>
            <thead>
              <tr>
                <th>Timeline</th>
                <th>Corpus Proj.</th>
                <th>Equity Ratio</th>
              </tr>
            </thead>
            <tbody>
              {roadmapQs.map((r, i) => (
                <tr key={i}>
                  <td>Q{i + 1} 2024</td>
                  <td>{fmt(r.corpus)}</td>
                  <td><span className="badge-tag">{r.equity_pct}% HIGH</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dimensions of Health Radial */}
      <div className="card" style={{ marginTop: "1rem" }}>
        <div className="radial-container">
          <div className="radial-wrapper" style={{background: `conic-gradient(var(--accent-gold) ${data.health_score}%, var(--bg-input) 0)`}}>
            <div className="radial-inner">
              <span className="radial-value">{data.health_score}</span>
              <span className="radial-label">INTEGRITY</span>
            </div>
          </div>
          
          <div className="health-bars">
             <div className="section-title" style={{ marginBottom: "0.5rem" }}>
               <span>DIMENSIONS OF HEALTH</span>
             </div>
             
             {Object.entries(data.health_dimensions).slice(0, 3).map(([k, v]) => (
                <div key={k} className="health-bar-item">
                  <div className="bar-header">
                    <span>{k.replace(/_/g, " ")}</span>
                    <span>{v}%</span>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${v}%` }}></div>
                  </div>
                </div>
             ))}
          </div>
        </div>
      </div>

      <div className="disclaimer">
        {data.disclaimer}
      </div>
      
    </div>
  );
}
