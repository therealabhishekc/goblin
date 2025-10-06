-- ==================================================================================
-- Marketing Campaign Management System
-- ==================================================================================
-- This schema supports sending 10,000+ marketing messages with rate limiting (250/day)
-- and prevents duplicate sends to customers
-- ==================================================================================

-- 1. MARKETING CAMPAIGNS TABLE
-- Stores campaign metadata and settings
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Campaign details
    name VARCHAR(200) NOT NULL,
    description TEXT,
    template_name VARCHAR(100) NOT NULL,  -- WhatsApp template to use
    language_code VARCHAR(10) DEFAULT 'en_US',
    
    -- Campaign configuration
    target_audience JSONB,  -- Filter criteria for target audience
    total_target_customers INTEGER DEFAULT 0,
    daily_send_limit INTEGER DEFAULT 250,  -- WhatsApp rate limit
    
    -- Campaign status
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'active', 'paused', 'completed', 'cancelled'
    priority INTEGER DEFAULT 5,  -- 1 (highest) to 10 (lowest)
    
    -- Scheduling
    scheduled_start_date TIMESTAMP,
    scheduled_end_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Template parameters (for dynamic content)
    template_components JSONB,  -- Full template structure with components
    
    -- Statistics
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_read INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    messages_pending INTEGER DEFAULT 0,
    
    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 10)
);

-- 2. CAMPAIGN RECIPIENTS TABLE
-- Tracks which customers are targeted and their send status
CREATE TABLE IF NOT EXISTS campaign_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    campaign_id UUID NOT NULL REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    
    -- Sending status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'queued', 'sent', 'delivered', 'read', 'failed', 'skipped'
    whatsapp_message_id VARCHAR(100),  -- ID from WhatsApp API after sending
    
    -- Scheduling
    scheduled_send_date DATE,  -- Which day this message should be sent
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    failed_at TIMESTAMP,
    
    -- Error handling
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Personalization
    template_parameters JSONB,  -- Custom parameters for this recipient
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_recipient_status CHECK (status IN ('pending', 'queued', 'sent', 'delivered', 'read', 'failed', 'skipped')),
    CONSTRAINT unique_campaign_recipient UNIQUE (campaign_id, phone_number)
);

-- 3. CAMPAIGN SEND SCHEDULE TABLE
-- Manages daily send batches to respect rate limits
CREATE TABLE IF NOT EXISTS campaign_send_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    campaign_id UUID NOT NULL REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
    
    -- Schedule details
    send_date DATE NOT NULL,
    batch_number INTEGER NOT NULL,  -- Multiple batches per day if needed
    
    -- Batch limits
    batch_size INTEGER DEFAULT 250,
    messages_sent INTEGER DEFAULT 0,
    messages_remaining INTEGER DEFAULT 250,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_schedule_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT unique_campaign_date_batch UNIQUE (campaign_id, send_date, batch_number)
);

-- 4. CAMPAIGN ANALYTICS TABLE
-- Daily aggregated statistics for campaigns
CREATE TABLE IF NOT EXISTS campaign_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    campaign_id UUID NOT NULL REFERENCES marketing_campaigns(id) ON DELETE CASCADE,
    
    -- Analytics date
    date DATE NOT NULL,
    
    -- Message metrics
    messages_sent INTEGER DEFAULT 0,
    messages_delivered INTEGER DEFAULT 0,
    messages_read INTEGER DEFAULT 0,
    messages_failed INTEGER DEFAULT 0,
    
    -- Engagement metrics
    replies_received INTEGER DEFAULT 0,
    unique_responders INTEGER DEFAULT 0,
    
    -- Performance metrics
    delivery_rate DECIMAL(5,2),  -- Percentage
    read_rate DECIMAL(5,2),  -- Percentage
    response_rate DECIMAL(5,2),  -- Percentage
    avg_response_time_minutes INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_campaign_date UNIQUE (campaign_id, date)
);

-- ==================================================================================
-- INDEXES FOR PERFORMANCE
-- ==================================================================================

-- Campaign indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON marketing_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_priority ON marketing_campaigns(priority);
CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled_start ON marketing_campaigns(scheduled_start_date);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON marketing_campaigns(created_at);

