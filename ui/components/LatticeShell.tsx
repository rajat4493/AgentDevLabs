import Link from "next/link";
import { useRouter } from "next/router";
import type { ReactNode } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/utils";

type ShellProps = {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

const NAV_LINKS: Array<{ label: string; icon: string; href?: string }> = [
  { label: "Overview", icon: "●", href: "/" },
  { label: "Playground", icon: "▶" },
  { label: "Metrics", icon: "✦", href: "/traces" },
  { label: "Stats", icon: "▣", href: "/stats" },
  { label: "Settings", icon: "⚙" },
];

export default function LatticeShell({ title, subtitle, actions, children }: ShellProps) {
  const router = useRouter();
  const envLabel = process.env.NEXT_PUBLIC_LATTICE_ENV || "Local Dev";
  const heading = title || "Overview";

  return (
    <div className="relative min-h-screen overflow-hidden font-sans text-slate-900 dark:text-slate-100 transition-colors">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.08),_transparent_45%),radial-gradient(circle_at_bottom,_rgba(14,165,233,0.08),_transparent_40%)] dark:bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_45%),radial-gradient(circle_at_bottom,_rgba(59,130,246,0.18),_transparent_40%)]" />
      <div className="absolute inset-0 bg-white/70 dark:bg-[#050816]/90 backdrop-blur-2xl" />
      <div className="relative z-10 flex min-h-screen">
        <aside className="hidden md:flex w-60 flex-col border-r border-white/40 dark:border-white/10 bg-white/40 dark:bg-white/5 backdrop-blur-2xl shadow-[0_0_40px_rgba(15,23,42,0.15)]">
        <div className="px-5 py-4 flex items-center gap-2 border-b border-slate-200/80 dark:border-slate-800">
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/40 grid grid-cols-3 grid-rows-3 gap-[2px] p-[2px]">
            {Array.from({ length: 9 }).map((_, idx) => (
              <div key={idx} className="rounded-[2px] bg-emerald-400/80" />
            ))}
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight">Lattice</p>
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
              LLM Proxy &amp; Monitor
            </p>
          </div>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 text-sm">
          {NAV_LINKS.map((item) => {
            const isActive = item.href ? router.pathname === item.href : false;
            if (!item.href) {
              return (
                <button
                  key={item.label}
                  type="button"
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-slate-400/80 dark:text-slate-600 cursor-not-allowed border border-transparent"
                >
                  <span className="text-xs">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              );
            }
            return (
              <Link
                key={item.label}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 hover:text-slate-900 hover:dark:bg-slate-800/70 hover:dark:text-slate-50 transition-colors border border-transparent",
                  isActive && "bg-slate-100 dark:bg-slate-800/80 text-slate-900 dark:text-slate-50 border-slate-200 dark:border-slate-700"
                )}
              >
                <span className="text-xs">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="px-4 py-4 border-t border-slate-200/80 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center justify-between">
            <span>Environment</span>
            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {envLabel}
            </span>
          </div>
        </div>
      </aside>
        <main className="flex-1 flex flex-col">
        <header className="h-16 border-b border-white/40 dark:border-white/10 bg-white/60 dark:bg-white/5 backdrop-blur-2xl flex items-center justify-between px-4 md:px-6 shadow-[0_10px_30px_rgba(15,23,42,0.08)]">
          <div>
            <h1 className="text-base font-semibold tracking-tight">{heading}</h1>
            {subtitle ? (
              <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
            ) : (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Live view of your LLM traffic through Lattice.
              </p>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="hidden sm:inline-flex items-center gap-1 rounded-full border border-slate-200 dark:border-slate-700 px-2 py-1 text-slate-600 dark:text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Proxy online
            </span>
            {actions ?? (
              <button className="rounded-xl bg-emerald-500/90 hover:bg-emerald-400 text-slate-900 font-medium px-3 py-1.5 text-xs transition-colors">
                Open Playground
              </button>
            )}
            <ThemeToggle />
          </div>
        </header>
        <div className="relative flex-1 overflow-auto">
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.08] dark:opacity-[0.12]"
            style={{
              backgroundImage:
                "linear-gradient(to right, rgba(148,163,184,0.5) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.5) 1px, transparent 1px)",
              backgroundSize: "32px 32px",
            }}
          />
          <div className="relative z-10 px-4 md:px-6 py-5 md:py-8 space-y-6">{children}</div>
        </div>
        </main>
      </div>
    </div>
  );
}
