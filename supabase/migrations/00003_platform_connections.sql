-- Platform connections — stores OAuth tokens for direct platform APIs.
-- Replaces the single AYRSHARE_API_KEY with per-platform credentials.

CREATE TABLE platform_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    brand_id UUID REFERENCES brands(id) NOT NULL,
    platform TEXT NOT NULL
        CHECK (platform IN ('linkedin', 'x', 'instagram', 'tiktok', 'youtube', 'bluesky')),
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    account_id TEXT,
    account_name TEXT,
    connected_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE (org_id, brand_id, platform)
);

ALTER TABLE platform_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "org_isolation" ON platform_connections
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);

CREATE INDEX idx_platform_connections_org ON platform_connections(org_id);
CREATE INDEX idx_platform_connections_brand ON platform_connections(brand_id);
CREATE INDEX idx_platform_connections_lookup
    ON platform_connections(org_id, brand_id, platform);

-- Update content_slots platform CHECK to include bluesky
ALTER TABLE content_slots DROP CONSTRAINT content_slots_platform_check;
ALTER TABLE content_slots ADD CONSTRAINT content_slots_platform_check
    CHECK (platform IN ('linkedin', 'x', 'instagram', 'tiktok', 'youtube', 'bluesky'));
