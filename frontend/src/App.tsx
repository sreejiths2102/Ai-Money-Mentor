import { useState } from "react";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import type { FormData, AnalyseResponse } from "./types";
import { LayoutDashboard, LineChart, FileText, Settings, HelpCircle, LogOut, Bell, History, Database, Activity, AlertTriangle, Briefcase, FileSearch } from "lucide-react";

export default function App() {
  const [result, setResult] = useState<AnalyseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Navigation State
  const [activeView, setActiveView] = useState("overview"); // overview, analytics, reports, settings, portfolio, markets, research

  const handleSubmit = async (data: FormData) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/analyse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        let msg = `Server error ${res.status}`;
        if (detail?.detail) {
           msg = typeof detail.detail === 'string' ? detail.detail : JSON.stringify(detail.detail);
        }
        throw new Error(msg);
      }
      setResult(await res.json());
      setActiveView("overview"); // Force back to overview to see results if generated from another tab (unlikely but safe)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const handleSupport = (e: React.MouseEvent) => {
    e.preventDefault();
    alert("Sovereign Support Node offline. Please contact your system administrator.");
  };

  const handleSignOut = (e: React.MouseEvent) => {
    e.preventDefault();
    if(window.confirm("Terminate secure session? All unsaved trajectory data will be cleared.")) {
      window.location.reload();
    }
  };

  // Render dummy views for tabs without real data
  const PlaceholderView = ({ title, icon: Icon, desc }: { title: string, icon: any, desc: string }) => (
    <div className="card" style={{ padding: "4rem", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
      <Icon size={48} color="var(--border-strong)" />
      <h3 style={{ fontSize: "1.5rem" }}>{title} Subsystem Offline</h3>
      <p style={{ color: "var(--text-secondary)", maxWidth: "400px" }}>{desc}</p>
      <div className="badge-tag" style={{ marginTop: "1rem" }}>RESTRICTED CLEARANCE</div>
    </div>
  );

  const renderContent = () => {
    switch (activeView) {
      case "analytics":
        return <PlaceholderView title="Deep Analytics" icon={LineChart} desc="Historical multi-asset risk regression engines are currently indexing. Try again post-sync." />;
      case "reports":
        return <PlaceholderView title="Secure Reports" icon={FileText} desc="PDF trajectory generation and compliance dossiers are locked." />;
      case "settings":
        return <PlaceholderView title="Terminal Configuration" icon={Settings} desc="User preferences, thematic overrides, and API routing configs." />;
      case "portfolio":
        return <PlaceholderView title="Live Portfolio" icon={Briefcase} desc="No broker integrations detected. Bind API keys to visualize live holdings." />;
      case "markets":
        return <PlaceholderView title="Global Markets" icon={Activity} desc="Live ticker feed and macroscopic geopolitical data currently out of bounds." />;
      case "research":
        return <PlaceholderView title="Tactical Research" icon={FileSearch} desc="Sovereign analysts' intelligence reports are securely encrypted." />;
      case "overview":
      default:
        return (
          <div className="content-grid">
            {/* Left: Input Engine */}
            <div>
              <div className="section-title">
                <span>
                  <Database size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                  INPUT ENGINE
                </span>
              </div>
              <InputForm onSubmit={handleSubmit} loading={loading} />
            </div>

            {/* Right: Strategic Blueprint */}
            <div>
              <div className="section-title">
                <span>
                  <Activity size={14} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                  STRATEGIC BLUEPRINT
                </span>
                {result && <span className="badge-tag">✨ TACTILE INTELLIGENCE ENHANCED</span>}
              </div>
              
              {loading && (
                <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', color: 'var(--accent-gold)' }}>
                  <div className="spinner"></div> Generating tactile analysis...
                </div>
              )}
              
              {error && (
                <div className="card" style={{ borderColor: 'var(--status-error)' }}>
                  <h3 style={{ color: 'var(--status-error)', fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Analytics Error</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{error}</p>
                </div>
              )}

              {result && !loading && <Results data={result} />}
              
              {/* If no result and not loading, show a neat placeholder */}
              {!result && !loading && !error && (
                <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "4rem 2rem", textAlign: "center", opacity: 0.8 }}>
                   <Database size={48} color="var(--border-strong)" style={{ marginBottom: "1rem" }} />
                   <h3 style={{ color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Awaiting Input Parameters</h3>
                   <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", maxWidth: "250px" }}>Configure the engine via the left panel and initialize generation to synthesize the strategic blueprint.</p>
                </div>
              )}
            </div>
          </div>
        );
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12h4l3-9 5 18 3-9h5"/></svg>
          </div>
          <div className="brand-text">
            <h1>Sovereign Platform</h1>
            <span>Professional Intelligence</span>
          </div>
        </div>

        <nav className="nav-links">
          <a href="#" className={`nav-item ${activeView === "overview" ? "active" : ""}`} onClick={(e) => { e.preventDefault(); setActiveView("overview") }}>
            <LayoutDashboard size={18} /> Overview
          </a>
          <a href="#" className={`nav-item ${activeView === "analytics" ? "active" : ""}`} onClick={(e) => { e.preventDefault(); setActiveView("analytics") }}>
            <LineChart size={18} /> Analytics
          </a>
          <a href="#" className={`nav-item ${activeView === "reports" ? "active" : ""}`} onClick={(e) => { e.preventDefault(); setActiveView("reports") }}>
            <FileText size={18} /> Reports
          </a>
          <a href="#" className={`nav-item ${activeView === "settings" ? "active" : ""}`} onClick={(e) => { e.preventDefault(); setActiveView("settings") }}>
            <Settings size={18} /> Settings
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="bottom-nav">
            <a href="#" onClick={handleSupport}><HelpCircle size={16} /> Support</a>
            <a href="#" onClick={handleSignOut}><LogOut size={16} /> Sign Out</a>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="main-area">
        {/* Top Nav */}
        <div className="top-nav">
          <div className="top-links">
            <a href="#" className={activeView === "portfolio" ? "active" : ""} 
               style={activeView === "portfolio" ? { color: 'var(--text-primary)', borderBottom: '2px solid var(--accent-gold)' } : {}}
               onClick={(e) => { e.preventDefault(); setActiveView("portfolio") }}>Portfolio</a>
            <a href="#" className={activeView === "markets" ? "active" : ""} 
               style={activeView === "markets" ? { color: 'var(--text-primary)', borderBottom: '2px solid var(--accent-gold)' } : {}}
               onClick={(e) => { e.preventDefault(); setActiveView("markets") }}>Markets</a>
            <a href="#" className={activeView === "research" ? "active" : ""} 
               style={activeView === "research" ? { color: 'var(--text-primary)', borderBottom: '2px solid var(--accent-gold)' } : {}}
               onClick={(e) => { e.preventDefault(); setActiveView("research") }}>Research</a>
          </div>
          <div className="top-icons">
            <Bell size={18} style={{ cursor: 'pointer' }} onClick={(e) => alert('No active notifications.')} />
            <History size={18} style={{ cursor: 'pointer' }} onClick={(e) => alert('Audit log is deeply encrypted.')} />
            <div className="profile-pic" style={{ cursor: 'pointer' }} onClick={() => setActiveView('settings')}></div>
          </div>
        </div>

        {/* Header */}
        <div className="content-header">
          <div className="title-section">
            <div className="status-badge">
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-gold)', display: 'inline-block' }}></span>
              SOVEREIGN ACTIVE
            </div>
            <h2 style={{ textTransform: 'capitalize' }}>
               {activeView === "overview" ? "Trajectory Planning" : activeView + " Operations"}
            </h2>
            <p>Tactile intelligence for sovereign institutional analysis.</p>
          </div>
          <div className="status-grid">
            <div className="status-item">
              <span>Market Status</span>
              <strong>STABLE <span className="green">+0.42%</span></strong>
            </div>
            <div className="status-item">
              <span>Last Sync</span>
              <strong>14:02:11</strong>
            </div>
          </div>
        </div>

        {/* Dynamic Content View */}
        {renderContent()}
        
      </main>
    </div>
  );
}
