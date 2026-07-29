import { Link, Navigate, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import Pipeline from "./pages/Pipeline";
import Audit from "./pages/Audit";
import Metrics from "./pages/Metrics";
import Scenarios from "./pages/Scenarios";

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-ink/10 bg-white/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="font-display text-lg font-semibold tracking-tight text-ink">
            Agentic SDLC
          </Link>
          <nav className="flex gap-4 text-sm font-medium text-ink/70">
            <Link to="/" className="hover:text-accent">
              New run
            </Link>
            <Link to="/scenarios" className="hover:text-accent">
              Scenarios
            </Link>
            <Link to="/metrics" className="hover:text-accent">
              Metrics
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pipelines/:runId" element={<Pipeline />} />
          <Route path="/audit/:runId" element={<Audit />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
