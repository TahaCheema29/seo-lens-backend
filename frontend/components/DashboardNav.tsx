"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const base: React.CSSProperties = {
  padding: "0.5rem 0.85rem",
  borderRadius: 8,
  fontWeight: 500,
};

export function DashboardNav() {
  const pathname = usePathname();
  const isDash = pathname === "/dashboard";
  const isSub = pathname?.startsWith("/dashboard/subscription");

  const link = (href: string, label: string, active: boolean) => (
    <Link
      href={href}
      style={{
        ...base,
        color: active ? "var(--text)" : "var(--muted)",
        background: active ? "rgba(61, 156, 240, 0.12)" : "transparent",
        border: active ? "1px solid var(--accent-dim)" : "1px solid transparent",
      }}
    >
      {label}
    </Link>
  );

  return (
    <nav
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "0.75rem 1.25rem",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        flexWrap: "wrap",
      }}
    >
      <Link href="/dashboard" style={{ fontWeight: 700, marginRight: "auto", color: "var(--text)" }}>
        SEO Lens
      </Link>
      {link("/dashboard", "Overview", isDash)}
      {link("/dashboard/subscription", "Subscription", !!isSub)}
    </nav>
  );
}
