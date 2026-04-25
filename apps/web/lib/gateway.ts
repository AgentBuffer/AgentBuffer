import type {
  ContentSlot,
  BrandKit,
  AgentEnvelope,
  RankedSlot,
  PublishResult,
  Platform,
  CalendarResponse,
} from "@/lib/types/models";

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://localhost:8000";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

function authHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

// ─── Mock Data ───────────────────────────────────────────────

const MOCK_BRAND: BrandKit = {
  brand_id: "brand-001",
  org_id: "org-001",
  name: "lumen.coffee",
  tagline: "Light up your morning",
  voice_description:
    "Warm, artisan, approachable. We speak like a knowledgeable barista who genuinely loves their craft.",
  target_audience: "Urban professionals aged 25-40 who appreciate specialty coffee",
  color_palette: ["#2C1810", "#D4A574", "#F5F0EB", "#8B4513"],
  logo_url: null,
  sample_captions: [
    "Every cup tells a story. Today's single-origin from Ethiopia has notes of blueberry and dark chocolate.",
    "Rise and grind (literally). Our new cold brew is steeped for 18 hours for maximum smoothness.",
  ],
  industry: "Coffee & Beverage",
};

const MOCK_SLOTS: ContentSlot[] = [
  {
    slot_id: "slot-001",
    slot_number: 1,
    caption:
      "Every morning deserves a moment of ritual. Our single-origin Ethiopian pour-over brings you there.",
    image_prompt:
      "Artisan coffee pour-over in warm morning light, steam rising, minimalist cafe aesthetic",
    platform: "linkedin" as Platform,
    scheduled_for: "2026-04-28T09:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.5, reasoning: "Perfectly captures lumen's warm, artisan tone" },
      { axis: "Visual Coherence", score: 4.0, reasoning: "Pour-over imagery aligns with brand aesthetic" },
      { axis: "Platform Fit", score: 4.2, reasoning: "Professional tone suitable for LinkedIn" },
      { axis: "Audience Relevance", score: 4.3, reasoning: "Appeals to specialty coffee enthusiasts" },
      { axis: "Originality", score: 4.0, reasoning: "Ritual angle is fresh" },
    ],
    critic_average: 4.2,
    critic_summary: "Strong brand alignment with engaging ritual narrative.",
  },
  {
    slot_id: "slot-002",
    slot_number: 2,
    caption:
      "Behind the beans: Our roaster Marco shares why he chose a light roast for this week's blend. Thread below.",
    image_prompt:
      "Coffee roaster working with beans in artisan roastery, warm industrial lighting",
    platform: "x" as Platform,
    scheduled_for: "2026-04-28T12:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 3.8, reasoning: "Good behind-the-scenes approach" },
      { axis: "Visual Coherence", score: 3.9, reasoning: "Roastery setting fits brand" },
      { axis: "Platform Fit", score: 4.0, reasoning: "Thread format works well on X" },
      { axis: "Audience Relevance", score: 3.7, reasoning: "Niche but engaged audience" },
      { axis: "Originality", score: 3.6, reasoning: "Behind-the-scenes is common but executed well" },
    ],
    critic_average: 3.8,
    critic_summary: "Solid behind-the-scenes content with good platform fit.",
  },
  {
    slot_id: "slot-003",
    slot_number: 3,
    caption: "Start your day right with great coffee! Buy now and get 10% off! #coffee #morning",
    image_prompt: "Generic coffee cup on white background with sale text overlay",
    platform: "instagram" as Platform,
    scheduled_for: "2026-04-29T08:00:00Z",
    image_url: null,
    status: "rejected",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 3.0, reasoning: "Too salesy, doesn't match lumen's artisan positioning" },
      { axis: "Visual Coherence", score: 2.8, reasoning: "Generic stock-photo feel contradicts brand aesthetic" },
      { axis: "Platform Fit", score: 3.5, reasoning: "IG-appropriate but hashtag-heavy" },
      { axis: "Audience Relevance", score: 3.4, reasoning: "Discount angle undercuts premium positioning" },
      { axis: "Originality", score: 3.3, reasoning: "Very generic, could be any coffee brand" },
    ],
    critic_average: 3.2,
    critic_summary:
      "Caption is too generic and salesy. Doesn't reflect lumen's artisan positioning. The discount angle undercuts the premium brand image.",
  },
  {
    slot_id: "slot-004",
    slot_number: 4,
    caption:
      "Coffee is a conversation starter. Our new downtown cafe was designed to feel like your living room, but better.",
    image_prompt:
      "Cozy modern cafe interior with warm lighting, people having conversations over coffee",
    platform: "linkedin" as Platform,
    scheduled_for: "2026-04-29T10:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.2, reasoning: "Warm and inviting, on-brand" },
      { axis: "Visual Coherence", score: 4.0, reasoning: "Cafe interior reinforces community feel" },
      { axis: "Platform Fit", score: 4.1, reasoning: "Business-casual tone for LinkedIn" },
      { axis: "Audience Relevance", score: 4.0, reasoning: "Resonates with urban professionals" },
      { axis: "Originality", score: 4.2, reasoning: "'Living room but better' is a nice hook" },
    ],
    critic_average: 4.1,
    critic_summary: "Strong community-focused message with good LinkedIn fit.",
  },
  {
    slot_id: "slot-005",
    slot_number: 5,
    caption:
      "Cold brew season is here. 18 hours of patience for one sip of perfection. Available at all locations starting Monday.",
    image_prompt:
      "Cold brew coffee being poured into glass with ice, condensation on glass, summer light",
    platform: "x" as Platform,
    scheduled_for: "2026-04-30T11:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.6, reasoning: "Poetic and craft-focused, peak lumen voice" },
      { axis: "Visual Coherence", score: 4.5, reasoning: "Cold brew pour is visually striking" },
      { axis: "Platform Fit", score: 4.4, reasoning: "Concise, punchy — perfect for X" },
      { axis: "Audience Relevance", score: 4.5, reasoning: "Seasonal excitement drives engagement" },
      { axis: "Originality", score: 4.5, reasoning: "'18 hours of patience' is a memorable line" },
    ],
    critic_average: 4.5,
    critic_summary: "Excellent craft-forward messaging. Top-performing slot.",
  },
  {
    slot_id: "slot-006",
    slot_number: 6,
    caption:
      "Meet the farmers who make your morning possible. This month's spotlight: the Guji cooperative in southern Ethiopia.",
    image_prompt:
      "Ethiopian coffee farmers in lush green coffee plantation, warm documentary style",
    platform: "linkedin" as Platform,
    scheduled_for: "2026-04-30T09:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.3, reasoning: "Thoughtful, educational — on-brand" },
      { axis: "Visual Coherence", score: 4.1, reasoning: "Documentary style suits the story" },
      { axis: "Platform Fit", score: 4.2, reasoning: "LinkedIn audience appreciates supply chain stories" },
      { axis: "Audience Relevance", score: 4.0, reasoning: "Appeals to ethically-minded consumers" },
      { axis: "Originality", score: 4.4, reasoning: "Farm-to-cup narrative with specific detail" },
    ],
    critic_average: 4.2,
    critic_summary: "Strong ethical narrative with specific sourcing details.",
  },
  {
    slot_id: "slot-007",
    slot_number: 7,
    caption:
      "Sunday slow-down. No rush, no to-do list. Just you and a perfectly brewed cup. What are you sipping?",
    image_prompt:
      "Peaceful Sunday morning scene, person relaxing with coffee by a window, soft natural light",
    platform: "instagram" as Platform,
    scheduled_for: "2026-05-01T10:00:00Z",
    image_url: null,
    status: "approved",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.1, reasoning: "Relaxed, inviting — very lumen" },
      { axis: "Visual Coherence", score: 4.0, reasoning: "Cozy window scene matches brand mood" },
      { axis: "Platform Fit", score: 4.3, reasoning: "Engagement question drives IG comments" },
      { axis: "Audience Relevance", score: 3.9, reasoning: "Lifestyle content resonates broadly" },
      { axis: "Originality", score: 3.7, reasoning: "Sunday coffee is common but well-executed" },
    ],
    critic_average: 4.0,
    critic_summary: "Good lifestyle content with strong engagement hook.",
  },
  {
    slot_id: "slot-008",
    slot_number: 8,
    caption:
      "POV: You walk into a coffee shop and the barista already knows your order. That's the lumen experience.",
    image_prompt:
      "First-person POV entering a warm coffee shop, barista waving, cinematic vertical video",
    platform: "tiktok" as Platform,
    scheduled_for: "2026-04-30T18:00:00Z",
    image_url: null,
    status: "pending",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.0, reasoning: "Casual, relatable — fits TikTok voice" },
      { axis: "Visual Coherence", score: 3.8, reasoning: "POV format is on-trend" },
      { axis: "Platform Fit", score: 4.5, reasoning: "Perfect TikTok format" },
      { axis: "Audience Relevance", score: 4.2, reasoning: "Younger audience cross-sell" },
      { axis: "Originality", score: 3.9, reasoning: "POV trend is popular but well-executed" },
    ],
    critic_average: 4.08,
    critic_summary: "Strong TikTok-native content with good engagement potential.",
  },
  {
    slot_id: "slot-009",
    slot_number: 9,
    caption:
      "Monday motivation: Your coffee order says a lot about you. What's yours?",
    image_prompt: "Coffee cups lineup flat lay with personality labels",
    platform: "instagram" as Platform,
    scheduled_for: "2026-04-28T16:00:00Z",
    image_url: null,
    status: "published",
    critic_scores: [
      { axis: "Brand Voice Alignment", score: 4.1, reasoning: "Engaging and on-brand" },
      { axis: "Visual Coherence", score: 4.0, reasoning: "Flat lay is Instagram-classic" },
      { axis: "Platform Fit", score: 4.3, reasoning: "Poll-style IG content" },
      { axis: "Audience Relevance", score: 4.0, reasoning: "Broad appeal" },
      { axis: "Originality", score: 3.5, reasoning: "Common format but well-done" },
    ],
    critic_average: 3.98,
    critic_summary: "Solid engagement bait with good brand alignment.",
    engagement: {
      likes: 342,
      shares: 28,
      comments: 67,
      reach: 4200,
      engagement_rate: 10.4,
    },
  },
];