-- Recipient indexes
CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON campaign_recipients(campaign_id);
CREATE INDEX IF NOT EXISTS idx_recipients_phone ON campaign_recipients(phone_number);
CREATE INDEX IF NOT EXISTS idx_recipients_status ON campaign_recipients(status);
CREATE INDEX IF NOT EXISTS idx_recipients_scheduled_date ON campaign_recipients(scheduled_send_date);
CREATE INDEX IF NOT EXISTS idx_recipients_campaign_status ON campaign_recipients(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_recipients_date_status ON campaign_recipients(scheduled_send_date, status);

-- Schedule indexes
CREATE INDEX IF NOT EXISTS idx_schedule_campaign ON campaign_send_schedule(campaign_id);
CREATE INDEX IF NOT EXISTS idx_schedule_date ON campaign_send_schedule(send_date);
CREATE INDEX IF NOT EXISTS idx_schedule_status ON campaign_send_schedule(status);
CREATE INDEX IF NOT EXISTS idx_schedule_campaign_date ON campaign_send_schedule(campaign_id, send_date);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_analytics_campaign ON campaign_analytics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON campaign_analytics(date);

-- ==================================================================================
-- FUNCTIONS AND TRIGGERS
-- ==================================================================================

-- Function to update campaign statistics
CREATE OR REPLACE FUNCTION update_campaign_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        -- Update campaign message counts
        UPDATE marketing_campaigns
        SET 
            messages_sent = (
                SELECT COUNT(*) FROM campaign_recipients 
                WHERE campaign_id = NEW.campaign_id AND status IN ('sent', 'delivered', 'read')
            ),
            messages_delivered = (
                SELECT COUNT(*) FROM campaign_recipients 
                WHERE campaign_id = NEW.campaign_id AND status IN ('delivered', 'read')
            ),
            messages_read = (
                SELECT COUNT(*) FROM campaign_recipients 
                WHERE campaign_id = NEW.campaign_id AND status = 'read'
            ),
            messages_failed = (
                SELECT COUNT(*) FROM campaign_recipients 
                WHERE campaign_id = NEW.campaign_id AND status = 'failed'
            ),
            messages_pending = (
                SELECT COUNT(*) FROM campaign_recipients 
                WHERE campaign_id = NEW.campaign_id AND status = 'pending'
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.campaign_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update campaign stats
CREATE TRIGGER trigger_update_campaign_stats
AFTER UPDATE OF status ON campaign_recipients
FOR EACH ROW
EXECUTE FUNCTION update_campaign_stats();

-- Function to automatically update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at timestamps
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON marketing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON campaign_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedule_updated_at BEFORE UPDATE ON campaign_send_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_updated_at BEFORE UPDATE ON campaign_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================================================================================
-- GRANT PERMISSIONS TO APP USER
-- ==================================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON marketing_campaigns TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON campaign_recipients TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON campaign_send_schedule TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON campaign_analytics TO app_user;

-- ==================================================================================
-- HELPFUL VIEWS FOR QUERIES
-- ==================================================================================

-- View: Active campaigns with progress
CREATE OR REPLACE VIEW v_active_campaigns AS
SELECT 
    c.id,
    c.name,
    c.status,
    c.template_name,
    c.total_target_customers,
    c.messages_sent,
    c.messages_delivered,
    c.messages_read,
    c.messages_failed,
    c.messages_pending,
    ROUND((c.messages_sent::DECIMAL / NULLIF(c.total_target_customers, 0)) * 100, 2) as progress_percentage,
    c.daily_send_limit,
    c.scheduled_start_date,
    c.scheduled_end_date,
    c.created_at
FROM marketing_campaigns c
WHERE c.status IN ('active', 'paused')
ORDER BY c.priority ASC, c.created_at ASC;

GRANT SELECT ON v_active_campaigns TO app_user;

-- View: Daily campaign schedule summary
CREATE OR REPLACE VIEW v_daily_campaign_schedule AS
SELECT 
    s.send_date,
    s.campaign_id,
    c.name as campaign_name,
    COUNT(s.id) as batch_count,
    SUM(s.batch_size) as total_planned,
    SUM(s.messages_sent) as total_sent,
    SUM(s.messages_remaining) as total_remaining,
    MIN(s.status) as overall_status
FROM campaign_send_schedule s
JOIN marketing_campaigns c ON s.campaign_id = c.id
GROUP BY s.send_date, s.campaign_id, c.name
ORDER BY s.send_date DESC, c.name;

GRANT SELECT ON v_daily_campaign_schedule TO app_user;

-- View: Recipient send status summary
CREATE OR REPLACE VIEW v_recipient_status_summary AS
SELECT 
    campaign_id,
    status,
    COUNT(*) as count,
    MIN(sent_at) as first_sent,
    MAX(sent_at) as last_sent
FROM campaign_recipients
GROUP BY campaign_id, status;

GRANT SELECT ON v_recipient_status_summary TO app_user;

-- ==================================================================================
-- END OF MARKETING CAMPAIGNS SCHEMA
-- ==================================================================================
