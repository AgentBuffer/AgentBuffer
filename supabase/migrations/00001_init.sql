-- AgentBuffer schema

-- Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Brands (1 per org for demo)
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    name TEXT NOT NULL,
    brand_kit JSONB NOT NULL,
    logo_url TEXT,
    source_pdfs TEXT[],
    social_links JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Content slots (7 per slate)
CREATE TABLE content_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    brand_id UUID REFERENCES brands(id) NOT NULL,
    slate_id UUID NOT NULL,
    slot_number INT NOT NULL,
    caption TEXT,
    image_prompt TEXT,
    image_url TEXT,
    platform TEXT CHECK (platform IN ('linkedin', 'x', 'instagram')),
    status TEXT DEFAULT 'draft'
        CHECK (status IN ('draft', 'proposed', 'rejected', 'approved', 'published', 'failed')),
    critic_scores JSONB,
    publish_result JSONB,
    idempotency_key TEXT UNIQUE,
    scheduled_for TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Agent messages (live feed / ledger)
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    from_agent TEXT NOT NULL CHECK (from_agent IN ('strategist', 'critic', 'publisher')),
    to_agent TEXT NOT NULL,
    envelope_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    signature TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Dead letters (Publisher reliability)
CREATE TABLE dead_letters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    slot_id UUID REFERENCES content_slots(id),
    error_message TEXT,
    error_code TEXT,
    full_payload JSONB,
    retry_count INT DEFAULT 0,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE dead_letters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_isolation" ON organizations
    FOR ALL USING (id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);
CREATE POLICY "org_isolation" ON brands
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);
CREATE POLICY "org_isolation" ON content_slots
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);
CREATE POLICY "org_isolation" ON agent_messages
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);
CREATE POLICY "org_isolation" ON dead_letters
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);

-- Indexes
CREATE INDEX idx_brands_org ON brands(org_id);
CREATE INDEX idx_content_slots_org ON content_slots(org_id);
CREATE INDEX idx_content_slots_brand ON content_slots(brand_id);
CREATE INDEX idx_content_slots_slate ON content_slots(slate_id);
CREATE INDEX idx_agent_messages_org ON agent_messages(org_id);
CREATE INDEX idx_agent_messages_created ON agent_messages(created_at);
CREATE INDEX idx_dead_letters_org ON dead_letters(org_id);
CREATE INDEX idx_dead_letters_resolved ON dead_letters(resolved) WHERE NOT resolved;
