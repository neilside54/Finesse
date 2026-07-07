import { useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, Loader2 } from "lucide-react";
import { getCsrfToken } from "../lib/csrf";

/**
 * Social-first login page for Finesse.
 *
 * django-allauth handles the actual authentication flow server-side.
 * This page provides the entry points:
 *   1. Google OAuth  (redirect to /accounts/google/login/)
 *   2. Email + password (POST to /accounts/login/)
 *   3. Link to register page
 *
 * After successful login, allauth redirects to LOGIN_REDIRECT_URL = "/"
 */

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const form = new URLSearchParams();
      form.append("login", email);
      form.append("password", password);
      form.append("csrfmiddlewaretoken", getCsrfToken());

      const res = await fetch("/accounts/login/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
        credentials: "same-origin",
        redirect: "manual",
      });

      // allauth returns 302 on success (redirect to LOGIN_REDIRECT_URL).
      // A 200 means the form was re-rendered with errors (wrong password,
      // CSRF failure, etc.). We must NOT treat 200 as success.
      if (res.status === 302) {
        window.location.href = "/";
        return;
      }

      // 200 = allauth re-rendered the login form with an error.
      if (res.status === 200) {
        const html = await res.text();
        // allauth puts errors in <ul class="errorlist"> or the form has
        // a field with class "errorlist". Extract a user-friendly message.
        if (html.includes("The e-mail address and/or password are not")) {
          setError("Invalid email or password. Please try again.");
        } else if (html.includes(" CSRF")) {
          setError("Session expired. Please refresh the page and try again.");
        } else {
          setError("Invalid email or password. Please try again.");
        }
        return;
      }

      // Any other status (400, 403, 500, etc.)
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
          Welcome Back
        </h1>
        <p className="text-sm text-[#A89070]">
          Sign in to access your saved analyses and history.
        </p>
      </div>

      {/* Social logins - primary path */}
      <div className="space-y-3 mb-8">
        <a
          href="/accounts/google/login/?process=login"
          className="w-full flex items-center justify-center gap-3 py-3.5 border border-[#3D2B1A] bg-[#251A12] text-sm font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </a>

        <a
          href="/accounts/lichess/login/?process=login"
          className="w-full flex items-center justify-center gap-3 py-3.5 border border-[#3D2B1A] bg-[#251A12] text-sm font-medium tracking-wide text-[#F0E6D3] hover:bg-[#2E2016] active:scale-[0.97] transition-all duration-150"
        >
          <span className="text-base font-bold" style={{ color: "#96bf3d" }}>♞</span>
          Continue with Lichess
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

      {/* Email + password fallback */}
      <form onSubmit={handleEmailLogin} className="space-y-4">
        {error && (
          <div className="border border-[#B85C4A]/30 bg-[#B85C4A]/5 px-4 py-3 text-xs text-[#B85C4A]">
            {error}
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="login-email"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Email or Username
          </label>
          <input
            id="login-email"
            type="text"
            placeholder="you@example.com or username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        <div className="space-y-2">
          <label
            htmlFor="login-password"
            className="text-[10px] uppercase tracking-[0.2em] font-medium text-[#A89070]"
          >
            Password
          </label>
          <input
            id="login-password"
            type="password"
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full h-12 px-4 border border-[#3D2B1A] bg-[#251A12] text-sm text-[#F0E6D3] placeholder:text-[#A89070]/50 focus:outline-none focus:border-[#C8A96E] transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full flex items-center justify-center gap-2 py-3.5 bg-[#C8A96E] text-[#1C1510] text-sm font-medium tracking-wide hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150 disabled:opacity-50"
        >
          {submitting ? <Loader2 size={16} className="animate-spin" /> : "Sign In"}
        </button>
      </form>

      <p className="text-center text-xs text-[#A89070] mt-8">
        Don't have an account?{" "}
        <Link to="/register" className="text-[#F0E6D3] hover:underline font-medium">
          Create one free
        </Link>
      </p>
    </div>
  );
}
