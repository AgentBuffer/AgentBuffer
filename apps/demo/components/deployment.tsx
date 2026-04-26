"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar,
  Check,
  Loader2,
  Rocket,
  Sparkles,
  Image,
  Video,
  AlignLeft,
  Layers,
} from "lucide-react";
import { SectionLabel } from "./section-label";
import {
  CALENDAR_POSTS,
  PLATFORM_COLORS,
  PLATFORM_LABELS,
  type CalendarPost,
} from "@/lib/mock-data";

const TYPE_ICONS: Record<string, React.ElementType> = {
  image: Image,
  video: Video,
  text: AlignLeft,
  carousel: Layers,
};

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

type Phase = "idle" | "generating" | "snapping" | "deploying" | "live";

export function Deployment() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [posts, setPosts] = useState<CalendarPost[]>(CALENDAR_POSTS);
  const [deployedCount, setDeployedCount] = useState(0);

  const updatePostStatus = useCallback(
    (id: string, status: CalendarPost["status"]) => {
      setPosts((prev) =>
        prev.map((p) => (p.id === id ? { ...p, status } : p))
      );
    },
    []
  );

  function startDemo() {
    if (phase !== "idle") return;

    // Reset all posts
    setPosts(CALENDAR_POSTS.map((p) => ({ ...p, status: "generating" })));
    setPhase("generating");
    setDeployedCount(0);

    // Phase 1: Generating (posts appear one by one)
    CALENDAR_POSTS.forEach((post, i) => {
      setTimeout(() => {
        updatePostStatus(post.id, "ready");
      }, 800 + i * 200);
    });

    // Phase 2: Snapping into calendar
    setTimeout(() => setPhase("snapping"), 800 + CALENDAR_POSTS.length * 200 + 500);

    // Phase 3: Deploying
    const deployStart = 800 + CALENDAR_POSTS.length * 200 + 1500;
    setTimeout(() => {
      setPhase("deploying");
      CALENDAR_POSTS.forEach((post, i) => {
        setTimeout(() => {
          updatePostStatus(post.id, "deploying");
          setTimeout(() => {
            updatePostStatus(post.id, "live");
            setDeployedCount((c) => c + 1);
          }, 400);
        }, i * 200);
      });
    }, deployStart);

    // Phase 4: All live
    setTimeout(() => {
      setPhase("live");
    }, deployStart + CALENDAR_POSTS.length * 200 + 600);
  }

  function reset() {
    setPhase("idle");
    setPosts(CALENDAR_POSTS);
    setDeployedCount(0);
  }

  const postsByDay = DAYS.map((day) => ({
    day,
    posts: posts.filter((p) => p.day === day),
  }));

  return (
    <section id="deployment" className="relative py-32 px-6 bg-grid">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,rgba(16,185,129,0.06)_0%,transparent_60%)]" />
      <div className="relative max-w-6xl mx-auto">
        <SectionLabel
          step="Step 3"
          title="Generate & Deploy"
          subtitle="Agents deliver content that snaps into your calendar. One click to deploy across all platforms."
          color="#10b981"
        />

        {/* Calendar grid */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="glass rounded-2xl p-6 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-brand-emerald" />
              <h3 className="text-sm font-bold text-white">
                Content Calendar — This Week
              </h3>
            </div>
            <div className="flex items-center gap-2">
              {phase === "deploying" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-amber/10 border border-brand-amber/20"
                >
                  <Loader2 className="h-3 w-3 text-brand-amber animate-spin" />
                  <span className="text-xs font-mono text-brand-amber">
                    Deploying {deployedCount}/{CALENDAR_POSTS.length}
                  </span>
                </motion.div>
              )}
              {phase === "live" && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-emerald/10 border border-brand-emerald/20"
                >
                  <Check className="h-3 w-3 text-brand-emerald" />
                  <span className="text-xs font-mono text-brand-emerald">
                    All {CALENDAR_POSTS.length} posts live!
                  </span>
                </motion.div>
              )}
            </div>
          </div>

          {/* Day columns */}
          <div className="grid grid-cols-5 gap-3">
            {postsByDay.map(({ day, posts: dayPosts }) => (
              <div key={day}>
                <div className="text-center mb-3">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500">
                    {day}
                  </span>
                </div>
                <div className="space-y-2 min-h-[200px]">
                  <AnimatePresence mode="popLayout">
                    {dayPosts.map((post) => {
                      const TypeIcon = TYPE_ICONS[post.type];
                      const platformColor =
                        PLATFORM_COLORS[post.platform] ?? "#fff";
                      return (
                        <motion.div
                          key={post.id}
                          layout
                          initial={
                            phase === "idle"
                              ? { opacity: 1, scale: 1 }
                              : { opacity: 0, scale: 0.8, y: -20 }
                          }
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          transition={{ type: "spring", stiffness: 300, damping: 25 }}
                          className="relative group"
                        >
                          <motion.div
                            className="rounded-lg p-2.5 border transition-colors cursor-default"
                            style={{
                              background:
                                post.status === "live"
                                  ? `${platformColor}08`
                                  : post.status === "deploying"
                                    ? `rgba(245,158,11,0.05)`
                                    : "rgba(255,255,255,0.03)",
                              borderColor:
                                post.status === "live"
                                  ? `${platformColor}25`
                                  : post.status === "deploying"
                                    ? "rgba(245,158,11,0.2)"
                                    : "rgba(255,255,255,0.06)",
                            }}
                            whileHover={{ scale: 1.02 }}
                          >
                            {/* Platform + time */}
                            <div className="flex items-center justify-between mb-1.5">
                              <span
                                className="text-[9px] font-bold uppercase tracking-wider"
                                style={{ color: platformColor }}
                              >
                                {PLATFORM_LABELS[post.platform]}
                              </span>
                              <span className="text-[9px] text-slate-500 font-mono">
                                {post.time}
                              </span>
                            </div>

                            {/* Type icon + caption */}
                            <div className="flex items-start gap-1.5">
                              <TypeIcon className="h-3 w-3 mt-0.5 shrink-0 text-slate-500" />
                              <p className="text-[10px] text-slate-300 leading-tight line-clamp-2">
                                {post.status === "generating" ? (
                                  <span className="text-slate-500 italic">
                                    Generating...
                                  </span>
                                ) : (
                                  post.caption
                                )}
                              </p>
                            </div>

                            {/* Status indicator */}
                            <div className="flex items-center gap-1 mt-1.5">
                              {post.status === "generating" && (
                                <Loader2 className="h-2.5 w-2.5 text-slate-500 animate-spin" />
                              )}
                              {post.status === "ready" && (
                                <Sparkles className="h-2.5 w-2.5 text-brand-cyan" />
                              )}
                              {post.status === "deploying" && (
                                <Rocket className="h-2.5 w-2.5 text-brand-amber" />
                              )}
                              {post.status === "live" && (
                                <Check className="h-2.5 w-2.5 text-brand-emerald" />
                              )}
                              <span
                                className="text-[8px] font-mono uppercase"
                                style={{
                                  color:
                                    post.status === "live"
                                      ? "#10b981"
                                      : post.status === "deploying"
                                        ? "#f59e0b"
                                        : post.status === "ready"
                                          ? "#06b6d4"
                                          : "#64748b",
                                }}
                              >
                                {post.status}
                              </span>
                            </div>
                          </motion.div>

                          {/* Deploy flash effect */}
                          {post.status === "live" && (
                            <motion.div
                              className="absolute inset-0 rounded-lg pointer-events-none"
                              style={{
                                border: `1px solid ${platformColor}`,
                              }}
                              initial={{ opacity: 0.6 }}
                              animate={{ opacity: 0 }}
                              transition={{ duration: 0.8 }}
                            />
                          )}
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Action button */}
        <div className="flex justify-center mt-10">
          <motion.button
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            onClick={phase === "live" ? reset : startDemo}
            disabled={
              phase === "generating" ||
              phase === "snapping" ||
              phase === "deploying"
            }
            className="px-6 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background:
                phase === "live"
                  ? "rgba(6,182,212,0.15)"
                  : "rgba(16,185,129,0.15)",
              color: phase === "live" ? "#06b6d4" : "#10b981",
              border: `1px solid ${phase === "live" ? "rgba(6,182,212,0.3)" : "rgba(16,185,129,0.3)"}`,
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.97 }}
          >
            {phase === "idle" && "▶  Generate & Deploy"}
            {phase === "generating" && "Generating content..."}
            {phase === "snapping" && "Scheduling..."}
            {phase === "deploying" && "Deploying..."}
            {phase === "live" && "↻  Reset Demo"}
          </motion.button>
        </div>
      </div>
    </section>
  );
}
