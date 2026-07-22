import { useEffect, useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, Clock, Trash2, ExternalLink, Loader2 } from "lucide-react";
import { getCsrfToken } from "../lib/csrf";

interface SavedAnalysis {
  id: number;
  task_id: string;
  subject: string;
  platform: string;
  total_games: number;
  created_at: string;
}

export function History() {
  const [analyses, setAnalyses] = useState<SavedAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/saved-analyses/", { credentials: "same-origin" });
        if (res.status === 401) {
          if (!cancelled) {
            setError("auth");
            setLoading(false);
          }
          return;
        }
        if (!res.ok) throw new Error("Failed to load analyses");
        const data = await res.json();
        if (!cancelled) setAnalyses(data.analyses ?? []);
      } catch (err: any) {
        if (!cancelled) setError(err.message || "Failed to load analyses");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await fetch(`/api/saved-analyses/${id}/`, {
        method: "DELETE",
        credentials: "same-origin",
        headers: { "X-CSRFToken": getCsrfToken() },
      });
      setAnalyses((prev) => prev.filter((a) => a.id !== id));
    } catch {
      // ignore
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <Link
        to="/"
        className="inline-flex items-center text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] mb-8 transition-colors"
      >
        <ArrowLeft size={14} className="mr-1.5" /> Back
      </Link>

      <div className="mb-10">
        <h1
          className="text-4xl font-bold tracking-tight mb-2"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Analysis History
        </h1>
        <p className="text-sm text-[#A89070]">
          Your saved chess analyses. Click any report to view the full breakdown.
        </p>
      </div>

      {/* Auth required state */}
      {error === "auth" && (
        <div className="border border-[#3D2B1A] bg-[#2E2016] p-8 text-center">
          <p className="text-sm text-[#A89070] mb-4">
            Sign in to view your analysis history.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center px-5 py-2.5 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
          >
            Sign In
          </Link>
        </div>
      )}

      {/* Loading state */}
      {loading && error !== "auth" && (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={20} className="animate-spin text-[#A89070]" />
        </div>
      )}

      {/* Error state */}
      {error && error !== "auth" && (
        <div className="border border-[#B85C4A]/30 bg-[#B85C4A]/5 p-6 text-center">
          <p className="text-sm text-[#B85C4A]">{error}</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && analyses.length === 0 && (
        <div className="border border-[#3D2B1A] bg-[#2E2016] p-8 text-center">
          <p className="text-sm text-[#A89070] mb-2">No saved analyses yet.</p>
          <p className="text-xs text-[#A89070] mb-4">
            Run an analysis and click "Save" to add it to your history.
          </p>
          <Link
            to="/analyze/username"
            className="inline-flex items-center px-5 py-2.5 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
          >
            Start Analyzing
          </Link>
        </div>
      )}

      {/* Analyses list */}
      {analyses.length > 0 && (
        <div className="space-y-3">
          {analyses.map((a) => (
            <div
              key={a.id}
              className="border border-[#3D2B1A] bg-[#251A12] p-5 flex items-center justify-between gap-4 hover:bg-[#2E2016] transition-colors"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-[#F0E6D3] truncate">{a.subject}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-[#A89070]">
                  <span className="capitalize">{a.platform}</span>
                  <span>&middot;</span>
                  <span>{a.total_games} games</span>
                  <span>&middot;</span>
                  <span className="flex items-center gap-1">
                    <Clock size={11} />
                    {new Date(a.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/results/${a.task_id}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#3D2B1A] text-xs font-medium text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
                >
                  <ExternalLink size={12} />
                  View
                </Link>
                <button
                  onClick={() => handleDelete(a.id)}
                  className="p-1.5 text-[#A89070] hover:text-[#B85C4A] transition-colors"
                  title="Remove from history"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
