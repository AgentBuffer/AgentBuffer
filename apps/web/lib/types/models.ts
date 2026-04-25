export enum Platform {
  LINKEDIN = "linkedin",
  X = "x",
  INSTAGRAM = "instagram",
  TIKTOK = "tiktok",
}

export interface BrandKit {
  brand_id: string;
  org_id: string;
  name: string;
  tagline: string;
  voice_description: string;
  target_audience: string;
  color_palette: string[];
  logo_url: string | null;
  sample_captions: string[];
  industry: string;
}

export interface ContentSlot {
  slot_id: string;
  slot_number: number;
  caption: string;
  image_prompt: string;
  platform: Platform;
  scheduled_for: string;
  image_url: string | null;
  video_url?: string | null;
  status:
    | "draft"
    | "proposed"
    | "rejected"
    | "approved"
    | "published"
    | "failed"
    | "pending"
    | "skipped";
  critic_scores?: CriticScore[];
  critic_average?: number;
  critic_summary?: string;
  note?: string;
  engagement?: EngagementMetrics;
}

export interface Slate {
  slate_id: string;
  brand_id: string;
  org_id: string;
  slots: ContentSlot[];
  generation_context: string;
}

export interface CriticScore {
  axis: string;
  score: number;
  reasoning: string;
}

export interface CriticVerdict {
  slot_id: string;
  scores: CriticScore[];
  average: number;
  approved: boolean;
  summary: string;
}

export interface PublishResult {
  slot_id: string;
  platform: Platform;
  success: boolean;
  permalink: string | null;
  error: string | null;
  idempotency_key: string;
}

export interface AgentEnvelope {
  id: string;
  from_agent: "strategist" | "critic" | "publisher";
  to_agent: string;
  envelope_type: string;
  payload: Record<string, unknown>;
  signature: string;
  created_at: string;
}

export interface RankedSlot {
  slot_id: string;
  rank: number;
  reasoning: string;
}

export interface EngagementMetrics {
  likes: number;
  shares: number;
  comments: number;
  reach: number;
  engagement_rate: number;
}

export interface CalendarResponse {
  brand_id: string;
  week_start: string;
  posts: ContentSlot[];
}
