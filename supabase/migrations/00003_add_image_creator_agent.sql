-- Add image_creator to agent_messages from_agent constraint

ALTER TABLE agent_messages DROP CONSTRAINT agent_messages_from_agent_check;
ALTER TABLE agent_messages ADD CONSTRAINT agent_messages_from_agent_check
    CHECK (from_agent IN ('strategist', 'critic', 'publisher', 'video_creator', 'image_creator'));
