import { useState } from "react";
import InputForm from "./components/InputForm";
import Results from "./components/Results";
import type { FormData, AnalyseResponse } from "./types";

export default function App() {
  const [result, setResult] = useState<AnalyseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
        throw new Error(detail?.detail || `Server error ${res.status}`);
      }
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>💰 AI Money Mentor</h1>
        <p>Personalised financial guidance for Indian salaried individuals</p>
      </header>

      <InputForm onSubmit={handleSubmit} loading={loading} />

      {loading && <div className="spinner" />}

      {error && <div className="error-box" style={{ marginTop: "1rem" }}>{error}</div>}

      {result && !loading && <Results data={result} />}
    </div>
  );
}
