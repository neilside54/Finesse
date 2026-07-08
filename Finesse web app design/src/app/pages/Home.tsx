import { Link } from "react-router";
import { Search, Upload, Target, Clock, BarChart3, Users } from "lucide-react";

export function Home() {
  return (
    <div className="flex flex-col items-center py-8">
      {/* Hero Section */}
      <section className="text-center space-y-8 max-w-2xl mb-16 relative">
        {/* Radial gradient background — warmer/lighter toward center */}
        <div
          className="absolute inset-0 -z-10 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse at center, rgba(200,169,110,0.08) 0%, transparent 70%)",
          }}
        />

        <div className="inline-flex items-center gap-2 px-3 py-1 border border-border text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#C8A96E]"></span>
          Stockfish 16.1 Integration
        </div>

        <h1
          className="text-5xl md:text-6xl font-bold tracking-tight leading-[1.1]"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Master Your Chess
          <br />
          <span className="text-[#C8A96E]">One Move at a Time</span>
        </h1>

        <p className="text-base text-[#A89070] leading-relaxed max-w-xl mx-auto">
          Deep, actionable insights into your chess games. Connect your Lichess or Chess.com
          account, or upload PGNs to uncover blunders, opening trends, and peer comparisons.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            to="/analyze/username"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 bg-[#C8A96E] text-[#1C1510] text-sm font-medium tracking-wide hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
          >
            <Search size={16} />
            Analyze Username
          </Link>
          <Link
            to="/analyze/pgn"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3 border border-border text-sm font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
          >
            <Upload size={16} />
            Upload PGN
          </Link>
        </div>

        {/* Social proof line */}
        <p className="text-[11px] text-[#A89070] tracking-wide pt-2">
          Powered by Stockfish 16.1 · Supports Chess.com &amp; Lichess · Free forever
        </p>

        {/* Browser-frame metric mockup */}
        <div className="mx-auto max-w-md mt-8">
          <div className="border border-[#3D2B1A] bg-[#251A12] overflow-hidden">
            {/* Fake browser bar */}
            <div className="flex items-center gap-2 px-3 py-2 border-b border-[#3D2B1A] bg-[#1C1510]">
              <div className="w-2 h-2 rounded-full bg-[#B85C4A]/60"></div>
              <div className="w-2 h-2 rounded-full bg-[#C8A96E]/60"></div>
              <div className="w-2 h-2 rounded-full bg-[#7A9E5F]/60"></div>
              <span className="text-[10px] text-[#A89070] ml-2 font-mono">finesse — analysis report</span>
            </div>
            {/* Mockup content: 3 metric bars */}
            <div className="px-6 py-5 space-y-5">
              <MockMetricBar label="Accuracy" value={78} />
              <MockMetricBar label="Resourcefulness" value={65} />
              <MockMetricBar label="Conversion" value={52} />
            </div>
          </div>
        </div>
      </section>

      {/* Divider */}
      <div className="w-full max-w-4xl border-t border-[#3D2B1A] mb-16"></div>

      {/* Feature Grid */}
      <section className="w-full max-w-4xl">
        <div className="text-center mb-12">
          <h2
            className="text-2xl font-bold"
            style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          >
            Comprehensive Analysis
          </h2>
          <p className="text-xs uppercase tracking-[0.15em] text-[#A89070] mt-2">
            Everything you need to improve your rating
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-px bg-[#3D2B1A] border border-[#3D2B1A]">
          <FeatureCard
            icon={<Target className="text-[#C8A96E]" size={18} />}
            title="Blunder Detection"
            description="Pinpoint critical mistakes and missed tactical opportunities with Stockfish."
          />
          <FeatureCard
            icon={<BarChart3 className="text-[#C8A96E]" size={18} />}
            title="Opening Trends"
            description="Discover which openings score best for you and where you are vulnerable."
          />
          <FeatureCard
            icon={<Users className="text-[#C8A96E]" size={18} />}
            title="Peer Comparison"
            description="See how your accuracy and time management compare to players at your level."
          />
          <FeatureCard
            icon={<Clock className="text-[#C8A96E]" size={18} />}
            title="Time Management"
            description="Analyze how you spend your clock in critical positions vs routine moves."
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-[#251A12] p-6 space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="text-sm font-semibold uppercase tracking-[0.1em]">{title}</h3>
      </div>
      <p className="text-sm text-[#A89070] leading-relaxed">{description}</p>
    </div>
  );
}

/** A small mock metric bar for the browser-frame preview */
function MockMetricBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium text-[#F0E6D3]">{label}</span>
        <span className="text-xs font-semibold tabular-nums text-[#F0E6D3]">
          {value}%
        </span>
      </div>
      <div className="h-1.5 w-full bg-[#2E2016]">
        <div
          className="h-full bg-[#C8A96E]"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
