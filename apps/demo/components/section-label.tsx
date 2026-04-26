"use client";

import { motion } from "framer-motion";

interface SectionLabelProps {
  step: string;
  title: string;
  subtitle: string;
  color: string;
}

export function SectionLabel({ step, title, subtitle, color }: SectionLabelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.7 }}
      className="text-center mb-16"
    >
      <div
        className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase mb-4"
        style={{
          color,
          background: `${color}15`,
          border: `1px solid ${color}30`,
        }}
      >
        {step}
      </div>
      <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
        {title}
      </h2>
      <p className="text-lg text-slate-400 max-w-xl mx-auto">{subtitle}</p>
    </motion.div>
  );
}
