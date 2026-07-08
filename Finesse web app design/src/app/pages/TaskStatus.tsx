import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { CheckCircle2, AlertTriangle, Gamepad2, Bell } from "lucide-react";

interface TaskProgress {
  phase: string;
  current: number;
  total: number;
  message: string;
}

/**
 * Compute a deterministic percentage from the pipeline progress metadata.
 *
 * Phase weights reflect where time is actually spent:
 *   fetching      0 –  5%
 *   Stockfish     5 – 82%  (game-by-game)
 *   metrics      82 – 92% (pieces/blunders/skills/phases)
 *   stats        92 – 100% (profile/openings/time)
 */
function progressPercent(p: TaskProgress | null): number {
  if (!p) return 5; // initial pending state
  const { phase, current, total } = p;
  if (total === 0) return 5;

  const ratio = current / total; // 0..1 within phase

  switch (phase) {
    case "fetching":
      return 2 + ratio * 3;           // 2–5%
    case "analyzing":
      return 5 + ratio * 77;          // 5–82%
    case "metrics":
      return 82 + ratio * 10;         // 82–92%
    case "stats":
      return 92 + ratio * 8;          // 92–100%
    default:
      return 5 + ratio * 85;          // generic fallback
  }
}

const PHASE_LABELS: Record<string, string> = {
  pending: "Queued",
  fetching: "Fetching games",
  analyzing: "Stockfish analysis",
  metrics: "Computing metrics",
  stats: "Building report",
};

/**
 * Request browser notification permission on mount (non-blocking).
 * Returns the current permission state.
 */
function useNotificationPermission(): NotificationPermission {
  const [permission, setPermission] = useState<NotificationPermission>(
    () => (typeof Notification !== "undefined" ? Notification.permission : "denied")
  );

  useEffect(() => {
    if (typeof Notification === "undefined") return;
    if (Notification.permission === "default") {
      Notification.requestPermission().then(setPermission);
    } else {
      setPermission(Notification.permission);
    }
  }, []);

  return permission;
}

/**
 * Fire a browser notification and return true if it was shown.
 */
function fireNotification(title: string, body: string, url: string): boolean {
  if (typeof Notification === "undefined" || Notification.permission !== "granted") {
    return false;
  }
  try {
    const n = new Notification(title, {
      body,
      icon: "/favicon.ico",
      tag: "chess-analysis-done",
    });
    n.onclick = () => {
      window.focus();
      window.location.href = url;
    };
    return true;
  } catch {
    return false;
  }
}

/** Animated warm dots spinner */
function WarmDots() {
  return (
    <div className="flex items-center gap-1.5 mb-5">
      <span className="w-2 h-2 rounded-full bg-[#C8A96E] warm-dot-1" />
      <span className="w-2 h-2 rounded-full bg-[#C8A96E] warm-dot-2" />
      <span className="w-2 h-2 rounded-full bg-[#C8A96E] warm-dot-3" />
    </div>
  );
}

