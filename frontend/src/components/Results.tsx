import { useState } from "react";
import type { AnalyseResponse } from "../types";

const fmt = (n: number) =>
  "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });

function Section({ title, children, open: defaultOpen = false }: {
  title: string; children: React.ReactNode; open?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card">
      <button className="section-toggle" onClick={() => setOpen(o => !o)}>
        <span>{title}</span><span>{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="section-body">{children}</div>}
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  const color = value >= 70 ? "#48bb78" : value >= 40 ? "#ed8936" : "#fc8181";
  return (
    <div style={{ marginBottom: "0.6rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", marginBottom: "2px" }}>
        <span style={{ textTransform: "capitalize" }}>{label.replace(/_/g, " ")}</span>
        <span style={{ fontWeight: 600 }}>{value.toFixed(0)}/100</span>
      </div>
      <div style={{ background: "#e2e8f0", borderRadius: 99, height: 8 }}>
        <div style={{ width: `${value}%`, background: color, borderRadius: 99, height: 8, transition: "width .4s" }} />
      </div>
    </div>
  );
}

export default function Results({ data }: { data: AnalyseResponse }) {
  return (
    <div className="results">
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Your Financial Plan</h2>
        <span className={data.ai_enhanced ? "badge-ai" : "badge-rule"}>
          {data.ai_enhanced ? "✨ AI Enhanced" : "📊 Rule-Based"}
        </span>
      </div>

      {/* Summary */}
      <Section title="📊 Summary" open>
        <p style={{ lineHeight: 1.7 }}>{data.summary}</p>
      </Section>

      {/* Tax Wizard */}
      <Section title="🧾 Tax Wizard" open>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
          {[
            ["Old Regime Tax", fmt(data.tax_old)],
            ["New Regime Tax", fmt(data.tax_new)],
            ["Recommended", data.tax_recommended + " Regime"],
            ["Savings Difference", fmt(data.tax_savings_diff)],
          ].map(([k, v]) => (
            <div key={k} style={{ background: "#f7fafc", borderRadius: 8, padding: "0.6rem 0.9rem" }}>
              <div style={{ fontSize: "0.75rem", color: "#718096" }}>{k}</div>
              <div style={{ fontWeight: 700, fontSize: "1rem" }}>{v}</div>
            </div>
          ))}
        </div>
        {data.tax_marginal && (
          <p style={{ color: "#d69e2e", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            ⚠️ Marginal difference — either regime is acceptable.
          </p>
        )}
        {data.missing_deductions.length > 0 && (
          <>
            <p style={{ fontWeight: 600, marginBottom: "0.4rem" }}>🔍 Missing Deductions</p>
            {data.missing_deductions.map(d => (
              <div key={d.name} style={{ background: "#fffbeb", border: "1px solid #f6e05e",
                borderRadius: 6, padding: "0.5rem 0.75rem", marginBottom: "0.4rem", fontSize: "0.85rem" }}>
                <strong>{d.name}</strong> — up to {fmt(d.max_amount)}<br />
                <span style={{ color: "#718096" }}>{d.description}</span>
              </div>
            ))}
          </>
        )}
        <p style={{ fontWeight: 600, margin: "0.75rem 0 0.4rem" }}>💡 Tax-Saving Suggestions (ranked for your profile)</p>
        {data.tax_suggestions.map(s => (
          <div key={s.name} style={{ background: "#f0fff4", border: "1px solid #9ae6b4",
            borderRadius: 6, padding: "0.5rem 0.75rem", marginBottom: "0.4rem", fontSize: "0.85rem" }}>
            <strong>{s.name}</strong> ({s.section}) — {s.risk} risk, {s.return_pct > 0 ? `~${s.return_pct}% p.a.` : "protection"}<br />
            <span style={{ color: "#718096" }}>{s.description}</span>
          </div>
        ))}
      </Section>

      {/* FIRE */}
      <Section title="🔥 FIRE Path Planner" open>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
          {[
            ["Savings Rate", data.fire_savings_rate.toFixed(1) + "%"],
            ["FIRE Corpus", fmt(data.fire_corpus)],
            ["Required SIP", fmt(data.fire_required_sip) + "/mo"],
            ["Years to FIRE", data.fire_years === 99 ? "∞" : data.fire_years.toFixed(1)],
            ["On Track", data.fire_on_track ? "✅ Yes" : "❌ No"],
            ["Deficit", data.fire_deficit ? "⚠️ Yes" : "✅ No"],
          ].map(([k, v]) => (
            <div key={k} style={{ background: "#f7fafc", borderRadius: 8, padding: "0.6rem 0.9rem" }}>
              <div style={{ fontSize: "0.75rem", color: "#718096" }}>{k}</div>
              <div style={{ fontWeight: 700 }}>{v}</div>
            </div>
          ))}
        </div>

        {/* Asset allocation */}
        <p style={{ fontWeight: 600, marginBottom: "0.4rem" }}>📐 Recommended Asset Allocation</p>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
          {data.fire_asset_allocation.map(a => (
            <div key={a.asset} style={{ background: "#ebf8ff", border: "1px solid #90cdf4",
              borderRadius: 6, padding: "0.4rem 0.75rem", fontSize: "0.85rem" }}>
              <strong>{a.pct}%</strong> {a.asset}
            </div>
          ))}
        </div>

        {/* Insurance gaps */}
        {data.fire_insurance_gaps.length > 0 && (
          <>
            <p style={{ fontWeight: 600, marginBottom: "0.4rem" }}>🛡️ Insurance Gaps</p>
            {data.fire_insurance_gaps.map((g, i) => (
              <div key={i} style={{ background: "#fff5f5", border: "1px solid #fc8181",
                borderRadius: 6, padding: "0.5rem 0.75rem", marginBottom: "0.4rem", fontSize: "0.85rem" }}>
                ⚠️ {g}
              </div>
            ))}
          </>
        )}

        {/* Monthly roadmap (first 12 months) */}
        <p style={{ fontWeight: 600, margin: "0.75rem 0 0.4rem" }}>📅 Month-by-Month Roadmap (first 12 months)</p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
            <thead>
              <tr style={{ background: "#edf2f7" }}>
                {["Month", "Corpus", "SIP", "Equity %"].map(h => (
                  <th key={h} style={{ padding: "0.4rem 0.6rem", textAlign: "left", fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.fire_monthly_roadmap.slice(0, 12).map(r => (
                <tr key={r.month} style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "0.35rem 0.6rem" }}>Month {r.month}</td>
                  <td style={{ padding: "0.35rem 0.6rem" }}>{fmt(r.corpus)}</td>
                  <td style={{ padding: "0.35rem 0.6rem" }}>{fmt(r.sip)}</td>
                  <td style={{ padding: "0.35rem 0.6rem" }}>{r.equity_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Yearly milestones */}
        <p style={{ fontWeight: 600, margin: "0.75rem 0 0.4rem" }}>📈 Yearly Milestones</p>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
            <thead>
              <tr style={{ background: "#edf2f7" }}>
                {["Year", "Age", "Projected Corpus"].map(h => (
                  <th key={h} style={{ padding: "0.4rem 0.6rem", textAlign: "left", fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.fire_yearly_milestones.map(m => (
                <tr key={m.year} style={{ borderBottom: "1px solid #e2e8f0" }}>
                  <td style={{ padding: "0.35rem 0.6rem" }}>Year {m.year}</td>
                  <td style={{ padding: "0.35rem 0.6rem" }}>{m.age}</td>
                  <td style={{ padding: "0.35rem 0.6rem" }}>{fmt(m.projected_corpus)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {/* Health Score */}
      <Section title="💊 Money Health Score" open>
        <div style={{ textAlign: "center", marginBottom: "1rem" }}>
          <div style={{ fontSize: "3rem", fontWeight: 800, color: data.health_score >= 70 ? "#48bb78" : data.health_score >= 40 ? "#ed8936" : "#fc8181" }}>
            {data.health_score}
          </div>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "#4a5568" }}>{data.health_label}</div>
          <div style={{ fontSize: "0.8rem", color: "#718096" }}>out of 100</div>
        </div>
        {Object.entries(data.health_dimensions).map(([k, v]) => (
          <Bar key={k} label={k} value={v} />
        ))}
        <p style={{ fontSize: "0.82rem", color: "#718096", marginTop: "0.5rem" }}>
          Weakest area: <strong>{data.health_top_factor.replace(/_/g, " ")}</strong>
        </p>
      </Section>

      {/* Recommendations */}
      <Section title="💡 Recommendations" open>
        {data.recommendations.split("\n").filter(Boolean).map((line, i) => (
          <p key={i} style={{ marginBottom: "0.5rem", lineHeight: 1.6 }}>{line}</p>
        ))}
      </Section>

      <div className="disclaimer">{data.disclaimer}</div>
    </div>
  );
}
