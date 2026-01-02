-- Migration: Add status timestamp columns to whatsapp_messages table
-- Date: 2026-01-01
-- Description: Add sent_at, delivered_at, read_at, failed_at, and failed_reason columns
--              Similar to campaign_recipients table structure

-- Add new columns to whatsapp_messages table
ALTER TABLE whatsapp_messages 
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS read_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS failed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS failed_reason TEXT;

-- Create indexes for timestamp columns for better query performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_sent_at ON whatsapp_messages(sent_at);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_delivered_at ON whatsapp_messages(delivered_at);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_read_at ON whatsapp_messages(read_at);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_failed_at ON whatsapp_messages(failed_at);

-- Update existing records: set sent_at to timestamp for all outgoing messages with 'sent' status
UPDATE whatsapp_messages 
SET sent_at = timestamp 
WHERE direction = 'outgoing' 
  AND status IN ('sent', 'delivered', 'read')
  AND sent_at IS NULL;

-- Update existing records: set delivered_at to timestamp for all messages with 'delivered' status
UPDATE whatsapp_messages 
SET delivered_at = timestamp 
WHERE status IN ('delivered', 'read')
  AND delivered_at IS NULL;

-- Update existing records: set read_at to timestamp for all messages with 'read' status
UPDATE whatsapp_messages 
SET read_at = timestamp 
WHERE status = 'read'
  AND read_at IS NULL;

-- Update existing records: set failed_at to timestamp for all messages with 'failed' status
UPDATE whatsapp_messages 
SET failed_at = timestamp 
WHERE status = 'failed'
  AND failed_at IS NULL;

-- Display summary of changes
SELECT 
    COUNT(*) as total_messages,
    COUNT(sent_at) as with_sent_at,
    COUNT(delivered_at) as with_delivered_at,
    COUNT(read_at) as with_read_at,
    COUNT(failed_at) as with_failed_at
FROM whatsapp_messages;

-- Migration completed successfully
