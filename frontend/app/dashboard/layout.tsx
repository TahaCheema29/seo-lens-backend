import { DashboardNav } from "@/components/DashboardNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          borderBottom: "1px solid var(--border)",
          background: "var(--surface)",
        }}
      >
        <DashboardNav />
      </header>
      <main
        style={{
          flex: 1,
          maxWidth: 960,
          margin: "0 auto",
          padding: "1.5rem 1.25rem",
          width: "100%",
        }}
      >
        {children}
      </main>
    </div>
  );
}