const MOCK_MESSAGES: AgentEnvelope[] = [
  {
    id: "msg-001",
    from_agent: "strategist",
    to_agent: "critic",
    envelope_type: "slate_proposal",
    payload: { slate_id: "slate-001", slot_count: 7 },
    signature: "0xab3f...e721",
    created_at: "2026-04-28T14:14:00Z",
  },
  {
    id: "msg-002",
    from_agent: "critic",
    to_agent: "strategist",
    envelope_type: "rejection_notice",
    payload: { rejected_slots: [3], reason: "Below 3.5 threshold" },
    signature: "0xcd91...f482",
    created_at: "2026-04-28T14:14:30Z",
  },
  {
    id: "msg-003",
    from_agent: "strategist",
    to_agent: "critic",
    envelope_type: "slate_revision",
    payload: { slate_id: "slate-001", revised_slots: [3] },
    signature: "0xef22...a193",
    created_at: "2026-04-28T14:15:00Z",
  },
  {
    id: "msg-004",
    from_agent: "critic",
    to_agent: "publisher",
    envelope_type: "full_approval",
    payload: { slate_id: "slate-001", approved_count: 7 },
    signature: "0x1a44...b304",
    created_at: "2026-04-28T14:15:30Z",
  },
  {
    id: "msg-005",
    from_agent: "publisher",
    to_agent: "ledger",
    envelope_type: "publish_result",
    payload: { published: 5, queued: 1, failed: 0 },
    signature: "0x3b77...c815",
    created_at: "2026-04-28T14:16:00Z",
  },
];

