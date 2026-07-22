import { useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, Info, AlertTriangle } from "lucide-react";

export function AnalyzeUsername() {
  const [platform, setPlatform] = useState<"lichess" | "chesscom">("chesscom");
  const [username, setUsername] = useState("");
  const [limit, setLimit] = useState("50");
  const [rateLimitError, setRateLimitError] = useState(false);
  const navigate = useNavigate();

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) return;
    setRateLimitError(false);
    (async () => {
      try {
        const mappedPlatform = platform === "chesscom" ? "chess.com" : platform;
        const resp = await fetch(`/api/analyze-async/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, platform: mappedPlatform, limit }),
        });
        if (resp.status === 403 || resp.status === 429) {
          setRateLimitError(true);
          return;
        }
        if (!resp.ok) throw new Error(`Server responded ${resp.status}`);
        const data = await resp.json();
        const taskId = data?.task_id || data?.taskId;
        if (taskId) navigate(`/status/${taskId}`);
        else navigate(`/status/unknown`);
      } catch (err) {
        console.error(err);
        alert("Failed to start analysis. Check the backend or network.");
      }
    })();
  };

  return (
    <div className="max-w-xl mx-auto py-8">
      {/* Header */}
      <div className="mb-10">
        <h1
          className="text-4xl font-bold tracking-tight mb-2"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Username Analysis
        </h1>
        <p className="text-sm text-[#A89070]">
          Pull your recent games directly from your favorite platform.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleAnalyze} className="space-y-8">
        {/* Platform selector */}
        <div className="space-y-3">
          <label className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]">
            Platform
          </label>
          <div className="grid grid-cols-2 gap-px bg-[#3D2B1A] border border-[#3D2B1A]">
            <button
              type="button"
              onClick={() => setPlatform("chesscom")}
              className={`flex items-center justify-center gap-2 py-3.5 text-sm font-medium active:scale-[0.97] transition-all duration-150 ${
                platform === "chesscom"
                  ? "bg-[#C8A96E] text-[#1C1510]"
                  : "bg-[#251A12] text-[#A89070] hover:bg-[#2E2016]"
              }`}
            >
              <span className="text-xs font-bold">C</span>
              Chess.com
            </button>
            <button
              type="button"
              onClick={() => setPlatform("lichess")}
              className={`flex items-center justify-center gap-2 py-3.5 text-sm font-medium transition-colors ${
                platform === "lichess"
                  ? "bg-[#C8A96E] text-[#1C1510]"
                  : "bg-[#251A12] text-[#A89070] hover:bg-[#2E2016]"
              }`}
            >
              <span className="text-xs font-bold">L</span>
              Lichess
            </button>
          </div>
        </div>

        {/* Username */}
        <div className="space-y-3">
          <label
            htmlFor="username"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Username
          </label>
          <input
            id="username"
            type="text"
            placeholder="e.g. Hikaru, MagnusCarlsen"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        {/* Game limit */}
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <label
              htmlFor="limit"
              className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
            >
              Games to Analyze
            </label>
            <span
              className="text-lg font-semibold tabular-nums text-[#F0E6D3]"
              style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
            >
              {limit}
            </span>
          </div>
          <input
            type="range"
            id="limit"
            min="10"
            max="200"
            step="10"
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="w-full h-px bg-[#3D2B1A] appearance-none cursor-pointer accent-[#C8A96E]"
          />
          <div className="flex text-[10px] text-[#A89070] justify-between tracking-widest">
            <span>10</span>
            <span>200</span>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#C8A96E] text-[#1C1510] text-sm font-medium tracking-wide hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
        >
          Start Analysis
          <ArrowRight size={16} />
        </button>

        {/* Rate limit warning */}
        {rateLimitError && (
          <div className="flex gap-3 items-start border border-[#B85C4A]/30 bg-[#B85C4A]/5 p-4">
            <AlertTriangle size={14} className="text-[#B85C4A] mt-0.5 shrink-0" />
            <p className="text-xs text-[#B85C4A] leading-relaxed">
              You've been rate-limited. Please wait a minute before trying again.
            </p>
          </div>
        )}

        {/* Note */}
        <div className="flex gap-3 items-start border border-[#3D2B1A] bg-[#2E2016] p-4">
          <Info size={14} className="text-[#A89070] mt-0.5 shrink-0" />
          <p className="text-xs text-[#A89070] leading-relaxed">
            Depending on the number of games, full analysis with Stockfish 16.1 may take a few
            minutes.
          </p>
        </div>
      </form>
    </div>
  );
}
