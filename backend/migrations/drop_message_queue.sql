-- =============================================================================
-- DROP MESSAGE_QUEUE TABLE
-- =============================================================================
-- This migration removes the message_queue table which was used for SQS tracking
-- but is no longer used in the application.
-- 
-- Created: 2024
-- =============================================================================

-- Drop the message_queue table if it exists
DROP TABLE IF EXISTS message_queue CASCADE;

-- Verification: Show remaining tables
SELECT 
    'Remaining tables:' as status,
    table_name
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Verification complete
SELECT '✅ message_queue table has been successfully removed' as status;
