"use client";

import { useTheme } from "@/components/theme-provider";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-1 rounded-full border border-slate-300/80 dark:border-slate-700/70 bg-white/70 dark:bg-slate-900/80 px-2.5 py-1 text-[11px] font-medium text-slate-800 dark:text-slate-100 shadow-sm hover:bg-white hover:dark:bg-slate-800 transition-colors"
      aria-label="Toggle theme"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
      <span className="hidden sm:inline">{isDark ? "Dark" : "Light"}</span>
      <span className="sm:hidden">{isDark ? "D" : "L"}</span>
    </button>
  );
}
