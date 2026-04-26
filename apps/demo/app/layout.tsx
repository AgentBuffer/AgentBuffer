import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentBuffer — AI Marketing Platform Demo",
  description:
    "See how AgentBuffer transforms your brand into an autonomous content machine with AI agents.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="antialiased">
      <body className="bg-surface-0 text-slate-200">{children}</body>
    </html>
  );
}
