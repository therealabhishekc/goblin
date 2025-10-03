-- Migration: Add direction column to whatsapp_messages table
-- Purpose: Store outgoing messages sent by employees to customers
-- Date: 2024-12-XX
-- Author: System Update

-- Add direction column with default value 'incoming'
ALTER TABLE whatsapp_messages 
ADD COLUMN direction VARCHAR(20) DEFAULT 'incoming';

-- Add check constraint to ensure only valid values
ALTER TABLE whatsapp_messages 
ADD CONSTRAINT check_direction CHECK (direction IN ('incoming', 'outgoing'));

-- Create index for efficient queries by direction
CREATE INDEX idx_messages_direction ON whatsapp_messages(direction);

-- Update existing records to have 'incoming' direction (if NULL)
UPDATE whatsapp_messages 
SET direction = 'incoming' 
WHERE direction IS NULL;

-- Optional: Add comment to the column
COMMENT ON COLUMN whatsapp_messages.direction IS 'Message direction: incoming (customer to business) or outgoing (business to customer)';

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    column_default, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'whatsapp_messages' 
AND column_name = 'direction';

-- Show index created
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'whatsapp_messages' 
AND indexname = 'idx_messages_direction';

-- Migration complete
-- Expected result: direction column added with default 'incoming' and index created
