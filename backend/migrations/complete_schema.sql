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
    business_name VARCHAR(200),
    email VARCHAR(100),
    customer_tier VARCHAR(20) DEFAULT 'regular',
    tags TEXT[] DEFAULT '{}',
    notes TEXT,
    first_contact TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user_profiles
CREATE INDEX IF NOT EXISTS idx_user_profiles_phone ON user_profiles(whatsapp_phone);
CREATE INDEX IF NOT EXISTS idx_user_profiles_tier ON user_profiles(customer_tier);

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
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for whatsapp_messages
CREATE INDEX IF NOT EXISTS idx_messages_message_id ON whatsapp_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_messages_from_phone ON whatsapp_messages(from_phone);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON whatsapp_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_status ON whatsapp_messages(status);

-- Create message_queue table (for SQS tracking)
CREATE TABLE IF NOT EXISTS message_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id VARCHAR(100) NOT NULL,
    queue_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_queue_message_id ON message_queue(message_id);
CREATE INDEX IF NOT EXISTS idx_queue_status ON message_queue(status);

-- =============================================================================
-- SECTION 2: ADD DIRECTION COLUMN (add_direction_column.sql)
-- =============================================================================

-- Add direction column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'whatsapp_messages' AND column_name = 'direction'
    ) THEN
        ALTER TABLE whatsapp_messages 
        ADD COLUMN direction VARCHAR(20) DEFAULT 'incoming';
    END IF;
END $$;

-- Add check constraint for direction (drop first if exists)
ALTER TABLE whatsapp_messages 
DROP CONSTRAINT IF EXISTS check_direction;

ALTER TABLE whatsapp_messages 
ADD CONSTRAINT check_direction CHECK (direction IN ('incoming', 'outgoing'));

-- Create index for direction
CREATE INDEX IF NOT EXISTS idx_messages_direction ON whatsapp_messages(direction);

-- Update existing NULL values to 'incoming'
UPDATE whatsapp_messages 
SET direction = 'incoming' 
WHERE direction IS NULL;

-- =============================================================================
-- SECTION 3: ADD SUBSCRIPTION COLUMN (add_subscription_column.sql)
-- =============================================================================

-- Add subscription column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'subscription'
    ) THEN
        ALTER TABLE user_profiles 
        ADD COLUMN subscription VARCHAR(20) DEFAULT 'subscribed';
    END IF;
END $$;

-- Add subscription check constraint (drop first if exists)
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS user_profiles_subscription_check;

ALTER TABLE user_profiles
ADD CONSTRAINT user_profiles_subscription_check 
CHECK (subscription IN ('subscribed', 'unsubscribed'));

-- Create index for subscription
CREATE INDEX IF NOT EXISTS idx_user_subscription ON user_profiles(subscription);

-- Add subscription_updated_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'subscription_updated_at'
    ) THEN
        ALTER TABLE user_profiles
        ADD COLUMN subscription_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Set all existing users to subscribed
UPDATE user_profiles 
SET subscription = 'subscribed', 
    subscription_updated_at = CURRENT_TIMESTAMP
WHERE subscription IS NULL;

-- =============================================================================
-- SECTION 4: ADD BUSINESS METRICS TABLE (add_business_metrics_table.sql)
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

-- Create message_templates table
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

-- Create indexes on message_templates
CREATE INDEX IF NOT EXISTS idx_message_templates_name ON message_templates(name);
CREATE INDEX IF NOT EXISTS idx_message_templates_category ON message_templates(category);
CREATE INDEX IF NOT EXISTS idx_message_templates_active ON message_templates(is_active);

-- =============================================================================
-- SECTION 5: UPDATE STATUS VALUES (update_status_values.sql)
-- =============================================================================

-- Drop existing status check constraint if it exists
ALTER TABLE whatsapp_messages 
DROP CONSTRAINT IF EXISTS whatsapp_messages_status_check;

-- Add new status check constraint with all valid values
ALTER TABLE whatsapp_messages 
ADD CONSTRAINT whatsapp_messages_status_check 
CHECK (status IN ('processing', 'processed', 'failed', 'sent', 'delivered', 'read', 'received'));

-- Update default value for status column
ALTER TABLE whatsapp_messages 
ALTER COLUMN status SET DEFAULT 'processing';

-- =============================================================================
-- SECTION 6: ADD COMMENTS AND DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE user_profiles IS 'Customer profile information for WhatsApp users';
COMMENT ON TABLE whatsapp_messages IS 'WhatsApp message history (incoming and outgoing)';
COMMENT ON TABLE business_metrics IS 'Daily business metrics and analytics';
COMMENT ON TABLE message_templates IS 'Reusable message templates for customer communication';

COMMENT ON COLUMN user_profiles.subscription IS 
'User subscription status for template messages: subscribed (can receive templates), unsubscribed (opted out via STOP command). Does NOT affect automated replies to customer messages.';

COMMENT ON COLUMN user_profiles.subscription_updated_at IS 
'Timestamp when subscription status was last changed';

COMMENT ON COLUMN whatsapp_messages.direction IS 
'Message direction: incoming (customer to business) or outgoing (business to customer)';

COMMENT ON COLUMN whatsapp_messages.status IS 
'Message status: processing (being processed), processed (completed successfully), failed (processing failed), sent (outgoing message sent), delivered (message delivered to customer), read (message read by recipient)';

-- =============================================================================
-- SECTION 7: GRANT PERMISSIONS TO APP USER
-- =============================================================================

DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT ALL PRIVILEGES ON user_profiles TO app_user;
        GRANT ALL PRIVILEGES ON whatsapp_messages TO app_user;
        GRANT ALL PRIVILEGES ON message_queue TO app_user;
        GRANT ALL PRIVILEGES ON business_metrics TO app_user;
        GRANT ALL PRIVILEGES ON message_templates TO app_user;
    END IF;
END $$;

-- =============================================================================
-- SECTION 8: VERIFICATION QUERIES
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
SELECT 'message_queue' as table_name, COUNT(*) as row_count FROM message_queue
UNION ALL
SELECT 'business_metrics' as table_name, COUNT(*) as row_count FROM business_metrics
UNION ALL
SELECT 'message_templates' as table_name, COUNT(*) as row_count FROM message_templates;

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
-- MIGRATION COMPLETE!
-- =============================================================================
-- All tables, columns, indexes, and constraints have been created/updated.
-- Run verification queries above to ensure everything is working correctly.
-- =============================================================================
