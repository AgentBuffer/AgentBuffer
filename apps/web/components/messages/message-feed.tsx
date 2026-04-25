"use client";

import { useEffect, useRef, useState } from "react";
import { EnvelopeCard } from "./envelope-card";
import { fetchMessages } from "@/lib/gateway";
import type { AgentEnvelope } from "@/lib/types/models";

export function MessageFeed() {
  const [messages, setMessages] = useState<AgentEnvelope[]>([]);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;

    async function poll() {
      const data = await fetchMessages();
      if (active) {
        setMessages(data);
        setLoading(false);
      }
    }

    poll();
    const interval = setInterval(poll, 3000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-neutral-400">
        Loading agent activity...
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-neutral-400">
        No agent activity yet. Onboard a brand to get started.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {messages.map((msg) => (
        <EnvelopeCard key={msg.id} envelope={msg} />
      ))}
      <div ref={bottomRef} />
      <p className="text-center text-xs text-neutral-400">
        Auto-refreshing every 3s
      </p>
    </div>
  );
}
