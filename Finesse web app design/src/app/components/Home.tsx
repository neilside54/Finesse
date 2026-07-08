import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Upload, User, Play, ChevronRight, Activity, Target, Zap, Clock, FileText } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

export function Home() {
  const [activeTab, setActiveTab] = useState<'username' | 'pgn'>('username');
  const [username, setUsername] = useState('');
  const [platform, setPlatform] = useState<'lichess' | 'chesscom'>('lichess');
  const [pgnText, setPgnText] = useState('');
  const [limit, setLimit] = useState(50);
  
  const navigate = useNavigate();

  const handleUsernameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) return;
    navigate(`/status/12345?type=username&user=${username}&platform=${platform}&limit=${limit}`);
  };

  const handlePgnSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pgnText) return;
    navigate(`/status/67890?type=pgn`);
  };

  return (
    <div className="flex flex-col gap-16 pb-12 animate-in fade-in duration-500">
      {/* Hero Section */}
      <section className="text-center pt-8 md:pt-16 max-w-3xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight mb-6">
          Elevate your game with <span className="text-[#81B64C]">precision analysis</span>
        </h1>
        <p className="text-lg md:text-xl text-slate-600 mb-10 leading-relaxed">
          Finesse brings grandmaster-level insights to your daily games. Uncover opening flaws, 
          track blunder patterns, and compare your accuracy with peers seamlessly.
        </p>

        {/* Input Card */}
        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200 overflow-hidden text-left max-w-2xl mx-auto">
          {/* Tabs */}
          <div className="flex border-b border-slate-100 bg-slate-50/50">
            <button
              onClick={() => setActiveTab('username')}
              className={cn(
                "flex-1 py-4 px-6 text-sm font-semibold flex items-center justify-center gap-2 transition-colors",
                activeTab === 'username' 
                  ? "text-[#81B64C] bg-white border-b-2 border-[#81B64C]" 
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              )}
            >
              <User className="w-4 h-4" />
              Username Analysis
            </button>
            <button
              onClick={() => setActiveTab('pgn')}
              className={cn(
                "flex-1 py-4 px-6 text-sm font-semibold flex items-center justify-center gap-2 transition-colors",
                activeTab === 'pgn' 
                  ? "text-[#81B64C] bg-white border-b-2 border-[#81B64C]" 
                  : "text-slate-500 hover:text-slate-700 hover:bg-slate-50"
              )}
            >
              <FileText className="w-4 h-4" />
              PGN File Analysis
            </button>
          </div>

          <div className="p-6 md:p-8">
            {activeTab === 'username' ? (
              <form onSubmit={handleUsernameSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">Platform</label>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setPlatform('lichess')}
                      className={cn(
                        "flex-1 py-3 px-4 rounded-xl border-2 font-medium flex items-center justify-center gap-2 transition-all",
                        platform === 'lichess' 
                          ? "border-slate-800 bg-slate-800 text-white shadow-md" 
                          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                      )}
                    >
                      Lichess
                    </button>
                    <button
                      type="button"
                      onClick={() => setPlatform('chesscom')}
                      className={cn(
                        "flex-1 py-3 px-4 rounded-xl border-2 font-medium flex items-center justify-center gap-2 transition-all",
                        platform === 'chesscom' 
                          ? "border-[#81B64C] bg-[#81B64C] text-white shadow-md shadow-[#81B64C]/20" 
                          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                      )}
                    >
                      Chess.com
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="username" className="block text-sm font-semibold text-slate-700 mb-2">Username</label>
                  <input 
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. MagnusCarlsen"
                    className="w-full px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-[#81B64C] focus:ring-4 focus:ring-[#81B64C]/10 outline-none transition-all text-slate-900 font-medium placeholder:text-slate-400 placeholder:font-normal"
                    required
                  />
                </div>

                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label htmlFor="gameLimit" className="block text-sm font-semibold text-slate-700">Games to analyze</label>
                    <span className="text-sm font-bold text-[#81B64C]">{limit} games</span>
                  </div>
                  <input 
                    id="gameLimit"
                    type="range"
                    min="10"
                    max="100"
                    step="10"
                    value={limit}
                    onChange={(e) => setLimit(parseInt(e.target.value))}
                    className="w-full accent-[#81B64C] h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1 font-medium">
                    <span>10</span>
                    <span>100</span>
                  </div>
                </div>

                <div className="pt-2">
                  <button 
                    type="submit"
                    className="w-full bg-[#81B64C] hover:bg-[#73a344] text-white py-3.5 px-6 rounded-xl font-bold text-lg flex items-center justify-center gap-2 shadow-lg shadow-[#81B64C]/30 transition-all active:scale-[0.98]"
                  >
                    Analyze Games
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handlePgnSubmit} className="space-y-6">
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-100/50 transition-colors cursor-pointer group">
                  <div className="w-12 h-12 bg-white rounded-full shadow-sm border border-slate-200 flex items-center justify-center mx-auto mb-4 group-hover:scale-105 transition-transform">
                    <Upload className="w-6 h-6 text-slate-500 group-hover:text-[#81B64C]" />
                  </div>
                  <h3 className="text-sm font-bold text-slate-700 mb-1">Upload PGN File</h3>
                  <p className="text-xs text-slate-500 mb-4">Drag and drop, or click to browse</p>
                  <button type="button" className="text-sm font-semibold text-[#81B64C] bg-white border border-slate-200 px-4 py-2 rounded-lg shadow-sm hover:border-[#81B64C] transition-colors">
                    Select File
                  </button>
                </div>

                <div className="relative flex items-center py-2">
                  <div className="flex-grow border-t border-slate-200"></div>
                  <span className="flex-shrink-0 mx-4 text-xs font-medium text-slate-400 uppercase tracking-wider">or paste PGN</span>
                  <div className="flex-grow border-t border-slate-200"></div>
                </div>

                <div>
                  <textarea 
                    value={pgnText}
                    onChange={(e) => setPgnText(e.target.value)}
                    placeholder="[Event &quot;FIDE World Cup 2023&quot;]&#10;[Site &quot;Baku AZE&quot;]&#10;..."
                    className="w-full h-32 px-4 py-3 rounded-xl border-2 border-slate-200 focus:border-[#81B64C] focus:ring-4 focus:ring-[#81B64C]/10 outline-none transition-all text-sm font-mono text-slate-700 resize-none"
                    required
                  />
                </div>

                <div className="pt-2">
                  <button 
                    type="submit"
                    className="w-full bg-[#81B64C] hover:bg-[#73a344] text-white py-3.5 px-6 rounded-xl font-bold text-lg flex items-center justify-center gap-2 shadow-lg shadow-[#81B64C]/30 transition-all active:scale-[0.98]"
                  >
                    Analyze PGN
                    <ChevronRight className="w-5 h-5" />
                  </button>
                  <div className="text-center text-xs text-slate-500 mt-4 flex flex-col gap-1">
                    <span>Supported file types: .pgn (Max size 5MB).</span>
                    <span>You can export PGNs from your profile on Chess.com or Lichess.</span>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* Feature Summary */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6 px-4">
        <FeatureCard 
          icon={<Activity className="w-6 h-6 text-blue-500" />}
          title="Accuracy Tracking"
          desc="Measure your CAPS and conversion rates across different time controls."
        />
        <FeatureCard 
          icon={<Target className="w-6 h-6 text-red-500" />}
          title="Blunder Patterns"
          desc="Identify tactical blindspots and the types of positions where you blunder most."
        />
        <FeatureCard 
          icon={<Zap className="w-6 h-6 text-amber-500" />}
          title="Opening Trends"
          desc="See which openings yield the highest win rates and where you fall into traps."
        />
        <FeatureCard 
          icon={<Clock className="w-6 h-6 text-purple-500" />}
          title="Time Management"
          desc="Analyze your clock usage in critical positions vs your opponents."
        />
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm text-slate-600 leading-relaxed">{desc}</p>
    </div>
  );
}