// ─── Calendar helpers ────────────────────────────────────────

function _mockMondayOf(date: Date): string {
  const d = new Date(date);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
}

function _filterSlotsByWeek(
  slots: ContentSlot[],
  weekStart: string,
): ContentSlot[] {
  const start = new Date(weekStart + "T00:00:00Z");
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + 7);
  return slots.filter((s) => {
    const d = new Date(s.scheduled_for);
    return d >= start && d < end;
  });
}

// ─── API Functions ───────────────────────────────────────────

export async function fetchCalendar(
  brandId: string,
  weekStart?: string,
  token?: string,
): Promise<CalendarResponse> {
  const ws = weekStart ?? _mockMondayOf(new Date());
  if (USE_MOCK) {
    return {
      brand_id: MOCK_BRAND.brand_id,
      week_start: ws,
      posts: _filterSlotsByWeek(MOCK_SLOTS, ws),
    };
  }
  const url = `${GATEWAY_URL}/brands/${brandId}/calendar?week_start=${ws}`;
  const res = await fetch(url, { headers: authHeaders(token) });
  if (!res.ok) return { brand_id: brandId, week_start: ws, posts: [] };
  return res.json();
}

export async function approveSlot(
  slotId: string,
  token?: string,
): Promise<void> {
  if (USE_MOCK) return;
  const res = await fetch(`${GATEWAY_URL}/api/slots/${slotId}/approve`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    console.error(`Failed to approve slot ${slotId}: ${res.status}`);
    throw new Error(`Failed to approve slot: ${res.statusText}`);
  }
}

