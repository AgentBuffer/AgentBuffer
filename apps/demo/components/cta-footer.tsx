"use client";

import { motion } from "framer-motion";
import { ArrowRight, Brain } from "lucide-react";

export function CTAFooter() {
  return (
    <section className="relative py-32 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.1)_0%,transparent_70%)]" />
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative max-w-2xl mx-auto text-center"
      >
        <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-gradient-to-br from-brand-cyan to-brand-purple mb-8 glow-cyan">
          <Brain className="h-8 w-8 text-white" />
        </div>
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Ready to automate
          <br />
          your content?
        </h2>
        <p className="text-lg text-slate-400 mb-10 max-w-md mx-auto">
          Join brands that have replaced their entire content workflow with
          autonomous AI agents.
        </p>
        <motion.a
          href="#hero"
          className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-brand-cyan to-brand-purple text-white font-semibold text-sm hover:shadow-[0_0_40px_rgba(6,182,212,0.3)] transition-shadow"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.97 }}
        >
          Get Early Access
          <ArrowRight className="h-4 w-4" />
        </motion.a>
        <p className="mt-16 text-xs text-slate-600">
          Built with AI agents on the{" "}
          <span className="text-slate-500">Fetch.ai</span> framework
        </p>
      </motion.div>
    </section>
  );
}
