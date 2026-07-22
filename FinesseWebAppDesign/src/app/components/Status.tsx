import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export function Status() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'pending' | 'processing' | 'completed' | 'error'>('pending');
  const [progress, setProgress] = useState(0);

  const type = searchParams.get('type') || 'unknown';

  useEffect(() => {
    // Simulate task processing
    setStatus('processing');
    
    const interval = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(interval);
          setStatus('completed');
          return 100;
        }
        // Random increment
        return Math.min(p + Math.random() * 15, 100);
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const handleViewResults = () => {
    navigate(`/analysis/${id}`);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 animate-in fade-in zoom-in-95 duration-500">
      <div className="w-full max-w-md bg-white p-8 rounded-3xl shadow-xl shadow-slate-200/50 border border-slate-200 text-center">
        
        {status === 'processing' && (
          <>
            <div className="relative w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <Loader2 className="w-12 h-12 text-[#81B64C] animate-spin" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Analyzing Games</h2>
            <p className="text-slate-500 mb-8 text-sm">
              We're crunching the numbers with Stockfish 16. This usually takes less than a minute.
            </p>
            
            <div className="w-full bg-slate-100 rounded-full h-3 mb-2 overflow-hidden">
              <div 
                className="bg-[#81B64C] h-full rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between text-xs font-semibold text-slate-400 mb-8">
              <span>Task ID: {id}</span>
              <span>{Math.round(progress)}%</span>
            </div>

            <button className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors">
              Run synchronously instead?
            </button>
          </>
        )}

        {status === 'completed' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="w-20 h-20 mx-auto mb-6 bg-green-50 rounded-full flex items-center justify-center border-8 border-green-50/50">
              <CheckCircle2 className="w-10 h-10 text-green-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Analysis Complete!</h2>
            <p className="text-slate-500 mb-8 text-sm">
              Successfully analyzed {type === 'username' ? '100 recent games' : 'games from PGN'}.
            </p>
            <button 
              onClick={handleViewResults}
              className="w-full bg-[#81B64C] hover:bg-[#73a344] text-white py-3.5 px-6 rounded-xl font-bold text-lg shadow-lg shadow-[#81B64C]/30 transition-all active:scale-[0.98]"
            >
              View Results Dashboard
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="animate-in fade-in duration-500">
            <div className="w-20 h-20 mx-auto mb-6 bg-red-50 rounded-full flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Analysis Failed</h2>
            <p className="text-slate-500 mb-8 text-sm">
              We encountered an issue processing the games. Please check the {type === 'username' ? 'username' : 'PGN formatting'} and try again.
            </p>
            <button 
              onClick={() => navigate('/')}
              className="w-full bg-slate-800 hover:bg-slate-900 text-white py-3 px-6 rounded-xl font-bold shadow-md transition-all active:scale-[0.98]"
            >
              Go Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
