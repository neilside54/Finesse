import { useEffect, useState } from "react";
import { Outlet, Link, useLocation } from "react-router";
import { User, LogOut } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

export function Layout() {
  const location = useLocation();
  const { user, loading, isAuthenticated, login, register, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col transition-colors duration-300">
      {/* Header — transparent at top, warm blurred on scroll */}
      <header
        className={`sticky top-0 z-50 border-b transition-all duration-300 ${
          scrolled
            ? "border-border/60 bg-[#1C1510]/85 backdrop-blur-md"
            : "border-transparent bg-transparent"
        }`}
      >
        <div className="max-w-5xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-14">
            <Link to="/" className="flex items-baseline gap-1.5 hover:opacity-70 transition-opacity">
              <span className="text-xl font-bold tracking-tight text-[#C8A96E]">
                ♞
              </span>
              <span
                className="text-xl font-bold tracking-tight text-[#F0E6D3]"
                style={{ fontFamily: "'Playfair Display', Georgia, serif" }}
              >
                Finesse
              </span>
            </Link>
            <nav className="flex items-center gap-6">
              <Link
                to="/analyze/username"
                className={`text-xs uppercase tracking-[0.15em] font-medium transition-colors ${
                  location.pathname === "/analyze/username"
                    ? "text-[#C8A96E]"
                    : "text-[#A89070] hover:text-[#F0E6D3]"
                }`}
              >
                Username
              </Link>
              <Link
                to="/analyze/pgn"
                className={`text-xs uppercase tracking-[0.15em] font-medium transition-colors ${
                  location.pathname === "/analyze/pgn"
                    ? "text-[#C8A96E]"
                    : "text-[#A89070] hover:text-[#F0E6D3]"
                }`}
              >
                PGN Upload
              </Link>
              <Link
                to="/support"
                className={`text-xs uppercase tracking-[0.15em] font-medium transition-colors ${
                  location.pathname === "/support"
                    ? "text-[#C8A96E]"
                    : "text-[#A89070] hover:text-[#F0E6D3]"
                }`}
              >
                Support ♟
              </Link>

              {/* Auth section */}
              {!loading && (
                <div className="flex items-center gap-3 pl-3 border-l border-border">
                  {isAuthenticated ? (
                    <>
                      <Link
                        to="/history"
                        className={`text-xs uppercase tracking-[0.15em] font-medium transition-colors ${
                          location.pathname === "/history"
                            ? "text-[#C8A96E]"
                            : "text-[#A89070] hover:text-[#F0E6D3]"
                        }`}
                      >
                        History
                      </Link>
                      <Link
                        to="/profile"
                        className="flex items-center gap-1.5 text-xs text-[#A89070] hover:text-[#F0E6D3] transition-colors"
                      >
                        <User size={13} />
                        {user?.username}
                      </Link>
                      <button
                        onClick={logout}
                        className="text-[10px] uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] transition-colors"
                      >
                        <LogOut size={13} />
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        to="/login"
                        className="text-[10px] uppercase tracking-[0.15em] font-medium text-[#A89070] hover:text-[#F0E6D3] transition-colors"
                      >
                        Sign In
                      </Link>
                      <Link
                        to="/register"
                        className="text-[10px] uppercase tracking-[0.15em] font-medium bg-[#C8A96E] text-[#1C1510] px-3 py-1.5 hover:bg-[#D4B87A] active:scale-[0.97] transition-all duration-150"
                      >
                        Sign Up
                      </Link>
                    </>
                  )}
                </div>
              )}


            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-6 lg:px-8 py-10">
        <Outlet />
      </main>

      {/* Footer — warm palette */}
      <footer className="border-t border-border py-8 mt-auto">
        <div className="max-w-5xl mx-auto px-6 text-center">            <p className="text-xs text-[#A89070] tracking-wide">
            Finesse
          </p>
        </div>
      </footer>
    </div>
  );
}
