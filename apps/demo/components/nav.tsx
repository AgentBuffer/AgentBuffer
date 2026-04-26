"use client";

import { motion, useScroll, useTransform } from "framer-motion";
import { Brain } from "lucide-react";

const SECTIONS = [
  { id: "hero", label: "Home" },
  { id: "context-engine", label: "Context Engine" },
  { id: "delegation", label: "Delegation" },
  { id: "deployment", label: "Deployment" },
];

export function Nav() {
  const { scrollYProgress } = useScroll();
  const bgOpacity = useTransform(scrollYProgress, [0, 0.05], [0, 1]);

  return (
    <motion.header
      className="fixed top-0 inset-x-0 z-50"
      style={{ "--bg-opacity": bgOpacity } as React.CSSProperties}
    >
      <motion.div
        className="glass border-b border-glass-border"
        style={{ opacity: bgOpacity }}
      />
      <nav className="relative max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
        <a href="#hero" className="flex items-center gap-2 group">
          <div className="h-8 w-8 rounded-lg border-2 border-brand-cyan bg-surface-1 flex items-center justify-center group-hover:glow-cyan transition-shadow">
            <Brain className="h-4 w-4 text-brand-cyan" />
          </div>
          <span className="font-bold text-white text-sm tracking-wide">
            AgentBuffer
          </span>
        </a>
        <div className="hidden md:flex items-center gap-1">
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white rounded-md hover:bg-white/5 transition-colors"
            >
              {s.label}
            </a>
          ))}
        </div>
        <a
          href="#context-engine"
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-brand-cyan/10 text-brand-cyan border border-brand-cyan/20 hover:bg-brand-cyan/20 transition-colors"
        >
          See How It Works
        </a>
      </nav>
    </motion.header>
  );
}
