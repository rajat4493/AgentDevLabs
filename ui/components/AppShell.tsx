"use client";

import { useState, type ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((prev) => !prev)} />
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</div>
    </div>
  );
}

