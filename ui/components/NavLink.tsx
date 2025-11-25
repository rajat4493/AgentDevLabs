"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavLinkProps = {
  href: string;
  label: string;
  collapsed?: boolean;
};

export function NavLink({ href, label, collapsed = false }: NavLinkProps) {
  const pathname = usePathname();
  const active =
    pathname === href || pathname.startsWith(`${href}/`);

  const baseClasses =
    "block rounded-md px-3 py-2 transition-colors text-sm font-medium";
  const activeClasses = active
    ? "bg-slate-800 text-white"
    : "text-slate-400 hover:bg-slate-800/50 hover:text-white";
  const layoutClasses = collapsed ? "text-center" : "";
  const displayChar = label.charAt(0).toUpperCase();

  return (
    <Link
      href={href}
      aria-label={label}
      className={`${baseClasses} ${activeClasses} ${layoutClasses}`}
    >
      {collapsed ? (
        <>
          <span aria-hidden="true">{displayChar}</span>
          <span className="sr-only">{label}</span>
        </>
      ) : (
        label
      )}
    </Link>
  );
}
