-- =============================================================================
-- DROP MESSAGE_TEMPLATES TABLE
-- =============================================================================
-- This migration removes the message_templates table as it's no longer needed
-- Date: 2025-01-XX
-- =============================================================================

-- Drop the message_templates table if it exists
DROP TABLE IF EXISTS message_templates CASCADE;

-- Verification - confirm the table is gone
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'message_templates'
        ) 
        THEN 'WARNING: message_templates table still exists'
        ELSE 'SUCCESS: message_templates table has been dropped'
    END AS status;
