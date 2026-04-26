"use client";

import { motion } from "framer-motion";
import { ArrowDown, Sparkles, Zap, Shield } from "lucide-react";

const FLOATERS = [
  { icon: Sparkles, x: "15%", y: "20%", delay: 0, color: "#06b6d4" },
  { icon: Zap, x: "80%", y: "30%", delay: 0.5, color: "#a855f7" },
  { icon: Shield, x: "70%", y: "70%", delay: 1, color: "#10b981" },
  { icon: Sparkles, x: "25%", y: "75%", delay: 1.5, color: "#f59e0b" },
];

export function Hero() {
  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-grid"
    >
      {/* Radial gradient overlay */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.08)_0%,transparent_70%)]" />

      {/* Floating icons */}
      {FLOATERS.map((f, i) => (
        <motion.div
          key={i}
          className="absolute opacity-20"
          style={{ left: f.x, top: f.y }}
          animate={{
            y: [0, -20, 0],
            rotate: [0, 10, -10, 0],
          }}
          transition={{
            duration: 6,
            delay: f.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          <f.icon className="h-8 w-8" style={{ color: f.color }} />
        </motion.div>
      ))}

      <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass mb-8"
        >
          <span className="h-2 w-2 rounded-full bg-brand-emerald animate-pulse" />
          <span className="text-xs font-medium text-slate-300">
            Autonomous AI Marketing Platform
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1]"
        >
          <span className="text-white">Your Brand.</span>
          <br />
          <span className="bg-gradient-to-r from-brand-cyan via-brand-purple to-brand-emerald bg-clip-text text-transparent">
            Our Agents.
          </span>
          <br />
          <span className="text-white">Zero Effort.</span>
        </motion.h1>

        {/* Sub-headline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="mt-6 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed"
        >
          Feed us your brand — we deploy a swarm of specialized AI agents that
          create, critique, and publish content across every platform.
          Autonomously.
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="mt-10 flex items-center justify-center gap-4"
        >
          <a
            href="#context-engine"
            className="group relative px-8 py-3 rounded-xl bg-brand-cyan text-surface-0 font-semibold text-sm hover:shadow-[0_0_30px_rgba(6,182,212,0.4)] transition-all duration-300"
          >
            Watch the Demo
            <span className="absolute inset-0 rounded-xl bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="mt-20"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <ArrowDown className="h-5 w-5 text-slate-500 mx-auto" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
