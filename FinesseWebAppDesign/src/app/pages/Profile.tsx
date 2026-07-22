import { useEffect, useState } from "react";
import { Link } from "react-router";
import {
  ArrowLeft,
  Loader2,
  Plus,
  Star,
  Trash2,
  ExternalLink,
} from "lucide-react";
import { getCsrfToken } from "../lib/csrf";

interface LinkedAccount {
  id: string;
  platform: string;
  platform_username: string;
  is_primary: boolean;
  rating: number | null;
  linked_at: string;
}

export function Profile() {
  const [linkedAccounts, setLinkedAccounts] = useState<LinkedAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New linked account form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPlatform, setNewPlatform] = useState<"chess.com" | "lichess">("chess.com");
  const [newUsername, setNewUsername] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const linkedRes = await fetch("/api/auth/linked-accounts/", { credentials: "same-origin" });

        if (linkedRes.status === 401) {
          if (!cancelled) setError("auth");
          return;
        }

        if (linkedRes.ok) {
          const data = await linkedRes.json();
          if (!cancelled) setLinkedAccounts(data.linked_accounts ?? []);
        }
      } catch {
        if (!cancelled) setError("Failed to load profile.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim()) return;
    setAdding(true);
    try {
      const res = await fetch("/api/auth/linked-accounts/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        credentials: "same-origin",
        body: JSON.stringify({
          platform: newPlatform,
          platform_username: newUsername.trim(),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.created) {
          setLinkedAccounts((prev) => [...prev, data]);
          setNewUsername("");
          setShowAddForm(false);
        } else {
          setError("This account is already linked.");
        }
      } else {
        const data = await res.json();
        setError(data.error || "Failed to add account.");
      }
    } catch {
      setError("Failed to add account.");
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveAccount = async (id: string) => {
    try {
      const res = await fetch(`/api/auth/linked-accounts/${id}/`, {
        method: "DELETE",
        credentials: "same-origin",
        headers: { "X-CSRFToken": getCsrfToken() },
      });
      if (res.ok) {
        setLinkedAccounts((prev) => prev.filter((a) => a.id !== id));
      }
    } catch {
      // ignore
    }
  };

  const handleSetPrimary = async (id: string) => {
    try {
      const res = await fetch(`/api/auth/linked-accounts/${id}/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        credentials: "same-origin",
        body: JSON.stringify({ is_primary: true }),
      });
      if (res.ok) {
        setLinkedAccounts((prev) =>
          prev.map((a) => ({ ...a, is_primary: a.id === id }))
        );
      }
    } catch {
      // ignore
    }
  };

  // Auth required state
  if (!loading && error === "auth") {
    return (
      <div className="max-w-xl mx-auto py-8">
        <Link
          to="/"
          className="inline-flex items-center text-xs uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] mb-8 transition-colors"
        >
          <ArrowLeft size={14} className="mr-1.5" /> Back
        </Link>
        <div className="border border-[#3D2B1A] bg-[#2E2016] p-8 text-center">
          <p className="text-sm text-[#A89070] mb-4">
            Sign in to view your profile.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center px-5 py-2.5 bg-[#C8A96E] text-[#1C1510] text-xs uppercase tracking-[0.15em] font-medium hover:bg-[#D4B87A] transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

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
          Profile
        </h1>
        <p className="text-sm text-[#A89070]">
          Manage your account details and linked chess platforms.
        </p>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 size={20} className="animate-spin text-[#A89070]" />
        </div>
      )}

      {!loading && (
        <div className="space-y-8">
          {/* Error banner */}
          {error && error !== "auth" && (
            <div className="border border-[#B85C4A]/30 bg-[#B85C4A]/5 px-4 py-3 text-xs text-[#B85C4A]">
              {error}
            </div>
          )}

          {/* Linked Chess Accounts */}
          <section className="border border-[#3D2B1A] bg-[#251A12] p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2
                className="text-lg font-semibold text-[#F0E6D3]"
                style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
              >
                Linked Chess Accounts
              </h2>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-[#3D2B1A] text-[10px] uppercase tracking-[0.15em] font-semibold text-[#A89070] hover:text-[#F0E6D3] hover:border-[#C8A96E] active:scale-[0.97] transition-all duration-150"
              >
                <Plus size={12} />
                Link Account
              </button>
            </div>

            <p className="text-xs text-[#A89070]">
              Link your Chess.com or Lichess accounts for quick one-click analysis.
            </p>

            {/* Add form */}
            {showAddForm && (
              <form
                onSubmit={handleAddAccount}
                className="border border-[#C8A96E]/30 bg-[#1C1510] p-4 space-y-3"
              >
                <div className="flex gap-3">
                  <select
                    value={newPlatform}
                    onChange={(e) =>
                      setNewPlatform(e.target.value as "chess.com" | "lichess")
                    }
                    className="h-10 px-3 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] focus:outline-none focus:border-[#C8A96E] transition-colors"
                  >
                    <option value="chess.com">Chess.com</option>
                    <option value="lichess">Lichess</option>
                  </select>
                  <input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="Platform username"
                    required
                    className="flex-1 h-10 px-3 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={adding || !newUsername.trim()}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#C8A96E] text-[#1C1510] text-[10px] uppercase tracking-[0.15em] font-semibold hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150 disabled:opacity-50"
                  >
                    {adding ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      "Add"
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddForm(false);
                      setNewUsername("");
                    }}
                    className="px-4 py-2 border border-[#3D2B1A] text-[10px] uppercase tracking-[0.15em] font-semibold text-[#A89070] hover:text-[#F0E6D3] active:scale-[0.97] transition-all duration-150"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            {/* Empty state */}
            {linkedAccounts.length === 0 && !showAddForm && (
              <div className="border border-dashed border-[#3D2B1A] p-6 text-center">
                <p className="text-sm text-[#A89070]">
                  No linked accounts yet.
                </p>
                <p className="text-xs text-[#A89070]/70 mt-1">
                  Link your chess platform accounts for quick analysis.
                </p>
              </div>
            )}

            {/* Linked accounts list */}
            {linkedAccounts.length > 0 && (
              <div className="space-y-2">
                {linkedAccounts.map((account) => (
                  <div
                    key={account.id}
                    className="flex items-center justify-between gap-4 bg-[#1C1510] border border-[#3D2B1A] p-4"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span
                          className="text-xs font-semibold uppercase tracking-wider"
                          style={{
                            color:
                              account.platform === "chess.com"
                                ? "#7A9E5F"
                                : "#96bf3d",
                          }}
                        >
                          {account.platform}
                        </span>
                        <span className="text-sm font-medium text-[#F0E6D3]">
                          {account.platform_username}
                        </span>
                        {account.is_primary && (
                          <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] uppercase tracking-[0.15em] font-semibold text-[#C8A96E] border border-[#C8A96E]/30 bg-[#C8A96E]/10">
                            <Star size={9} fill="currentColor" /> Primary
                          </span>
                        )}
                        {account.rating != null && (
                          <span className="text-xs text-[#A89070]">
                            {account.rating} ELO
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!account.is_primary && (
                        <button
                          onClick={() => handleSetPrimary(account.id)}
                          className="p-1.5 text-[#A89070] hover:text-[#C8A96E] active:scale-[0.97] transition-all duration-150"
                          title="Set as primary"
                        >
                          <Star size={14} />
                        </button>
                      )}
                      <a
                        href={`https://${account.platform === "chess.com" ? "www.chess.com" : "lichess.org"}/${account.platform_username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 text-[#A89070] hover:text-[#F0E6D3] active:scale-[0.97] transition-all duration-150"
                        title="View profile"
                      >
                        <ExternalLink size={14} />
                      </a>
                      <button
                        onClick={() => handleRemoveAccount(account.id)}
                        className="p-1.5 text-[#A89070] hover:text-[#B85C4A] active:scale-[0.97] transition-all duration-150"
                        title="Unlink account"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
