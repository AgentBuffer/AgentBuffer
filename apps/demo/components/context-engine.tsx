"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  FileText,
  Globe,
  Palette,
  Video,
  Image,
  Check,
  Loader2,
} from "lucide-react";
import { SectionLabel } from "./section-label";
import { INPUT_MATERIALS, BLUEPRINT_ITEMS } from "@/lib/mock-data";

const ICON_MAP: Record<string, React.ElementType> = {
  "file-text": FileText,
  globe: Globe,
  palette: Palette,
  video: Video,
  image: Image,
};

type Phase = "idle" | "ingesting" | "processing" | "complete";

export function ContextEngine() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [ingestedIds, setIngestedIds] = useState<Set<string>>(new Set());

  function startDemo() {
    if (phase !== "idle") return;
    setPhase("ingesting");
    setIngestedIds(new Set());

    INPUT_MATERIALS.forEach((mat, i) => {
      setTimeout(() => {
        setIngestedIds((prev) => new Set([...prev, mat.id]));
        if (i === INPUT_MATERIALS.length - 1) {
          setTimeout(() => setPhase("processing"), 600);
          setTimeout(() => setPhase("complete"), 2600);
        }
      }, (i + 1) * 500);
    });
  }

  function reset() {
    setPhase("idle");
    setIngestedIds(new Set());
  }

  return (
    <section id="context-engine" className="relative py-32 px-6 bg-grid">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(6,182,212,0.06)_0%,transparent_60%)]" />
      <div className="relative max-w-5xl mx-auto">
        <SectionLabel
          step="Step 1"
          title="The Context Engine"
          subtitle="Feed us everything about your brand. Our AI ingests it all and builds a deep understanding."
          color="#06b6d4"
        />

        {/* Interactive visualization */}
        <div className="relative flex flex-col items-center">
          {/* Input materials ring */}
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {INPUT_MATERIALS.map((mat, i) => {
              const Icon = ICON_MAP[mat.icon];
              const ingested = ingestedIds.has(mat.id);
              return (
                <motion.div
                  key={mat.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="relative"
                >
                  <motion.div
                    className="glass rounded-xl px-4 py-3 flex items-center gap-3 cursor-default"
                    animate={
                      ingested
                        ? { opacity: 0.3, scale: 0.9, y: 20 }
                        : phase === "ingesting" && !ingested
                          ? { scale: [1, 1.05, 1] }
                          : {}
                    }
                    transition={{ duration: 0.4 }}
                    whileHover={phase === "idle" ? { scale: 1.05, y: -2 } : {}}
                  >
                    <div
                      className="h-8 w-8 rounded-lg flex items-center justify-center"
                      style={{ background: `${mat.color}20` }}
                    >
                      <Icon className="h-4 w-4" style={{ color: mat.color }} />
                    </div>
                    <span className="text-sm font-medium text-slate-300">
                      {mat.label}
                    </span>
                    {ingested && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-brand-cyan flex items-center justify-center"
                      >
                        <Check className="h-3 w-3 text-surface-0" />
                      </motion.div>
                    )}
                  </motion.div>

                  {/* Data stream particle */}
                  <AnimatePresence>
                    {ingested && (
                      <motion.div
                        initial={{ opacity: 1, y: 0 }}
                        animate={{ opacity: 0, y: 80 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.6 }}
                        className="absolute left-1/2 -translate-x-1/2 top-full mt-2"
                      >
                        <div
                          className="h-2 w-2 rounded-full"
                          style={{ background: mat.color, boxShadow: `0 0 10px ${mat.color}` }}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>

          {/* Central AI node */}
          <motion.div
            className="relative mb-12"
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            {/* Pulse rings */}
            {(phase === "ingesting" || phase === "processing") && (
              <>
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-brand-cyan/30"
                  animate={{ scale: [1, 1.8], opacity: [0.5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  style={{ margin: "-20px" }}
                />
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-brand-cyan/20"
                  animate={{ scale: [1, 2.2], opacity: [0.3, 0] }}
                  transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                  style={{ margin: "-20px" }}
                />
              </>
            )}

            <motion.div
              className="h-24 w-24 rounded-full flex items-center justify-center relative"
              style={{
                background:
                  phase === "complete"
                    ? "linear-gradient(135deg, #06b6d4, #a855f7)"
                    : "linear-gradient(135deg, rgba(6,182,212,0.2), rgba(168,85,247,0.2))",
                boxShadow:
                  phase === "processing" || phase === "complete"
                    ? "0 0 40px rgba(6,182,212,0.4), 0 0 80px rgba(168,85,247,0.2)"
                    : "0 0 20px rgba(6,182,212,0.1)",
              }}
              animate={
                phase === "processing"
                  ? { rotate: 360 }
                  : {}
              }
              transition={
                phase === "processing"
                  ? { duration: 3, repeat: Infinity, ease: "linear" }
                  : {}
              }
            >
              {phase === "processing" ? (
                <Loader2 className="h-10 w-10 text-white animate-spin" />
              ) : (
                <Brain className="h-10 w-10 text-white" />
              )}
            </motion.div>

            {/* Status label */}
            <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
              <span className="text-xs font-mono tracking-wide text-slate-400">
                {phase === "idle" && "Ready to ingest"}
                {phase === "ingesting" && "Ingesting materials..."}
                {phase === "processing" && "Building brand context..."}
                {phase === "complete" && "Context Blueprint ready"}
              </span>
            </div>
          </motion.div>

          {/* Brand Context Blueprint output */}
          <AnimatePresence>
            {phase === "complete" && (
              <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md mt-8"
              >
                <div className="glass-highlight rounded-2xl p-6 glow-cyan">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-brand-cyan to-brand-purple flex items-center justify-center">
                      <Brain className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">
                        Brand Context Blueprint
                      </h3>
                      <p className="text-xs text-slate-400">
                        AI-extracted identity profile
                      </p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {BLUEPRINT_ITEMS.map((item, i) => (
                      <motion.div
                        key={item.label}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex items-baseline justify-between gap-4 py-1.5 border-b border-white/5 last:border-0"
                      >
                        <span className="text-xs font-mono text-slate-500 uppercase tracking-wider shrink-0">
                          {item.label}
                        </span>
                        <span className="text-sm text-slate-200 text-right">
                          {item.value}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action button */}
          <motion.button
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            onClick={phase === "complete" ? reset : startDemo}
            disabled={phase === "ingesting" || phase === "processing"}
            className="mt-12 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background:
                phase === "complete"
                  ? "rgba(168,85,247,0.15)"
                  : "rgba(6,182,212,0.15)",
              color: phase === "complete" ? "#a855f7" : "#06b6d4",
              border: `1px solid ${phase === "complete" ? "rgba(168,85,247,0.3)" : "rgba(6,182,212,0.3)"}`,
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
          >
            {phase === "idle" && "▶  Start Ingestion"}
            {phase === "ingesting" && "Ingesting..."}
            {phase === "processing" && "Processing..."}
            {phase === "complete" && "↻  Reset Demo"}
          </motion.button>
        </div>
      </div>
    </section>
  );
}
