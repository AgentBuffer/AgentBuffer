-- Add bluesky platform and pending/skipped statuses

-- Update content_slots platform CHECK to include bluesky
ALTER TABLE content_slots DROP CONSTRAINT content_slots_platform_check;
ALTER TABLE content_slots ADD CONSTRAINT content_slots_platform_check
    CHECK (platform IN ('linkedin', 'x', 'instagram', 'tiktok', 'youtube', 'bluesky'));

-- Update content_slots status CHECK to include pending and skipped
ALTER TABLE content_slots DROP CONSTRAINT content_slots_status_check;
ALTER TABLE content_slots ADD CONSTRAINT content_slots_status_check
    CHECK (status IN ('draft', 'proposed', 'rejected', 'approved', 'published', 'failed', 'pending', 'skipped'));
