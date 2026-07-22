import { useState } from "react";
import { useNavigate } from "react-router";
import { Upload, FileText, ArrowRight, AlertTriangle } from "lucide-react";

export function AnalyzePgn() {
  const [pgnText, setPgnText] = useState("");
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [rateLimitError, setRateLimitError] = useState(false);
  const navigate = useNavigate();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    if (file.name.endsWith(".pgn")) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target?.result as string | null;
        if (text) setPgnText(text);
      };
      reader.onerror = () => alert("Failed to read the PGN file");
      reader.readAsText(file, "utf-8");
    } else {
      alert("Please upload a valid .pgn file");
    }
  };

  const handleAnalyze = () => {
    if (!pgnText) return;
    setRateLimitError(false);
    (async () => {
      try {
        const form = new FormData();
        form.append("pgn", pgnText);
        const resp = await fetch(`/api/analyze-async/`, {
          method: "POST",
          body: form,
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
        alert("Failed to start PGN analysis. Check the backend or network.");
      }
    })();
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      {/* Header */}
      <div className="mb-10">
        <h1
          className="text-4xl font-bold tracking-tight mb-2"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Upload PGN
        </h1>
        <p className="text-sm text-[#A89070]">
          Analyze custom games, tournaments, or external databases.
        </p>
      </div>

      <div className="space-y-8">
        {/* Drag & Drop Area */}
        <div
          className={`border-2 border-dashed p-12 text-center transition-colors ${
            dragActive
              ? "border-[#C8A96E] bg-[#C8A96E]/5"
              : "border-[#3D2B1A] hover:border-[#A89070]/50 bg-[#251A12]"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {fileName ? (
            <div className="flex flex-col items-center gap-4">
              <FileText size={28} className="text-[#C8A96E]" />
              <div>
                <p className="text-sm font-medium text-[#F0E6D3]">{fileName}</p>
                <button
                  onClick={() => {
                    setFileName(null);
                    setPgnText("");
                  }}
                  className="text-xs text-[#B85C4A] hover:underline mt-1"
                >
                  Remove file
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <Upload size={28} className="text-[#A89070]" />
              <div>
                <p className="text-sm font-medium text-[#F0E6D3]">
                  Drag and drop your PGN file here
                </p>
                <p className="text-xs text-[#A89070] mt-1">
                  Supported file types: .pgn, max 10MB
                </p>
              </div>
              <button
                type="button"
                onClick={() => document.getElementById("file-upload")?.click()}
                className="inline-flex items-center justify-center px-5 py-2 border border-[#3D2B1A] text-xs font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
              >
                Select File
              </button>
              <input
                id="file-upload"
                type="file"
                accept=".pgn"
                className="hidden"
                onChange={(e) => e.target.files && handleFile(e.target.files[0])}
              />
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="flex items-center gap-4">
          <div className="h-px bg-[#3D2B1A] flex-1"></div>
          <span className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]">
            or paste text
          </span>
          <div className="h-px bg-[#3D2B1A] flex-1"></div>
        </div>

        {/* Text Area */}
        <div className="space-y-3">
          <label className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]">
            Raw PGN Text
          </label>
          <textarea
            className="w-full h-48 border border-[#3D2B1A] bg-[#251A12] p-4 font-mono text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] resize-none transition-colors leading-relaxed"
            placeholder={`[Event "FIDE World Cup 2023"]\n[Site "Baku AZE"]\n[Date "2023.08.24"]\n...`}
            value={pgnText}
            onChange={(e) => setPgnText(e.target.value)}
            disabled={!!fileName}
          />
        </div>

        {/* Rate limit warning */}
        {rateLimitError && (
          <div className="flex gap-3 items-start border border-[#B85C4A]/30 bg-[#B85C4A]/5 p-4">
            <AlertTriangle size={14} className="text-[#B85C4A] mt-0.5 shrink-0" />
            <p className="text-xs text-[#B85C4A] leading-relaxed">
              You've been rate-limited. Please wait a minute before trying again.
            </p>
          </div>
        )}

        {/* Submit */}
        <button
          onClick={handleAnalyze}
          disabled={!pgnText}
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#C8A96E] text-[#1C1510] text-sm font-medium tracking-wide hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Analyze PGN
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}
