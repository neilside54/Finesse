import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router";
import {
  ArrowLeft, ChevronDown, ChevronUp, Crosshair, BookOpen, Clock,
  Layers, Crown, BarChart3, BookmarkPlus, Check, Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, Badge } from "../components/ui";
import { ScoreRing } from "../components/ScoreRing";
import { MetricBar } from "../components/MetricBar";
import { useAuth } from "../hooks/useAuth";
import { getCsrfToken } from "../lib/csrf";

// --- Task polling -----------------------------------------------------------

export function useTaskResult(taskId?: string, interval = 3000) {
  const [status, setStatus] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;

    const fetchOnce = async () => {
      try {
        const res = await fetch(`/api/task/${taskId}/`);
        if (!res.ok) throw new Error("Fetch failed");
        const data = await res.json();
        if (cancelled) return;
        setStatus(data.status);
        if (data.status === "done") {
          setResult(data.result);
        } else if (data.status === "failed") {
          setResult({ error: data.error || data.details || "Task failed" });
        }
      } catch (err) {
        console.error(err);
      }
    };

    fetchOnce();
    timer = setInterval(fetchOnce, interval);

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [taskId, interval]);

  return { status, result } as const;
}

// --- Section registry -------------------------------------------------------

const SECTIONS = [
  { id: "skills", title: "Skills", icon: Crosshair, description: "Accuracy, resourcefulness, and conversion — how well you play and recover." },
  { id: "openings", title: "Openings", icon: BookOpen, description: "Your opening repertoire, trends, and lines needing study." },
  { id: "time_management", title: "Time Management", icon: Clock, description: "Clock discipline and time trouble patterns." },
  { id: "game_phases", title: "Game Phases", icon: Layers, description: "Performance across opening, middlegame, and endgame." },
  { id: "pieces", title: "Piece Accuracy", icon: Crown, description: "How accurately you handle each piece type." },
  { id: "general_stats", title: "Statistics", icon: BarChart3, description: "Win rate, game volume, and per-mode breakdowns." },
] as const;

const SECTION_TELEMETRY_KEY: Record<string, string> = {
  skills: "skills_telemetry",
  time_management: "time_report",
  game_phases: "phase_telemetry",
  pieces: "piece_telemetry",
  openings: "opening_stats",
  general_stats: "general_stats",
};

const PIECE_NAMES: Record<string, string> = {
  P: "Pawns", N: "Knights", B: "Bishops", R: "Rooks", Q: "Queen", K: "King",
};
const PIECE_SYMBOLS: Record<string, string> = {
  P: "\u2659", N: "\u2658", B: "\u2657", R: "\u2656", Q: "\u2655", K: "\u2654",
};

// --- Main Results component -------------------------------------------------

