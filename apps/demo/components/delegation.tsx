"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  PenTool,
  Video,
  Image,
  BarChart3,
  Send,
  ChevronRight,
} from "lucide-react";
import { SectionLabel } from "./section-label";
import { SUB_AGENTS } from "@/lib/mock-data";

const ICON_MAP: Record<string, React.ElementType> = {
  "pen-tool": PenTool,
  video: Video,
  image: Image,
  "bar-chart-3": BarChart3,
  send: Send,
};

type Phase = "idle" | "spawning" | "routing" | "active";

export function Delegation() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [spawnedIds, setSpawnedIds] = useState<Set<string>>(new Set());
  const [activeAgent, setActiveAgent] = useState<string | null>(null);

  function startDemo() {
    if (phase !== "idle") return;
    setPhase("spawning");
    setSpawnedIds(new Set());

    SUB_AGENTS.forEach((agent, i) => {
      setTimeout(() => {
        setSpawnedIds((prev) => new Set([...prev, agent.id]));
        if (i === SUB_AGENTS.length - 1) {
          setTimeout(() => setPhase("routing"), 400);
          setTimeout(() => setPhase("active"), 1400);
        }
      }, (i + 1) * 350);
    });
  }

  function reset() {
    setPhase("idle");
    setSpawnedIds(new Set());
    setActiveAgent(null);
  }

  return (
    <section id="delegation" className="relative py-32 px-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(168,85,247,0.06)_0%,transparent_60%)]" />
      <div className="relative max-w-5xl mx-auto">
        <SectionLabel
          step="Step 2"
          title="Smart Task Delegation"
          subtitle="The Director spawns specialized AI agents and routes tasks based on your brand context."
          color="#a855f7"
        />

        {/* Hub and spoke visualization */}
        <div className="relative flex flex-col items-center">
          {/* Central hub */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative z-10 mb-4"
          >
            <motion.div
              className="h-20 w-20 rounded-full flex items-center justify-center"
              style={{
                background: "linear-gradient(135deg, rgba(168,85,247,0.3), rgba(6,182,212,0.3))",
                boxShadow: phase !== "idle"
                  ? "0 0 40px rgba(168,85,247,0.3)"
                  : "0 0 20px rgba(168,85,247,0.1)",
              }}
              animate={
                phase === "spawning" || phase === "routing"
                  ? { scale: [1, 1.1, 1] }
                  : {}
              }
              transition={{ duration: 1, repeat: phase === "routing" ? Infinity : 0 }}
            >
              <Brain className="h-8 w-8 text-white" />
            </motion.div>
            <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
              <span className="text-[10px] font-mono text-brand-purple tracking-wider uppercase">
                Marketing Director
              </span>
            </div>
          </motion.div>

          {/* Connection lines + Agent nodes */}
          <div className="relative w-full mt-12">
            {/* Routing lines (SVG) */}
            <svg
              className="absolute top-0 left-0 w-full h-20 pointer-events-none"
              viewBox="0 0 1000 80"
              preserveAspectRatio="none"
            >
              {SUB_AGENTS.map((agent, i) => {
                const x = (i / (SUB_AGENTS.length - 1)) * 800 + 100;
                return (
                  <motion.line
                    key={agent.id}
                    x1="500"
                    y1="0"
                    x2={x}
                    y2="80"
                    stroke={agent.color}
                    strokeWidth="1.5"
                    strokeDasharray="6 4"
                    initial={{ pathLength: 0, opacity: 0 }}
                    animate={
                      spawnedIds.has(agent.id)
                        ? { pathLength: 1, opacity: 0.4 }
                        : { pathLength: 0, opacity: 0 }
                    }
                    transition={{ duration: 0.5 }}
                  />
                );
              })}
            </svg>

            {/* Agent cards */}
            <div className="flex flex-wrap justify-center gap-4 pt-20">
              {SUB_AGENTS.map((agent, i) => {
                const Icon = ICON_MAP[agent.icon];
                const spawned = spawnedIds.has(agent.id);
                const isActive = activeAgent === agent.id;

                return (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, y: 30, scale: 0.9 }}
                    animate={
                      spawned
                        ? { opacity: 1, y: 0, scale: 1 }
                        : { opacity: 0, y: 30, scale: 0.9 }
                    }
                    transition={{ delay: 0.1 * i, type: "spring", stiffness: 200 }}
                    className="relative w-44"
                  >
                    <motion.div
                      className="glass rounded-xl p-4 cursor-pointer relative overflow-hidden"
                      whileHover={{ scale: 1.03, y: -2 }}
                      onClick={() =>
                        phase === "active" &&
                        setActiveAgent(isActive ? null : agent.id)
                      }
                      style={{
                        borderColor: isActive ? `${agent.color}40` : undefined,
                        boxShadow: isActive
                          ? `0 0 20px ${agent.color}30`
                          : undefined,
                      }}
                    >
                      {/* Spawn flash */}
                      {spawned && (
                        <motion.div
                          className="absolute inset-0 rounded-xl"
                          style={{ background: agent.color }}
                          initial={{ opacity: 0.3 }}
                          animate={{ opacity: 0 }}
                          transition={{ duration: 0.5 }}
                        />
                      )}

                      <div className="flex items-center gap-3 mb-2">
                        <div
                          className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0"
                          style={{ background: `${agent.color}20` }}
                        >
                          <Icon
                            className="h-4 w-4"
                            style={{ color: agent.color }}
                          />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-white truncate">
                            {agent.name}
                          </p>
                          <p className="text-[10px] text-slate-500 truncate">
                            {agent.role}
                          </p>
                        </div>
                      </div>

                      {/* Task routing animation */}
                      <AnimatePresence>
                        {phase === "routing" && spawned && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="pt-2 border-t border-white/5">
                              {agent.tasks.map((task, j) => (
                                <motion.div
                                  key={j}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: j * 0.15 }}
                                  className="flex items-center gap-1.5 py-0.5"
                                >
                                  <ChevronRight
                                    className="h-3 w-3 shrink-0"
                                    style={{ color: agent.color }}
                                  />
                                  <span className="text-[10px] text-slate-400 truncate">
                                    {task}
                                  </span>
                                </motion.div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                      {/* Active state — show tasks */}
                      <AnimatePresence>
                        {isActive && phase === "active" && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="pt-2 border-t border-white/5">
                              {agent.tasks.map((task, j) => (
                                <motion.div
                                  key={j}
                                  initial={{ opacity: 0, x: -10 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: j * 0.1 }}
                                  className="flex items-center gap-1.5 py-1"
                                >
                                  <div
                                    className="h-1.5 w-1.5 rounded-full shrink-0"
                                    style={{ background: agent.color }}
                                  />
                                  <span className="text-[10px] text-slate-300">
                                    {task}
                                  </span>
                                </motion.div>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>

                    {/* Status indicator */}
                    {spawned && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex items-center justify-center gap-1 mt-2"
                      >
                        <motion.div
                          className="h-1.5 w-1.5 rounded-full"
                          style={{ background: agent.color }}
                          animate={{ opacity: [1, 0.3, 1] }}
                          transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            delay: i * 0.2,
                          }}
                        />
                        <span className="text-[9px] font-mono text-slate-500">
                          {phase === "active" ? "ACTIVE" : "SPAWNING"}
                        </span>
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Action button */}
          <motion.button
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            onClick={phase === "active" ? reset : startDemo}
            disabled={phase === "spawning" || phase === "routing"}
            className="mt-14 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background:
                phase === "active"
                  ? "rgba(6,182,212,0.15)"
                  : "rgba(168,85,247,0.15)",
              color: phase === "active" ? "#06b6d4" : "#a855f7",
              border: `1px solid ${phase === "active" ? "rgba(6,182,212,0.3)" : "rgba(168,85,247,0.3)"}`,
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
          >
            {phase === "idle" && "▶  Spawn Agents"}
            {phase === "spawning" && "Spawning..."}
            {phase === "routing" && "Routing tasks..."}
            {phase === "active" && "↻  Reset Demo"}
          </motion.button>

          {phase === "active" && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-slate-500 mt-3"
            >
              Click any agent card to see its assigned tasks
            </motion.p>
          )}
        </div>
      </div>
    </section>
  );
}