export async function skipSlot(
  slotId: string,
  token?: string,
): Promise<void> {
  if (USE_MOCK) return;
  const res = await fetch(`${GATEWAY_URL}/api/slots/${slotId}/skip`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    console.error(`Failed to skip slot ${slotId}: ${res.status}`);
    throw new Error(`Failed to skip slot: ${res.statusText}`);
  }
}

export async function regenerateSlot(
  slotId: string,
  token?: string,
): Promise<void> {
  if (USE_MOCK) return;
  const res = await fetch(`${GATEWAY_URL}/api/slots/${slotId}/regenerate`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    console.error(`Failed to regenerate slot ${slotId}: ${res.status}`);
    throw new Error(`Failed to regenerate slot: ${res.statusText}`);
  }
}

export async function addManualPost(
  post: {
    platform: string;
    scheduled_for: string;
    content_text: string;
  },
  token?: string,
): Promise<ContentSlot | null> {
  if (USE_MOCK) return null;
  const res = await fetch(`${GATEWAY_URL}/api/slots/manual`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(post),
  });
  if (!res.ok) {
    console.error(`Failed to add manual post: ${res.status}`);
    throw new Error(`Failed to add manual post: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchBrand(token?: string): Promise<BrandKit | null> {
  if (USE_MOCK) return MOCK_BRAND;
  const res = await fetch(`${GATEWAY_URL}/api/brands`, {
    headers: authHeaders(token),
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data[0] ?? null;
}

export async function fetchSlots(token?: string): Promise<ContentSlot[]> {
  if (USE_MOCK) return MOCK_SLOTS;
  const res = await fetch(`${GATEWAY_URL}/api/slots`, {
    headers: authHeaders(token),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchMessages(token?: string): Promise<AgentEnvelope[]> {
  if (USE_MOCK) return MOCK_MESSAGES;
  const res = await fetch(`${GATEWAY_URL}/api/messages`, {
    headers: authHeaders(token),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function rankSlots(
  slotIds: string[],
  token?: string
): Promise<RankedSlot[]> {
  if (USE_MOCK) {
    return [
      { slot_id: "slot-001", rank: 1, reasoning: "Strong brand voice alignment with ritual narrative." },
      { slot_id: "slot-005", rank: 2, reasoning: "Authentic craft-forward messaging drives engagement." },
    ];
  }
  const res = await fetch(`${GATEWAY_URL}/api/rank-slots`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ slot_ids: slotIds }),
  });
  if (!res.ok) return [];
  return res.json();
}

export async function triggerPublish(
  slotIds: string[],
  token?: string
): Promise<PublishResult[]> {
  if (USE_MOCK) {
    return slotIds.map((id) => ({
      slot_id: id,
      platform: MOCK_SLOTS.find((s) => s.slot_id === id)?.platform ?? ("linkedin" as Platform),
      success: true,
      permalink: `https://linkedin.com/posts/lumen-coffee_${id}`,
      error: null,
      idempotency_key: `idem-${id}-${Date.now()}`,
    }));
  }
  const res = await fetch(`${GATEWAY_URL}/api/trigger-publish`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ slot_ids: slotIds }),
  });
  if (!res.ok) return [];
  return res.json();
}
