-- Campaign tracking
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    brand_id UUID REFERENCES brands(id) NOT NULL,
    campaign_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    stages JSONB DEFAULT '[]',
    result_summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Performance analytics
CREATE TABLE performance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) NOT NULL,
    post_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    content_type TEXT,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    comments INT DEFAULT 0,
    reach INT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(brand_id, post_id)
);

-- Asset columns on content_slots
ALTER TABLE content_slots ADD COLUMN video_url TEXT;
ALTER TABLE content_slots ADD COLUMN carousel_urls TEXT[];

-- Expand agent_messages from_agent CHECK
ALTER TABLE agent_messages DROP CONSTRAINT agent_messages_from_agent_check;
ALTER TABLE agent_messages ADD CONSTRAINT agent_messages_from_agent_check
    CHECK (from_agent IN (
        'strategist', 'critic', 'publisher', 'video_creator',
        'carousel_creator', 'design_director', 'performance_harvester'
    ));

-- RLS + indexes
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_isolation" ON campaigns
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);

CREATE POLICY "brand_isolation" ON performance_records
    FOR ALL USING (brand_id IN (
        SELECT id FROM brands
        WHERE org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid
    ));

CREATE INDEX idx_campaigns_org ON campaigns(org_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_perf_records_brand ON performance_records(brand_id);
CREATE INDEX idx_perf_records_published ON performance_records(published_at);
