-- Add tiktok, youtube platforms and video_creator agent

-- Update content_slots platform CHECK to include tiktok and youtube
ALTER TABLE content_slots DROP CONSTRAINT content_slots_platform_check;
ALTER TABLE content_slots ADD CONSTRAINT content_slots_platform_check
    CHECK (platform IN ('linkedin', 'x', 'instagram', 'tiktok', 'youtube'));

-- Update agent_messages from_agent CHECK to include video_creator
ALTER TABLE agent_messages DROP CONSTRAINT agent_messages_from_agent_check;
ALTER TABLE agent_messages ADD CONSTRAINT agent_messages_from_agent_check
    CHECK (from_agent IN ('strategist', 'critic', 'publisher', 'video_creator'));
