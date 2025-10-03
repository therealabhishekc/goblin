-- Migration: Update status values in whatsapp_messages table
-- Purpose: Add 'processing', 'processed', and 'failed' status values
-- Date: 2024-12-XX
-- Author: System Update

-- This migration updates the status column to support new values:
-- - processing: Message is being processed
-- - processed: Message processing completed successfully
-- - failed: Message processing failed

-- Step 1: Update existing messages with old status values
-- Convert any messages with status 'received' or NULL to 'processing'
UPDATE whatsapp_messages 
SET status = 'processing' 
WHERE status = 'received' OR status IS NULL;

-- Step 2: Drop existing check constraint if it exists (PostgreSQL)
ALTER TABLE whatsapp_messages 
DROP CONSTRAINT IF EXISTS whatsapp_messages_status_check;

-- Step 3: Add new check constraint with updated values
ALTER TABLE whatsapp_messages 
ADD CONSTRAINT whatsapp_messages_status_check 
CHECK (status IN ('processing', 'processed', 'failed', 'sent', 'delivered', 'read'));

-- Step 4: Update default value for status column
ALTER TABLE whatsapp_messages 
ALTER COLUMN status SET DEFAULT 'processing';

-- Step 5: Add comment explaining the status values
COMMENT ON COLUMN whatsapp_messages.status IS 
'Message status: processing (being processed), processed (completed successfully), failed (processing failed), sent (outgoing message sent), delivered (message delivered to customer), read (message read by recipient)';

-- Verification queries
SELECT 
    status,
    COUNT(*) as count,
    direction
FROM whatsapp_messages
GROUP BY status, direction
ORDER BY status, direction;

-- Show constraint
SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint 
WHERE conrelid = 'whatsapp_messages'::regclass 
AND conname LIKE '%status%';

-- Migration complete
-- Expected result: 
-- - Status values updated: 'received' -> 'processing'
-- - New constraint allows: processing, processed, failed, sent, delivered, read
-- - Default status is now 'processing'
