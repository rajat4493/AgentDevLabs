import Link from "next/link";
import type { ReactNode } from "react";

type LayoutProps = {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

const NAV_LINKS = [
  { label: "Overview", href: "/" },
  { label: "Traces", href: "/traces" },
  { label: "Stats", href: "/stats" },
];

export function Layout({ title, subtitle, actions, children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-900/70 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <Link href="/" className="text-xl font-semibold tracking-wide text-white">
              RAJOS
            </Link>
            <p className="text-xs uppercase tracking-[0.3em] text-amber-400">Tracing & Routing Devkit</p>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            {NAV_LINKS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="font-medium text-slate-300 transition hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        {(title || subtitle || actions) && (
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              {title && <h1 className="text-2xl font-semibold text-white sm:text-3xl">{title}</h1>}
              {subtitle && <p className="text-slate-400">{subtitle}</p>}
            </div>
            {actions}
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
