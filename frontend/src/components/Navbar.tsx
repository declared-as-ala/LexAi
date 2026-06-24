import { useState } from "react";
import { Link, useLocation } from "react-router-dom";

const NAV_LINKS = [
  { to: "/", label: "Accueil" },
  { to: "/analyze", label: "Analyser" },
  { to: "/how-it-works", label: "Comment ça marche" },
];

export function Navbar() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-gold-200/40 bg-white/90 backdrop-blur-md shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-gold-500 to-gold-400 shadow-[0_2px_10px_rgba(201,163,54,0.35)] transition-transform group-hover:scale-105">
            <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.97z" />
            </svg>
          </div>
          <div>
            <span className="block text-[10px] font-bold uppercase tracking-[0.22em] text-gold-600 leading-none">LexAI</span>
            <span className="block text-sm font-semibold text-stone-800 leading-none mt-0.5">Compliance IA</span>
          </div>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((l) => {
            const active = pathname === l.to;
            return (
              <Link
                key={l.to}
                to={l.to}
                className={[
                  "rounded-lg px-4 py-2 text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-amber-50 text-gold-700 font-semibold"
                    : "text-stone-600 hover:bg-stone-50 hover:text-stone-900",
                ].join(" ")}
              >
                {l.label}
              </Link>
            );
          })}
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-gold-600 to-gold-500 px-5 py-2 text-sm font-semibold text-white shadow-[0_2px_12px_rgba(201,163,54,0.40)] transition-all hover:from-gold-700 hover:to-gold-600 hover:shadow-[0_4px_16px_rgba(201,163,54,0.50)]"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Analyser un contrat
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="md:hidden rounded-lg p-2 text-stone-600 hover:bg-stone-100"
        >
          {open ? (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-gold-200/30 bg-white px-4 py-3 space-y-1">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className={[
                "block rounded-lg px-4 py-2.5 text-sm font-medium",
                pathname === l.to
                  ? "bg-amber-50 text-gold-700 font-semibold"
                  : "text-stone-700 hover:bg-stone-50",
              ].join(" ")}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/analyze"
            onClick={() => setOpen(false)}
            className="block mt-2 rounded-xl bg-gradient-to-r from-gold-600 to-gold-500 px-4 py-2.5 text-center text-sm font-semibold text-white"
          >
            Analyser un contrat
          </Link>
        </div>
      )}
    </nav>
  );
}
