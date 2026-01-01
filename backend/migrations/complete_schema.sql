-- =============================================================================
-- COMPLETE DATABASE SCHEMA MIGRATION
-- =============================================================================
-- This file combines all migrations into one comprehensive schema setup
-- Run this to create/update all tables and columns from scratch
-- Date: 2025-10-03
-- =============================================================================

-- =============================================================================
-- SECTION 1: CORE TABLES (00_init_schema.sql)
-- =============================================================================

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_phone VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zipcode VARCHAR(20),
    email VARCHAR(100),
    customer_tier VARCHAR(20) DEFAULT 'regular',
    subscription VARCHAR(20) DEFAULT 'subscribed',
    subscription_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    first_contact TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT user_profiles_subscription_check CHECK (subscription IN ('subscribed', 'unsubscribed'))
);

-- Create indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_phone ON user_profiles(whatsapp_phone);
CREATE INDEX IF NOT EXISTS idx_user_profiles_tier ON user_profiles(customer_tier);
CREATE INDEX IF NOT EXISTS idx_user_subscription ON user_profiles(subscription);
CREATE INDEX IF NOT EXISTS idx_user_profiles_city ON user_profiles(city);
CREATE INDEX IF NOT EXISTS idx_user_profiles_state ON user_profiles(state);
CREATE INDEX IF NOT EXISTS idx_user_profiles_zipcode ON user_profiles(zipcode);

-- Create whatsapp_messages table
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(100) UNIQUE NOT NULL,
    from_phone VARCHAR(20) NOT NULL,
    to_phone VARCHAR(20),
    message_type VARCHAR(20) NOT NULL,
    content TEXT,
    media_url VARCHAR(500),
    media_type VARCHAR(50),
    media_size INTEGER,
    status VARCHAR(20) DEFAULT 'processing',
    direction VARCHAR(20) DEFAULT 'incoming',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_direction CHECK (direction IN ('incoming', 'outgoing')),
    CONSTRAINT whatsapp_messages_status_check CHECK (status IN ('processing', 'processed', 'failed', 'sent', 'delivered', 'read', 'received'))
);

-- Create indexes for whatsapp_messages
CREATE INDEX IF NOT EXISTS idx_messages_message_id ON whatsapp_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_messages_from_phone ON whatsapp_messages(from_phone);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON whatsapp_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_status ON whatsapp_messages(status);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON whatsapp_messages(direction);

-- =============================================================================
-- SECTION 2: ADD BUSINESS METRICS TABLE (add_business_metrics_table.sql)
-- =============================================================================

-- Create business_metrics table
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

-- =============================================================================
-- SECTION 3: ADD COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE user_profiles IS 'Customer profile information for WhatsApp users';
COMMENT ON TABLE whatsapp_messages IS 'WhatsApp message history (incoming and outgoing)';
COMMENT ON TABLE business_metrics IS 'Daily business metrics and analytics';

COMMENT ON COLUMN user_profiles.subscription IS 
'User subscription status for template messages: subscribed (can receive templates), unsubscribed (opted out via STOP command). Does NOT affect automated replies to customer messages.';

COMMENT ON COLUMN user_profiles.subscription_updated_at IS 
'Timestamp when subscription status was last changed';

COMMENT ON COLUMN whatsapp_messages.direction IS 
'Message direction: incoming (customer to business) or outgoing (business to customer)';

COMMENT ON COLUMN whatsapp_messages.status IS 
'Message status: processing (being processed), processed (completed successfully), failed (processing failed), sent (outgoing message sent), delivered (message delivered to customer), read (message read by recipient)';

-- =============================================================================
-- SECTION 4: CREATE APPLICATION USER
-- =============================================================================

-- Create app_user for IAM authentication (no password needed)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        -- Create user without password (for IAM authentication)
        CREATE USER app_user;
        
        -- Grant IAM authentication role
        EXECUTE 'GRANT rds_iam TO app_user';
        
        RAISE NOTICE 'Created app_user with IAM authentication';
    ELSE
        RAISE NOTICE 'app_user already exists';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Note: Could not grant rds_iam role. This is expected if rds_iam role does not exist in non-RDS environments.';
END $$;

