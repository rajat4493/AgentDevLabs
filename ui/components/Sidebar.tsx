"use client";

import { NavLink } from "@/components/NavLink";

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
};

const navItems = [
  { name: "Overview", href: "/overview" },
  { name: "Playground", href: "/playground" },
  { name: "Logs", href: "/logs" },
  { name: "Analytics", href: "/analytics" },
  { name: "Settings", href: "/settings" },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const widthClass = collapsed ? "w-16" : "w-56";

  return (
    <aside
      className={`relative z-20 flex h-screen flex-col border-r border-slate-800 bg-slate-900/95 p-4 text-sm text-slate-100 shadow-2xl transition-all duration-300 ease-in-out ${widthClass}`}
    >
      <div
        className={`mb-6 font-semibold text-white ${
          collapsed ? "text-base text-center" : "text-lg"
        }`}
      >
        {collapsed ? "AL" : "AgenticLabs"}
      </div>
      <nav className="flex-1 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            href={item.href}
            label={item.name}
            collapsed={collapsed}
          />
        ))}
      </nav>
      <button
        type="button"
        onClick={onToggle}
        className="mt-6 flex items-center justify-center rounded-md border border-slate-700/70 px-2 py-1 text-xs text-slate-200 transition hover:bg-slate-800/70"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <span aria-hidden="true" className="text-lg leading-none">
          {collapsed ? "›" : "‹"}
        </span>
      </button>
    </aside>
  );
}
