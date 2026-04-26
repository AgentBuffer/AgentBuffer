/* ── Mock data powering the interactive demo ─────────────────────────── */

export interface InputMaterial {
  id: string;
  label: string;
  icon: "file-text" | "globe" | "palette" | "video" | "image";
  color: string;
}

export const INPUT_MATERIALS: InputMaterial[] = [
  { id: "pdf", label: "Brand Guidelines.pdf", icon: "file-text", color: "#06b6d4" },
  { id: "web", label: "company-website.com", icon: "globe", color: "#a855f7" },
  { id: "style", label: "Style Reference Pack", icon: "palette", color: "#f59e0b" },
  { id: "video", label: "Past Campaign Videos", icon: "video", color: "#f43f5e" },
  { id: "social", label: "Social Media Profiles", icon: "image", color: "#10b981" },
];

export interface BlueprintItem {
  label: string;
  value: string;
}

export const BLUEPRINT_ITEMS: BlueprintItem[] = [
  { label: "Brand Voice", value: "Warm, artisan, approachable" },
  { label: "Target Audience", value: "Urban professionals, 25-40" },
  { label: "Color Palette", value: "#2C1810 · #D4A574 · #F5F0EB" },
  { label: "Content Pillars", value: "Craft · Community · Quality" },
  { label: "Tone Keywords", value: "Authentic · Premium · Inviting" },
];

export interface SubAgent {
  id: string;
  name: string;
  role: string;
  icon: "pen-tool" | "video" | "image" | "bar-chart-3" | "send";
  color: string;
  tasks: string[];
}

export const SUB_AGENTS: SubAgent[] = [
  {
    id: "copywriter",
    name: "Copywriter",
    role: "Caption & copy generation",
    icon: "pen-tool",
    color: "#06b6d4",
    tasks: ["LinkedIn thought-leader post", "Instagram carousel caption", "X thread (5 tweets)"],
  },
  {
    id: "video-editor",
    name: "Video Editor",
    role: "Short-form video creation",
    icon: "video",
    color: "#a855f7",
    tasks: ["TikTok 15s product reel", "Instagram Stories teaser", "YouTube Shorts intro"],
  },
  {
    id: "designer",
    name: "Graphic Designer",
    role: "Visual asset production",
    icon: "image",
    color: "#10b981",
    tasks: ["Carousel slide deck (5 slides)", "Story template set", "Post graphic with quote"],
  },
  {
    id: "analyst",
    name: "Performance Analyst",
    role: "Engagement optimization",
    icon: "bar-chart-3",
    color: "#f59e0b",
    tasks: ["Best-time-to-post analysis", "Hashtag strategy", "A/B caption variants"],
  },
  {
    id: "publisher",
    name: "Publisher",
    role: "Cross-platform deployment",
    icon: "send",
    color: "#f43f5e",
    tasks: ["Schedule to Instagram", "Schedule to LinkedIn", "Schedule to X & TikTok"],
  },
];

export interface CalendarPost {
  id: string;
  day: string;
  time: string;
  platform: "instagram" | "linkedin" | "x" | "tiktok";
  type: "image" | "video" | "carousel" | "text";
  caption: string;
  status: "generating" | "ready" | "deploying" | "live";
  agentId: string;
}

export const CALENDAR_POSTS: CalendarPost[] = [
  {
    id: "p1",
    day: "Mon",
    time: "9:00 AM",
    platform: "linkedin",
    type: "text",
    caption: "Every morning deserves a moment of ritual...",
    status: "ready",
    agentId: "copywriter",
  },
  {
    id: "p2",
    day: "Mon",
    time: "12:00 PM",
    platform: "instagram",
    type: "carousel",
    caption: "Behind the beans: Meet our roaster Marco",
    status: "ready",
    agentId: "designer",
  },
  {
    id: "p3",
    day: "Tue",
    time: "10:00 AM",
    platform: "tiktok",
    type: "video",
    caption: "POV: The barista already knows your order",
    status: "ready",
    agentId: "video-editor",
  },
  {
    id: "p4",
    day: "Tue",
    time: "3:00 PM",
    platform: "x",
    type: "text",
    caption: "Cold brew season is here. 18 hours of patience...",
    status: "ready",
    agentId: "copywriter",
  },
  {
    id: "p5",
    day: "Wed",
    time: "8:00 AM",
    platform: "instagram",
    type: "image",
    caption: "Your coffee order says a lot about you",
    status: "ready",
    agentId: "designer",
  },
  {
    id: "p6",
    day: "Wed",
    time: "2:00 PM",
    platform: "linkedin",
    type: "text",
    caption: "Meet the farmers who make your morning possible",
    status: "ready",
    agentId: "copywriter",
  },
  {
    id: "p7",
    day: "Thu",
    time: "11:00 AM",
    platform: "tiktok",
    type: "video",
    caption: "How we roast our single-origin Ethiopian beans",
    status: "ready",
    agentId: "video-editor",
  },
  {
    id: "p8",
    day: "Thu",
    time: "4:00 PM",
    platform: "instagram",
    type: "carousel",
    caption: "5 ways to brew the perfect cup at home",
    status: "ready",
    agentId: "designer",
  },
  {
    id: "p9",
    day: "Fri",
    time: "9:00 AM",
    platform: "x",
    type: "text",
    caption: "Friday ritual: What's in your cup this morning?",
    status: "ready",
    agentId: "copywriter",
  },
  {
    id: "p10",
    day: "Fri",
    time: "5:00 PM",
    platform: "instagram",
    type: "image",
    caption: "Sunday slow-down. Just you and a perfect cup.",
    status: "ready",
    agentId: "designer",
  },
];

export const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  linkedin: "#0A66C2",
  x: "#ffffff",
  tiktok: "#00f2ea",
};

export const PLATFORM_LABELS: Record<string, string> = {
  instagram: "Instagram",
  linkedin: "LinkedIn",
  x: "X",
  tiktok: "TikTok",
};
