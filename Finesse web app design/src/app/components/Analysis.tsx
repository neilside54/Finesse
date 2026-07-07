import { useState } from 'react';
import { useParams } from 'react-router';
import { 
  TrendingUp, 
  TrendingDown, 
  Swords, 
  Brain, 
  Target, 
  AlertTriangle, 
  Code2, 
  ChevronDown, 
  ChevronUp, 
  Clock,
  ShieldAlert,
  Crown
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

const mockOpeningData = [
  { name: 'Sicilian Defense', win: 65, draw: 15, loss: 20 },
  { name: 'French Defense', win: 45, draw: 20, loss: 35 },
  { name: 'Caro-Kann', win: 55, draw: 25, loss: 20 },
  { name: 'Ruy Lopez', win: 50, draw: 30, loss: 20 },
];

const mockTimeData = [
  { name: 'Opening', time: 10 },
  { name: 'Middlegame', time: 60 },
  { name: 'Endgame', time: 30 },
];

const COLORS = ['#81B64C', '#64748b', '#ef4444']; // Win, Draw, Loss

export function Analysis() {
  const { id } = useParams();
  const [showJson, setShowJson] = useState(false);

  return (
    <div className="flex flex-col gap-8 pb-12 animate-in fade-in duration-500">
      
      {/* Header Summary */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500 mb-2">
            <span className="bg-slate-200 text-slate-700 px-2 py-0.5 rounded uppercase tracking-wider text-xs">Report {id}</span>
            <span>Analyzed via Finesse Engine v2.1</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Performance Overview</h1>
          <p className="text-slate-600 mt-1">Based on last 100 Rapid games (10|0)</p>
        </div>
        <div className="flex items-center gap-4 bg-white px-5 py-3 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex flex-col">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Global Rating</span>
            <span className="text-2xl font-black text-slate-800">1850</span>
          </div>
          <div className="w-px h-10 bg-slate-200"></div>
          <div className="flex flex-col">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Accuracy</span>
            <span className="text-2xl font-black text-[#81B64C]">84.2%</span>
          </div>
        </div>
      </header>

      {/* Snapshot Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Conversion Rate" 
          value="68%" 
          trend="+4.2%" 
          trendUp={true}
          icon={<TrendingUp className="text-blue-500 w-5 h-5" />} 
          desc="Games won when +2.0 advantage"
        />
        <MetricCard 
          title="Avg Blunders" 
          value="1.2" 
          trend="-0.3" 
          trendUp={true}
          icon={<ShieldAlert className="text-red-500 w-5 h-5" />} 
          desc="Per game (down from 1.5)"
        />
        <MetricCard 
          title="Opening Eval" 
          value="+0.4" 
          trend="+0.1" 
          trendUp={true}
          icon={<Swords className="text-amber-500 w-5 h-5" />} 
          desc="Average eval at move 15"
        />
        <MetricCard 
          title="Time Mgmt" 
          value="Solid" 
          trend="Stable" 
          trendUp={true}
          icon={<Clock className="text-purple-500 w-5 h-5" />} 
          desc="Rarely in time trouble"
        />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (Main Analysis) */}
        <div className="lg:col-span-2 flex flex-col gap-8">
          
          {/* Priority Focus */}
          <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
              <Target className="w-5 h-5 text-red-500" />
              <h2 className="text-lg font-bold text-slate-800">Priority Focus</h2>
            </div>
            <div className="p-6">
              <ul className="space-y-4">
                <li className="flex gap-4 items-start">
                  <div className="bg-red-50 p-2 rounded-lg text-red-500 shrink-0">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Endgame Blunders in Time Trouble</h3>
                    <p className="text-sm text-slate-600 mt-1">
                      In games where you have under 1 minute left, your endgame accuracy drops by 15%. Focus on practical endgame techniques and drilling basic mates.
                    </p>
                  </div>
                </li>
                <li className="flex gap-4 items-start">
                  <div className="bg-amber-50 p-2 rounded-lg text-amber-500 shrink-0">
                    <Swords className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Struggling against the French Defense</h3>
                    <p className="text-sm text-slate-600 mt-1">
                      As White, you are scoring only 40% against the French Defense. Your typical setup (Advance Variation) is losing to early c5 pawn breaks.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          {/* Opening Report */}
          <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-[#81B64C]" />
                <h2 className="text-lg font-bold text-slate-800">Opening Repertoire (As White)</h2>
              </div>
            </div>
            <div className="p-6">
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mockOpeningData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                    <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="win" name="Win %" stackId="a" fill="#81B64C" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="draw" name="Draw %" stackId="a" fill="#94a3b8" />
                    <Bar dataKey="loss" name="Loss %" stackId="a" fill="#f87171" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-6 flex justify-center gap-6 text-sm font-medium">
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-[#81B64C]"></div> Win</div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-slate-400"></div> Draw</div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-400"></div> Loss</div>
              </div>
            </div>
          </section>

        </div>

        {/* Right Column (Sidebars) */}
        <div className="lg:col-span-1 flex flex-col gap-8">
          
          {/* Peer Comparison */}
          <section className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-md text-white">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex items-center gap-2">
              <Crown className="w-5 h-5 text-amber-400" />
              <h2 className="text-lg font-bold">Peer Comparison</h2>
            </div>
            <div className="p-6">
              <p className="text-slate-400 text-sm mb-6">Compared to other 1800-1900 rated players.</p>
              
              <div className="space-y-5">
                <ComparisonBar label="Tactical Vision" value={85} peerAvg={70} />
                <ComparisonBar label="Positional Play" value={65} peerAvg={75} />
                <ComparisonBar label="Endgame Technique" value={55} peerAvg={65} />
                <ComparisonBar label="Opening Prep" value={90} peerAvg={60} />
              </div>
            </div>
          </section>

          {/* Time Management Pie */}
          <section className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-500" />
              <h2 className="text-lg font-bold text-slate-800">Time Usage</h2>
            </div>
            <div className="p-6 flex flex-col items-center">
              <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={mockTimeData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="time"
                    >
                      {mockTimeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#8b5cf6', '#f59e0b'][index % 3]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex gap-4 text-xs font-semibold text-slate-600 mt-2">
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Opening</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-purple-500"></div> Middlegame</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-amber-500"></div> Endgame</div>
              </div>
            </div>
          </section>

        </div>
      </div>

      {/* Advanced Result Area (JSON) */}
      <section className="bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden">
        <button 
          onClick={() => setShowJson(!showJson)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-100 transition-colors"
        >
          <div className="flex items-center gap-2 text-slate-700 font-bold">
            <Code2 className="w-5 h-5" />
            Advanced Data (Raw Output)
          </div>
          {showJson ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
        </button>
        
        {showJson && (
          <div className="p-6 border-t border-slate-200 bg-[#1e1e1e] text-[#d4d4d4] font-mono text-xs md:text-sm overflow-x-auto">
            <pre>
{`{
  "report_id": "${id}",
  "engine": "Stockfish 16.1",
  "depth": 22,
  "nodes_searched": 1450392,
  "metrics": {
    "caps": 84.2,
    "blunders": 1.2,
    "mistakes": 3.4,
    "inaccuracies": 5.1
  },
  "openings": {
    "eco_A": { "played": 45, "win_rate": 0.51 },
    "eco_B": { "played": 82, "win_rate": 0.62 },
    "eco_C": { "played": 31, "win_rate": 0.45 }
  }
}`}
            </pre>
          </div>
        )}
      </section>
      
    </div>
  );
}

function MetricCard({ title, value, trend, trendUp, icon, desc }: { 
  title: string, value: string, trend: string, trendUp: boolean, icon: React.ReactNode, desc: string 
}) {
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col relative overflow-hidden">
      <div className="flex items-start justify-between mb-2">
        <span className="text-sm font-bold text-slate-500">{title}</span>
        <div className="p-2 bg-slate-50 rounded-lg">{icon}</div>
      </div>
      <div className="flex items-baseline gap-2 mt-auto">
        <span className="text-3xl font-black text-slate-800">{value}</span>
        <span className={cn("text-sm font-bold", trendUp ? "text-[#81B64C]" : "text-red-500")}>
          {trend}
        </span>
      </div>
      <span className="text-xs font-medium text-slate-400 mt-1">{desc}</span>
    </div>
  );
}

function ComparisonBar({ label, value, peerAvg }: { label: string, value: number, peerAvg: number }) {
  const isBetter = value >= peerAvg;
  return (
    <div>
      <div className="flex justify-between text-sm font-medium mb-1">
        <span className="text-slate-300">{label}</span>
        <span className="text-white">{value}/100</span>
      </div>
      <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className={cn("absolute top-0 left-0 h-full rounded-full", isBetter ? "bg-[#81B64C]" : "bg-amber-500")}
          style={{ width: `${value}%` }}
        />
        <div 
          className="absolute top-0 bottom-0 w-1 bg-white z-10 -ml-0.5 shadow-[0_0_4px_rgba(255,255,255,0.5)]"
          style={{ left: `${peerAvg}%` }}
          title={`Peer Average: ${peerAvg}`}
        />
      </div>
    </div>
  );
}