export function Results() {
  const { taskId } = useParams();
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [showJson, setShowJson] = useState(false);
  const { status: taskStatus, result: taskResult } = useTaskResult(taskId);
  const { isAuthenticated } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const isLoading = taskStatus !== "done" || !taskResult;
  const hasError = taskStatus === "failed" || (taskResult && taskResult.error && taskStatus !== "done");

  const sections: any[] = taskResult?.sections ?? [];
  const availableSectionIds = useMemo(() => new Set(sections.map((s) => s.id)), [sections]);

  const visibleSections = SECTIONS.filter((s) => availableSectionIds.has(s.id));

  const handleSave = async () => {
    if (!taskId || !taskResult) return;
    setSaving(true);
    try {
      const res = await fetch("/api/saved-analyses/save/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ task_id: taskId, report: taskResult }),
      });
      if (res.ok) setSaved(true);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pb-16">
      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] mb-8 transition-colors"
      >
        <ArrowLeft size={14} className="mr-1.5" /> Back
      </Link>

      {/* Save analysis banner (guest) or save button (authenticated) */}
      {!isLoading && !hasError && (
        <div className="mb-8 border border-[#3D2B1A] bg-[#2E2016] p-5 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[#F0E6D3]">
              {isAuthenticated
                ? "Save this analysis to your library"
                : "Sign in to save this analysis and track your progress over time"}
            </p>
            <p className="text-xs text-[#A89070] mt-1">
              {isAuthenticated
                ? "Access it anytime from your history."
                : "Free account — takes 10 seconds."}
            </p>
          </div>
          {isAuthenticated ? (
            <button
              onClick={handleSave}
              disabled={saving || saved}
              className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 size={13} className="animate-spin" />
              ) : saved ? (
                <Check size={13} />
              ) : (
                <BookmarkPlus size={13} />
              )}
              {saved ? "Saved" : "Save"}
            </button>
          ) : (
            <Link
              to="/login"
              className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
            >
              <BookmarkPlus size={13} />
              Sign In to Save
            </Link>
          )}
        </div>
      )}

      {/* Report header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-2">
          <h1
            className="text-4xl font-bold tracking-tight"
            style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          >
            Analysis Report
          </h1>
          <Badge variant={taskStatus === "done" ? "success" : taskStatus === "failed" ? "danger" : "outline"}>
            {taskStatus === "done" ? "Complete" : taskStatus === "failed" ? "Failed" : "Running"}
          </Badge>
        </div>
        {taskResult?.user_info?.username && (
          <p className="text-sm text-[#A89070]">
            {taskResult.user_info.username} &middot; {taskResult.user_info.platform} &middot;{" "}
            {taskResult?.snapshot?.total_games ?? "N/A"} games analyzed
          </p>
        )}
      </div>

      {/* Loading state */}
      {isLoading && !hasError && (
        <Card>
          <CardContent>
            <p className="text-[#A89070] text-sm">
              The analysis is still running. This page will update automatically.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Error state */}
      {hasError && (
        <Card className="border-[#B85C4A]/30">
          <CardContent>
            <p className="text-[#B85C4A] text-sm">
              {taskResult?.error || "Analysis failed. Please retry."}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Report body */}
      {!isLoading && !hasError && (
        <div className="space-y-10">
          {/* Hero: Score Rings */}
          <HeroOverview taskResult={taskResult} />

          {/* Coaching Summary */}
          <CoachingSummary taskResult={taskResult} />

          {/* Highlights */}
          <HighlightsList taskResult={taskResult} />

          {/* Sticky Pill Nav */}
          <StickyNav
            sections={visibleSections}
            activeSection={activeSection}
            onSelect={setActiveSection}
          />

          {/* Accordion Sections */}
          <div className="space-y-4">
            {visibleSections.map((section) => {
              const sectionData = sections.find((s: any) => s.id === section.id);
              const verdict = taskResult?.[SECTION_TELEMETRY_KEY[section.id]]?.verdict;
              return (
                <AccordionSection
                  key={section.id}
                  id={section.id}
                  title={section.title}
                  icon={section.icon}
                  description={section.description}
                  isOpen={activeSection === section.id}
                  onToggle={() => setActiveSection(activeSection === section.id ? null : section.id)}
                >
                  {section.id === "openings" ? (
                    <OpeningsSection section={sectionData} />
                  ) : section.id === "general_stats" ? (
                    <GeneralStatsSection section={sectionData} />
                  ) : section.id === "pieces" ? (
                    <PiecesSection section={sectionData} />
                  ) : (
                    <MetricsSection section={sectionData} sectionId={section.id} />
                  )}
                  {verdict && verdict.length > 0 && (
                    <VerdictBox lines={verdict} />
                  )}
                </AccordionSection>
              );
            })}
          </div>

          {/* Warnings */}
          <WarningsList taskResult={taskResult} />

          {/* Raw JSON */}
          <div className="border border-[#3D2B1A]">
            <button
              onClick={() => setShowJson(!showJson)}
              className="w-full px-5 py-3 flex items-center justify-between hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
            >
              <span className="text-xs uppercase tracking-[0.15em] font-medium text-[#A89070]">
                Raw Data
              </span>
              {showJson ? <ChevronUp size={14} className="text-[#A89070]" /> : <ChevronDown size={14} className="text-[#A89070]" />}
            </button>
            {showJson && (
              <div className="px-5 pb-5 pt-2 border-t border-[#3D2B1A]">
                <pre className="text-[11px] font-mono bg-[#1C1510] text-[#F0E6D3] p-4 overflow-x-auto leading-relaxed">
                  {JSON.stringify({ taskId, status: taskStatus, result: taskResult }, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// --- Hero: Score Rings ------------------------------------------------------

function HeroOverview({ taskResult }: { taskResult: any }) {
  const snapshot = taskResult?.snapshot ?? {};
  return (
    <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-8 py-8 border border-[#3D2B1A] bg-[#251A12]">
      <ScoreRing label="Accuracy" value={snapshot.accuracy ?? 0} peerValue={snapshot.peer_accuracy} />
      <ScoreRing label="Win Rate" value={snapshot.win_rate ?? 0} />
      <ScoreRing label="Resourcefulness" value={snapshot.resourcefulness ?? 0} />
      <ScoreRing label="Conversion" value={snapshot.conversion ?? 0} />
      <ScoreRing
        label="Panic Rate"
        value={snapshot.panic_rate ?? 0}
        color={snapshot.panic_rate > 20 ? "#B85C4A" : "#C8A96E"}
      />
      <div className="flex flex-col items-center justify-center gap-1">
        <span
          className="text-3xl font-bold tracking-tight text-[#F0E6D3]"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          {snapshot.total_games ?? "\u2014"}
        </span>
        <span className="text-[10px] uppercase tracking-[0.2em] text-[#A89070] font-medium">
          Games
        </span>
      </div>
    </section>
  );
}

// --- Coaching Summary -------------------------------------------------------

function CoachingSummary({ taskResult }: { taskResult: any }) {
  const summary = taskResult?.summary ?? {};
  if (!summary.summary_text) return null;

  return (
    <Card>
      <CardContent className="py-6">
        <p
          className="text-lg leading-relaxed text-[#F0E6D3]"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          {summary.summary_text}
        </p>
        <div className="mt-4 flex items-center gap-4 text-xs text-[#A89070]">
          {summary.priority_label && (
            <span className="uppercase tracking-[0.15em] font-medium">
              Focus: {summary.priority_label}
            </span>
          )}
          {summary.peer_accuracy_source && (
            <span className="italic">
              Peer data: {summary.peer_accuracy_source === "actual" ? "measured" : "estimated"}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// --- Highlights List --------------------------------------------------------

function HighlightsList({ taskResult }: { taskResult: any }) {
  const highlights: any[] = taskResult?.highlights ?? [];
  if (highlights.length === 0) return null;

  return (
    <section>
      <h2
        className="text-lg font-semibold mb-4"
        style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
      >
        Key Findings
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {highlights.map((h, i) => (
          <div key={i} className="border border-[#3D2B1A] bg-[#251A12] p-4">
            <p className="text-sm font-medium text-[#F0E6D3]">{h.title}</p>
            {h.value !== undefined && (
              <p className="text-xs text-[#A89070] mt-1">
                Value: {h.value}
                {h.peer_average !== undefined ? ` (peers: ${h.peer_average})` : ""}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

// --- Sticky Pill Nav --------------------------------------------------------

function StickyNav({
  sections,
  activeSection,
  onSelect,
}: {
  sections: readonly { id: string; title: string; icon: any }[];
  activeSection: string | null;
  onSelect: (id: string | null) => void;
}) {
  return (
    <nav className="sticky top-14 z-10 bg-[#1C1510]/95 backdrop-blur-sm border-b border-[#3D2B1A] py-3 -mx-6 lg:-mx-8 px-6 lg:px-8">
      <div className="flex gap-1 overflow-x-auto">
        {sections.map((section) => {
          const Icon = section.icon;
          const isActive = activeSection === section.id;
          return (
            <button
              key={section.id}
              onClick={() => onSelect(isActive ? null : section.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-xs uppercase tracking-[0.12em] font-medium whitespace-nowrap active:scale-[0.97] transition-all duration-150 ${
                isActive
                  ? "bg-[#C8A96E] text-[#1C1510]"
                  : "text-[#A89070] hover:text-[#F0E6D3] hover:bg-[#2E2016]"
              }`}
            >
              <Icon size={13} />
              {section.title}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

// --- Accordion Section ------------------------------------------------------

function AccordionSection({
  id,
  title,
  icon: Icon,
  description,
  isOpen,
  onToggle,
  children,
}: {
  id: string;
  title: string;
  icon: any;
  description: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-[#3D2B1A] bg-[#251A12]">
      <button
        onClick={onToggle}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
      >
        <div className="flex items-center gap-3">
          <Icon size={16} className="text-[#A89070]" />
          <div className="text-left">
            <h3 className="text-sm font-semibold uppercase tracking-[0.1em]">{title}</h3>
            <p className="text-xs text-[#A89070] mt-0.5">{description}</p>
          </div>
        </div>
        <ChevronDown
          size={16}
          className={`text-[#A89070] transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen && (
        <div className="px-5 pb-5 pt-2 border-t border-[#3D2B1A]">
          {children}
        </div>
      )}
    </div>
  );
}

// --- Verdict Box ------------------------------------------------------------

function VerdictBox({ lines }: { lines: string[] }) {
  return (
    <div className="mt-4 border-l-2 border-[#C8A96E] pl-4 space-y-1.5">
      {lines.map((line, i) => (
        <p key={i} className="text-sm text-[#A89070] leading-relaxed">
          {line}
        </p>
      ))}
    </div>
  );
}

// --- Generic Metrics Section ------------------------------------------------

function MetricsSection({ section, sectionId }: { section: any; sectionId: string }) {
  const metrics: any[] = section?.metrics ?? [];
  return (
    <div className="space-y-5">
      {metrics.map((metric) => (
        <MetricBar
          key={metric.name}
          label={metric.name}
          value={metric.value}
          peerValue={metric.peer_average}
          peerSource={metric.peer_source}
          visual={metric.visual}
          suffix={sectionId === "game_phases" ? " pawns" : "%"}
        />
      ))}
    </div>
  );
}

// --- Pieces Section ---------------------------------------------------------

function PiecesSection({ section }: { section: any }) {
  const metrics: any[] = section?.metrics ?? [];
  return (
    <div className="space-y-5">
      {metrics.map((metric) => (
        <div key={metric.name} className="flex items-start gap-4">
          <div className="w-10 h-10 flex items-center justify-center border border-[#3D2B1A] text-xl shrink-0">
            {PIECE_SYMBOLS[metric.name] ?? "\u265F"}
          </div>
          <div className="flex-1">
            <MetricBar
              label={PIECE_NAMES[metric.name] ?? metric.name}
              value={metric.value}
              peerValue={metric.peer_average}
              peerSource={metric.peer_source}
              visual={metric.visual}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// --- General Stats Section --------------------------------------------------

function GeneralStatsSection({ section }: { section: any }) {
  const overall = section?.overall ?? {};
  const modes: Record<string, any> = section?.modes ?? {};
  const modeEntries = Object.entries(modes);

  return (
    <div className="space-y-6">
      {/* Overall summary table */}
      <div className="grid grid-cols-4 gap-4 text-center">
        {[
          { label: "Games", value: overall.total_games ?? "\u2014" },
          { label: "Wins", value: overall.wins ?? "\u2014" },
          { label: "Losses", value: overall.losses ?? "\u2014" },
          { label: "Win Rate", value: `${overall.win_rate ?? "\u2014"}%` },
        ].map((item) => (
          <div key={item.label} className="border border-[#3D2B1A] p-3">
            <p className="text-2xl font-bold tracking-tight text-[#F0E6D3]" style={{ fontFamily: "'Playfair Display', Georgia, serif" }}>
              {item.value}
            </p>
            <p className="text-[10px] uppercase tracking-[0.15em] text-[#A89070] mt-1">
              {item.label}
            </p>
          </div>
        ))}
      </div>

      {/* Per-mode breakdown */}
      {modeEntries.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs uppercase tracking-[0.15em] font-medium text-[#A89070]">
            By Time Control
          </h4>
          {modeEntries.map(([mode, data]: [string, any]) => (
            <div key={mode} className="border border-[#3D2B1A] p-4">
              <div className="flex items-baseline justify-between mb-3">
                <span className="text-sm font-semibold capitalize text-[#F0E6D3]">{mode}</span>
                <span className="text-xs text-[#A89070]">
                  {data.total_games} games &middot; {data.win_rate}% win rate
                </span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-xs text-[#A89070]">
                <div>
                  <span className="block text-[10px] uppercase tracking-widest mb-1">Your Rating</span>
                  <span className="text-sm font-semibold text-[#F0E6D3]">{data.avg_rating || "\u2014"}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase tracking-widest mb-1">Opp. Rating</span>
                  <span className="text-sm font-semibold text-[#F0E6D3]">{data.avg_peer_rating || "\u2014"}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase tracking-widest mb-1">Opp. Accuracy</span>
                  <span className="text-sm font-semibold text-[#F0E6D3]">
                    {data.avg_peer_accuracy ?? "\u2014"}%
                    {data.avg_peer_accuracy_source === "estimated" && (
                      <span className="ml-1 text-[10px] italic font-normal">(est.)</span>
                    )}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// --- Openings Section -------------------------------------------------------

function OpeningsSection({ section }: { section: any }) {
  const topWhite: any[] = section?.top_openings_white ?? [];
  const topBlack: any[] = section?.top_openings_black ?? [];
  const weak = section?.weak_openings ?? { white: [], black: [] };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <OpeningList title="White" items={topWhite} />
        <OpeningList title="Black" items={topBlack} />
      </div>

      {(weak.white?.length > 0 || weak.black?.length > 0) && (
        <div>
          <h4 className="text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] mb-3">
            Lines Needing Work
          </h4>
          <div className="space-y-2">
            {[...(weak.white ?? []), ...(weak.black ?? [])].map((item, i) => (
              <div key={i} className="border border-[#B85C4A]/30 bg-[#B85C4A]/5 p-3 flex items-baseline justify-between">
                <div>
                  <span className="text-sm font-medium text-[#F0E6D3]">{item.opening_family}</span>
                  <span className="text-xs text-[#A89070] ml-2">({item.color})</span>
                </div>
                <span className="text-xs font-semibold text-[#B85C4A]">
                  {item.win_rate}% &middot; {item.total_games} games
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OpeningList({ title, items }: { title: string; items: any[] }) {
  return (
    <div>
      <h4 className="text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] mb-3">
        {title} Repertoire
      </h4>
      {items.length > 0 ? (
        <div className="space-y-1">
          {items.map((item, i) => (
            <div key={i} className="flex items-baseline justify-between py-2 border-b border-[#3D2B1A] last:border-0">
              <div className="min-w-0">
                <p className="text-sm font-medium text-[#F0E6D3] truncate">{item.opening}</p>
                <p className="text-[10px] text-[#A89070]">
                  {item.eco} &middot; {item.total_games} games
                </p>
              </div>
              <span className="text-sm font-semibold tabular-nums ml-3 text-[#F0E6D3]">{item.win_rate}%</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-[#A89070] italic">No games recorded.</p>
      )}
    </div>
  );
}

// --- Warnings ---------------------------------------------------------------

function WarningsList({ taskResult }: { taskResult: any }) {
  const warnings: string[] = taskResult?.warnings ?? [];
  if (warnings.length === 0) return null;

  return (
    <div className="border border-[#3D2B1A] bg-[#2E2016] p-5">
      <h4 className="text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] mb-2">
        Partial Report
      </h4>
      <ul className="space-y-1">
        {warnings.map((w, i) => (
          <li key={i} className="text-xs text-[#A89070] leading-relaxed">
            {w}
          </li>
        ))}
      </ul>
    </div>
  );
}
