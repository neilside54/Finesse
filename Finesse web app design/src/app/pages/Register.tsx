import { useState, useRef, useEffect, useCallback } from "react";
import { Link } from "react-router";
import { ArrowLeft, Loader2, Check, X } from "lucide-react";
import { getCsrfToken } from "../lib/csrf";

export function Register() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [usernameStatus, setUsernameStatus] = useState<"idle" | "checking" | "available" | "taken">("idle");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const abortRef = useRef<AbortController>();
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const validateUsername = (value: string): string | null => {
    if (value.length === 0) return null; // don't show error while empty
    if (value.length < 3) return "At least 3 characters required.";
    if (!/^[a-zA-Z0-9]+$/.test(value)) return "Only letters and numbers allowed.";
    return null;
  };

  const checkUsernameAvailability = useCallback(async (value: string) => {
    abortRef.current?.abort();
    if (value.length < 3 || !/^[a-zA-Z0-9]+$/.test(value)) {
      setUsernameStatus("idle");
      return;
    }
    setUsernameStatus("checking");
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const res = await fetch(`/api/auth/username-check/${encodeURIComponent(value)}/`, {
        credentials: "same-origin",
        signal: controller.signal,
      });
      if (!res.ok) return;
      const data = await res.json();
      setUsernameStatus(data.available ? "available" : "taken");
    } catch (err: any) {
      if (err?.name !== "AbortError") setUsernameStatus("idle");
    }
  }, []);

  const handleUsernameChange = (value: string) => {
    setUsername(value);
    setUsernameError(validateUsername(value));
    // Reset status immediately for UX feedback
    setUsernameStatus("idle");
    // Debounce the async check by 500ms
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => checkUsernameAvailability(value), 500);
  };

  // Cleanup debounce and abort on unmount
  useEffect(() => {
    return () => {
      clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    };
  }, []);

  const handleEmailRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate username before submission
    const usernameErr = validateUsername(username);
    if (usernameErr) {
      setUsernameError(usernameErr);
      return;
    }
    if (username.length === 0) {
      setUsernameError("Username is required.");
      return;
    }

    if (password1 !== password2) {
      setError("Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      const form = new URLSearchParams();
      form.append("email", email);
      form.append("username", username);
      form.append("password1", password1);
      form.append("password2", password2);
      form.append("csrfmiddlewaretoken", getCsrfToken());

      const res = await fetch("/accounts/signup/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
        credentials: "same-origin",
        redirect: "manual",
      });

      // allauth returns 302 on success (redirect to LOGIN_REDIRECT_URL).
      // A 200 means the form was re-rendered with errors — NOT a success.
      if (res.status === 302) {
        window.location.href = "/";
        return;
      }

      // 200 = allauth re-rendered the signup form with an error.
      if (res.status === 200) {
        const html = await res.text();
        if (html.includes("already exists")) {
          setError("An account with this email already exists.");
        } else if (html.includes("too short")) {
          setError("Password is too short. Use at least 8 characters.");
        } else if (html.includes("common password")) {
          setError("This password is too common. Choose a stronger one.");
        } else if (html.includes("CSRF")) {
          setError("Session expired. Please refresh the page and try again.");
        } else {
          setError("Registration failed. Please check your details and try again.");
        }
        return;
      }

      setError("Something went wrong. Please try again.");
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-16">
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
          Create Account
        </h1>
        <p className="text-sm text-[#A89070]">
          Save your analysis history and track your improvement over time.
        </p>
      </div>

      {/* Social signups */}
      <div className="space-y-3 mb-8">
        <a
          href="/accounts/google/login/?process=signup"
          className="w-full flex items-center justify-center gap-3 py-3.5 border border-[#3D2B1A] bg-[#251A12] text-sm font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Sign up with Google
        </a>

        <a
          href="/accounts/lichess/login/?process=signup"
          className="w-full flex items-center justify-center gap-3 py-3.5 border border-[#3D2B1A] bg-[#251A12] text-sm font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
        >
          <span className="text-base font-bold" style={{ color: "#96bf3d" }}>♞</span>
          Sign up with Lichess
        </a>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4 mb-8">
        <div className="h-px bg-[#3D2B1A] flex-1"></div>
        <span className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]">
          or use email
        </span>
        <div className="h-px bg-[#3D2B1A] flex-1"></div>
      </div>

      {/* Email + password */}
      <form onSubmit={handleEmailRegister} className="space-y-4">
        {error && (
          <div className="border border-[#B85C4A]/30 bg-[#B85C4A]/5 px-4 py-3 text-xs text-[#B85C4A]">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="register-email"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Email
          </label>
          <input
            id="register-email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="register-username"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Username
          </label>
          <div className="relative">
            <input
              id="register-username"
              type="text"
              placeholder="e.g. chessfan42"
              value={username}
              onChange={(e) => handleUsernameChange(e.target.value)}
              required
              className={`w-full h-12 px-4 pr-10 bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none transition-colors border ${
                usernameError
                  ? "border-[#B85C4A]"
                  : usernameStatus === "available"
                  ? "border-[#7A9E5F]"
                  : usernameStatus === "taken"
                  ? "border-[#B85C4A]"
                  : "border-[#3D2B1A] focus:border-[#C8A96E]"
              }`}
            />
            {/* Status icon inside the input */}
            <span className="absolute right-3 top-1/2 -translate-y-1/2">
              {usernameStatus === "checking" && (
                <Loader2 size={14} className="animate-spin text-[#A89070]" />
              )}
              {usernameStatus === "available" && !usernameError && (
                <Check size={14} className="text-[#7A9E5F]" />
              )}
              {usernameStatus === "taken" && (
                <X size={14} className="text-[#B85C4A]" />
              )}
            </span>
          </div>
          {usernameError && (
            <p className="text-[11px] text-[#B85C4A] mt-1">{usernameError}</p>
          )}
          {!usernameError && usernameStatus === "taken" && (
            <p className="text-[11px] text-[#B85C4A] mt-1">This username is already taken.</p>
          )}
          {!usernameError && usernameStatus === "available" && (
            <p className="text-[11px] text-[#7A9E5F] mt-1">Username is available!</p>
          )}
        </div>

        <div className="space-y-2">
          <label
            htmlFor="register-password1"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Password
          </label>
          <input
            id="register-password1"
            type="password"
            placeholder="Choose a strong password"
            value={password1}
            onChange={(e) => setPassword1(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="register-password2"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Confirm Password
          </label>
          <input
            id="register-password2"
            type="password"
            placeholder="Re-enter your password"
            value={password2}
            onChange={(e) => setPassword2(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#C8A96E] text-[#1C1510] text-sm font-medium tracking-wide hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150 disabled:opacity-50"
        >
          {submitting ? <Loader2 size={16} className="animate-spin" /> : "Create Account"}
        </button>
      </form>

      <p className="text-center text-xs text-[#A89070] mt-8">
        Already have an account?{" "}
        <Link to="/login" className="text-[#F0E6D3] hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
