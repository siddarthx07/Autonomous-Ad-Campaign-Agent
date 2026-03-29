import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { cn } from "@/lib/utils";

const inter = Inter({ subsets: ["latin"] });

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
    <html lang="en">
      <body className={cn(inter.className, "min-h-screen")} style={{ background: "var(--bg)" }}>
        {/* Top Navigation */}
        <nav
          className="border-b sticky top-0 z-50 backdrop-blur-sm"
          style={{ borderColor: "var(--border)", background: "rgba(10,10,15,0.9)" }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-14">
              <div className="flex items-center gap-6">
                <Link href="/" className="flex items-center gap-2 group">
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center text-white font-bold text-xs"
                    style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
                  >
                    CA
                  </div>
                  <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
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
                  className="text-xs px-2 py-1 rounded-full border font-mono"
                  style={{
                    color: "var(--success)",
                    borderColor: "var(--success)",
                    background: "rgba(16,185,129,0.1)",
                  }}
                >
                  ● LangGraph v0.2
                </span>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
      className="text-sm px-3 py-1.5 rounded-md transition-colors hover:text-white"
      style={{ color: "var(--text-muted)" }}
    >
      {children}
    </Link>
  );
}