-- =============================================================================
-- SECTION 5: GRANT PERMISSIONS TO APP USER
-- =============================================================================

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT ALL PRIVILEGES ON user_profiles TO app_user;
        GRANT ALL PRIVILEGES ON whatsapp_messages TO app_user;
        GRANT ALL PRIVILEGES ON business_metrics TO app_user;
    END IF;
END $$;

-- =============================================================================
-- SECTION 6: VERIFICATION QUERIES
-- =============================================================================

-- Show all tables
SELECT 
    'Tables created:' as status,
    table_name
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show row counts
SELECT 'user_profiles' as table_name, COUNT(*) as row_count FROM user_profiles
UNION ALL
SELECT 'whatsapp_messages' as table_name, COUNT(*) as row_count FROM whatsapp_messages
UNION ALL
SELECT 'business_metrics' as table_name, COUNT(*) as row_count FROM business_metrics;

-- Show subscription distribution
SELECT 
    'Subscription Status' as metric,
    subscription,
    COUNT(*) as user_count
FROM user_profiles
GROUP BY subscription;

-- Show message direction distribution
SELECT 
    'Message Direction' as metric,
    direction,
    COUNT(*) as message_count
FROM whatsapp_messages
GROUP BY direction;

-- =============================================================================
-- SECTION 7: MARKETING CAMPAIGNS TABLES
-- =============================================================================
-- Marketing Campaign Management System
-- Supports sending 10,000+ marketing messages with rate limiting (250/day)
-- and prevents duplicate sends to customers
-- =============================================================================

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

-- Marketing campaign indexes
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

-- =============================================================================
-- SECTION 10: MARKETING CAMPAIGNS FUNCTIONS AND TRIGGERS
-- =============================================================================

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
DROP TRIGGER IF EXISTS trigger_update_campaign_stats ON campaign_recipients;
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

-- Triggers for updated_at timestamps on marketing tables
DROP TRIGGER IF EXISTS update_campaigns_updated_at ON marketing_campaigns;
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON marketing_campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_recipients_updated_at ON campaign_recipients;
CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON campaign_recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_schedule_updated_at ON campaign_send_schedule;
CREATE TRIGGER update_schedule_updated_at BEFORE UPDATE ON campaign_send_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SECTION 8: GRANT PERMISSIONS FOR MARKETING TABLES
-- =============================================================================

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT ALL PRIVILEGES ON marketing_campaigns TO app_user;
        GRANT ALL PRIVILEGES ON campaign_recipients TO app_user;
        GRANT ALL PRIVILEGES ON campaign_send_schedule TO app_user;
    END IF;
END $$;

-- =============================================================================
-- SECTION 9: HELPFUL VIEWS FOR MARKETING CAMPAIGNS
-- =============================================================================

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

-- Grant view permissions
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT SELECT ON v_active_campaigns TO app_user;
        GRANT SELECT ON v_daily_campaign_schedule TO app_user;
        GRANT SELECT ON v_recipient_status_summary TO app_user;
    END IF;
END $$;

-- =============================================================================
-- SECTION 10: FINAL VERIFICATION QUERIES
-- =============================================================================

-- Show all tables (including marketing tables)
SELECT 
    'All Tables Created:' as status,
    table_name
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show row counts for all tables
SELECT 'user_profiles' as table_name, COUNT(*) as row_count FROM user_profiles
UNION ALL
SELECT 'whatsapp_messages' as table_name, COUNT(*) as row_count FROM whatsapp_messages
UNION ALL
SELECT 'business_metrics' as table_name, COUNT(*) as row_count FROM business_metrics
UNION ALL
SELECT 'marketing_campaigns' as table_name, COUNT(*) as row_count FROM marketing_campaigns
UNION ALL
SELECT 'campaign_recipients' as table_name, COUNT(*) as row_count FROM campaign_recipients
UNION ALL
SELECT 'campaign_send_schedule' as table_name, COUNT(*) as row_count FROM campaign_send_schedule;

-- =============================================================================
-- MIGRATION COMPLETE!
-- =============================================================================
-- All tables, columns, indexes, constraints, functions, triggers, and views
-- have been created/updated.
-- 
-- Total Tables: 7
--   Core Tables (3):
--     - user_profiles
--     - whatsapp_messages
--     - business_metrics
--   Marketing Campaign Tables (4):
--     - marketing_campaigns
--     - campaign_recipients
--     - campaign_send_schedule
-- 
-- Run verification queries above to ensure everything is working correctly.
-- =============================================================================
