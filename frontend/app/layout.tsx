import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { cn } from "@/lib/utils";

const jakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-jakarta",
});

export const metadata: Metadata = {
  title: "Campaign Agent — Autonomous AI Marketing",
  description:
    "Multi-agent autonomous social media campaign system powered by LangGraph + GPT-4o",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ colorScheme: "light", backgroundColor: "#ffffff" }}>
      <body
        className={cn(jakartaSans.className, "min-h-screen")}
        style={{ backgroundColor: "#ffffff", color: "#0f172a" }}
      >
        {/* Top Navigation */}
        <nav
          className="border-b sticky top-0 z-50"
          style={{
            borderColor: "var(--border)",
            background: "rgba(255,255,255,0.95)",
            backdropFilter: "blur(8px)",
          }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              <div className="flex items-center gap-8">
                <Link href="/" className="flex items-center gap-2.5">
                  <div
                    className="w-7 h-7 rounded-md flex items-center justify-center text-white font-bold text-xs tracking-tight"
                    style={{ background: "var(--accent)" }}
                  >
                    CA
                  </div>
                  <span
                    className="font-semibold text-sm tracking-tight"
                    style={{ color: "var(--text)" }}
                  >
                    Campaign Agent
                  </span>
                </Link>
                <div className="hidden sm:flex items-center gap-1">
                  <NavLink href="/">Dashboard</NavLink>
                  <NavLink href="/campaign/new">New Campaign</NavLink>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="text-xs px-2.5 py-1 rounded-md border font-mono font-medium"
                  style={{
                    color: "var(--success)",
                    borderColor: "#bbf7d0",
                    background: "var(--success-light)",
                  }}
                >
                  LangGraph v0.2
                </span>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}

function NavLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="text-sm px-3 py-1.5 rounded-md transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]"
      style={{ color: "var(--text-muted)" }}
    >
      {children}
    </Link>
  );
}
