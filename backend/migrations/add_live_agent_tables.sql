-- Run this migration on your RDS database
-- Usage: psql "postgresql://postgres@whatsapp-postgres-development.cibi66cyqd2r.us-east-1.rds.amazonaws.com:5432/whatsapp_business_development" -f add_live_agent_tables.sql

BEGIN;

-- Create agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation_state(id) ON DELETE CASCADE,
    agent_id VARCHAR(50),
    agent_name VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '22 hours'),
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_status CHECK (status IN ('waiting', 'active', 'ended'))
);

CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_conversation ON agent_sessions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_expires ON agent_sessions(expires_at) WHERE status IN ('waiting', 'active');

-- Create agent messages table
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,
    sender_id VARCHAR(50),
    message_text TEXT NOT NULL,
    media_url TEXT,
    media_type VARCHAR(20),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_sender CHECK (sender_type IN ('customer', 'agent', 'system'))
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session ON agent_messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_messages_timestamp ON agent_messages(timestamp);

COMMIT;
