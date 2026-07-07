import { useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, Copy, Check } from "lucide-react";

const CRYPTO_ADDRESS = "0xDCfDFbB1E47A5f9DcC502da0E67e90E1163BD3b2";
const NOWPAYMENTS_URL =
  "https://nowpayments.io/donation?api_key=f4c26743-4215-4b56-a731-3af6cbba2a9b";

export function Support() {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(CRYPTO_ADDRESS);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = CRYPTO_ADDRESS;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-8">
      <Link
        to="/"
        className="inline-flex items-center text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] mb-8 transition-colors"
      >
        <ArrowLeft size={14} className="mr-1.5" /> Back
      </Link>

      {/* Header */}
      <div className="mb-10 text-center">
        <h1
          className="text-4xl font-bold tracking-tight mb-2"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          <span className="text-[#C8A96E]">♞</span> Support Finesse
        </h1>
        <p className="text-sm text-[#A89070] leading-relaxed max-w-md mx-auto mt-4">
          Finesse is free and always will be.
          <br />
          If it helped your chess, consider supporting the project.
        </p>
      </div>

      <div className="space-y-8">
        {/* Section 1 — Crypto */}
        <section className="border border-[#3D2B1A] bg-[#251A12] p-6 space-y-4">
          <h2
            className="text-lg font-semibold text-[#F0E6D3]"
            style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          >
            Send crypto directly — zero fees
          </h2>

          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-0.5 text-[10px] uppercase tracking-[0.15em] font-semibold text-[#C8A96E] border border-[#C8A96E]/30 bg-[#C8A96E]/10">
              BNB Smart Chain (BEP20)
            </span>
            <span className="text-[10px] uppercase tracking-[0.15em] font-semibold text-[#A89070]">
              USDT
            </span>
          </div>

          {/* Address box */}
          <div className="flex items-center gap-2 bg-[#1C1510] border border-[#3D2B1A] px-4 py-3">
            <code className="flex-1 text-xs font-mono text-[#F0E6D3] break-all leading-relaxed select-all">
              {CRYPTO_ADDRESS}
            </code>
            <button
              onClick={handleCopy}
              className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#C8A96E] text-[#1C1510] text-[10px] uppercase tracking-[0.15em] font-semibold hover:bg-[#D4B87A] transition-colors"
            >
              {copied ? (
                <>
                  <Check size={12} /> Copied ✓
                </>
              ) : (
                <>
                  <Copy size={12} /> Copy Address
                </>
              )}
            </button>
          </div>

          <p className="text-[11px] text-[#A89070]">
            Fastest option. No platform fees.
          </p>
        </section>

        {/* Section 2 — NOWPayments */}
        <section className="border border-[#3D2B1A] bg-[#251A12] p-6 space-y-4">
          <h2
            className="text-lg font-semibold text-[#F0E6D3]"
            style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
          >
            Donate with card or any crypto
          </h2>

          <a
            href={NOWPAYMENTS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#C8A96E] text-[#1C1510] text-sm font-semibold tracking-wide hover:bg-[#D4B87A] transition-colors"
          >
            Donate via NOWPayments ♟
          </a>

          <p className="text-[11px] text-[#A89070]">
            Supports Visa, Mastercard, and 300+ cryptocurrencies. 0.5% fee.
          </p>
        </section>
      </div>

      {/* Footer note */}
      <div className="mt-12 text-center border-t border-[#3D2B1A] pt-8">
        <p
          className="text-sm text-[#A89070] leading-relaxed max-w-md mx-auto"
          style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
        >
          Every donation keeps the server running and motivates new features.
          <br />
          Thank you for being part of Finesse. ♟
        </p>
      </div>
    </div>
  );
}
