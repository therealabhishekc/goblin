-- Migration: Add business_metrics table
-- Date: 2025-10-03
-- Description: Creates the business_metrics table for tracking daily analytics

-- Create business_metrics table if it doesn't exist
CREATE TABLE IF NOT EXISTS business_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date TIMESTAMP NOT NULL UNIQUE,
    
    -- Message metrics
    total_messages_received INTEGER DEFAULT 0,
    total_responses_sent INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    
    -- Performance metrics
    response_time_avg_seconds FLOAT,
    
    -- Content tracking
    popular_keywords JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on date for fast lookups
CREATE INDEX IF NOT EXISTS idx_business_metrics_date ON business_metrics(date);

-- Create message_templates table if it doesn't exist (bonus - for future use)
CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    
    -- Template content
    template_text VARCHAR(1000) NOT NULL,
    variables JSONB DEFAULT '[]',
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on template name for fast lookups
CREATE INDEX IF NOT EXISTS idx_message_templates_name ON message_templates(name);
CREATE INDEX IF NOT EXISTS idx_message_templates_category ON message_templates(category);
CREATE INDEX IF NOT EXISTS idx_message_templates_active ON message_templates(is_active);

-- Grant permissions to app_user
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT ALL PRIVILEGES ON business_metrics TO app_user;
        GRANT ALL PRIVILEGES ON message_templates TO app_user;
    END IF;
END $$;