export function TaskStatus() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [progressData, setProgressData] = useState<TaskProgress | null>(null);
  const [taskStatus, setTaskStatus] = useState<"pending" | "processing" | "done" | "failed">("pending");
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [showBanner, setShowBanner] = useState(false);
  const notifiedRef = useRef(false);

  const permission = useNotificationPermission();
  const percent = useMemo(() => progressPercent(progressData), [progressData]);
  const resultsUrl = `/results/${taskId}`;

  useEffect(() => {
    let cancelled = false;
    const pollTask = async () => {
      try {
        const res = await fetch(`/api/task/${taskId}/`);
        if (!res.ok) {
          throw new Error(`Task status request failed (${res.status})`);
        }

        const data = await res.json();
        if (cancelled) return;

        if (data.status === "done") {
          setTaskStatus("done");
          setProgressData({ phase: "done", current: 1, total: 1, message: "Redirecting..." });

          // Fire browser notification (only once)
          if (!notifiedRef.current) {
            notifiedRef.current = true;
            const shown = fireNotification(
              "Analysis Complete",
              "Your chess analysis is ready. Click to view the full report.",
              resultsUrl,
            );
            // Show in-page banner if notification was blocked or unsupported
            if (!shown) setShowBanner(true);
          }

          setTimeout(() => {
            if (!cancelled) navigate(resultsUrl);
          }, 800);
          return;
        }

        if (data.status === "failed") {
          setTaskStatus("failed");
          setError(data.error || data.details || "Analysis failed.");
          return;
        }

        setTaskStatus(data.status || "processing");
        setProgressData({
          phase: data.phase || "analyzing",
          current: data.current || 0,
          total: data.total || 0,
          message: data.message || "Analyzing...",
        });
      } catch (err: any) {
        if (cancelled) return;
        setError(err.message);
      }
    };

    pollTask();
    const interval = setInterval(pollTask, 2500);
    const timer = setInterval(() => {
      if (!cancelled) setElapsed((s) => s + 1);
    }, 1000);
    return () => {
      cancelled = true;
      clearInterval(interval);
      clearInterval(timer);
    };
  }, [taskId, navigate, resultsUrl]);

  const isActive = taskStatus !== "done" && taskStatus !== "failed";
  const gameProgress = progressData?.phase === "analyzing" && progressData.total > 0
    ? `${progressData.current} / ${progressData.total} games`
    : null;

  // Remember the total game count once we learn it, so it persists through
  // the metrics/stats phases (where progressData.total is step counts, not game counts).
  const totalGamesRef = useRef(0);
  if (progressData?.phase === "analyzing" && progressData.total > 0) {
    totalGamesRef.current = progressData.total;
  }
  const totalGames = totalGamesRef.current;

  const phaseLabel = PHASE_LABELS[progressData?.phase ?? taskStatus] || progressData?.phase;

  return (
    <div className="max-w-md mx-auto py-24 flex flex-col items-center justify-center">
      <div className="w-full border border-[#3D2B1A] bg-[#251A12] py-12 px-6">
        <div className="flex flex-col items-center p-0">

          {!error ? (
            <>
              {isActive ? (
                <WarmDots />
              ) : (
                <CheckCircle2 className="h-14 w-14 text-[#7A9E5F] mb-5" />
              )}

              <h2
                className="text-2xl font-bold text-[#F0E6D3] mb-3"
                style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
              >
                {isActive ? "Analyzing Your Games" : "Analysis Complete"}
              </h2>

              {isActive && (
                <p className="text-sm text-[#A89070] mb-1 leading-relaxed max-w-xs text-center">
                  Each move is being evaluated for accuracy, blunders,
                  and opening patterns by Stockfish 16.1.
                </p>
              )}

              {/* Game counter + total games display */}
              {isActive && (
                <div className="flex flex-col items-center mt-3 mb-1">
                  {gameProgress ? (
                    <p className="text-sm font-bold text-[#F0E6D3] tabular-nums">
                      {gameProgress}
                    </p>
                  ) : progressData?.total === 0 && progressData?.phase === "fetching" ? (
                    <p className="text-sm font-bold text-[#F0E6D3]">
                      Fetching games...
                    </p>
                  ) : totalGames > 0 ? (
                    <p className="text-sm font-bold text-[#F0E6D3] tabular-nums">
                      {totalGames} games to analyze
                    </p>
                  ) : null}
                </div>
              )}

              {/* Phase label */}
              {isActive && phaseLabel && (
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#A89070] font-mono mb-4">
                  {phaseLabel}
                </p>
              )}

              {isActive && (
                <div className="flex items-center gap-3 my-2 px-4 py-3 border border-[#3D2B1A] bg-[#2E2016]">
                  <Gamepad2 size={14} className="text-[#A89070] shrink-0" />
                  <div className="text-xs text-[#A89070] leading-relaxed">
                    <span className="font-medium text-[#F0E6D3]">Analysis can take 10–30 minutes</span> depending on how many games you submitted.
                    {" "}Go play a couple of quick games — we'll have your full report ready when you get back.
                  </div>
                </div>
              )}

              {isActive && (
                <div className="w-full bg-[#2E2016] h-1.5 overflow-hidden my-4">
                  <div
                    className="bg-[#C8A96E] h-full transition-all duration-700 ease-out"
                    style={{ width: `${Math.min(percent, 95)}%` }}
                  />
                </div>
              )}

              {isActive && elapsed > 0 && (
                <p className="text-[10px] uppercase tracking-[0.15em] text-[#A89070] font-mono">
                  Elapsed: {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, "0")}
                </p>
              )}

              {/* In-page banner when browser notifications are blocked */}
              {!isActive && showBanner && (
                <div className="w-full mt-4 border border-[#C8A96E]/30 bg-[#C8A96E]/5 p-4 flex items-start gap-3">
                  <Bell size={16} className="text-[#C8A96E] shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[#F0E6D3]">Analysis is ready!</p>
                    <p className="text-xs text-[#A89070] mt-0.5">
                      Browser notifications are blocked. Click below to view your report.
                    </p>
                  </div>
                  <Link
                    to={resultsUrl}
                    className="shrink-0 inline-flex items-center px-3 py-1.5 bg-[#C8A96E] text-[#1C1510] text-[10px] uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
                  >
                    View Report
                  </Link>
                </div>
              )}

              {!isActive && !showBanner && (
                <p className="text-sm text-[#A89070]">Redirecting to your results...</p>
              )}
            </>
          ) : (
            <>
              <div className="text-[#B85C4A] mb-5">
                <AlertTriangle className="h-14 w-14" />
              </div>
              <h2
                className="text-2xl font-bold text-[#F0E6D3] mb-3"
                style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
              >
                Analysis Failed
              </h2>
              <p className="text-sm text-[#A89070] mb-6 leading-relaxed max-w-xs text-center">
                {error}
              </p>
              <a
                href="/"
                className="inline-flex items-center justify-center px-6 py-2.5 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
              >
                Start Over
              </a>
            </>
          )}

          <div className="mt-4 text-sm text-[#A89070] font-mono">
            Task ID: {taskId}
          </div>

        </div>
      </div>
    </div>
  );
}
