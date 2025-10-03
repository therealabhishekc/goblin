-- Add subscription column for template message opt-in/opt-out
-- This migration adds support for STOP/START commands

-- Add subscription column with default value 'subscribed'
ALTER TABLE user_profiles 
ADD COLUMN subscription VARCHAR(20) DEFAULT 'subscribed' 
CHECK (subscription IN ('subscribed', 'unsubscribed'));

-- Create index for faster queries on subscription
CREATE INDEX idx_user_subscription ON user_profiles(subscription);

-- Add timestamp for when subscription status changed
ALTER TABLE user_profiles
ADD COLUMN subscription_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add comment explaining the column
COMMENT ON COLUMN user_profiles.subscription IS 
'User subscription status for template messages: subscribed (can receive templates), unsubscribed (opted out via STOP command). Does NOT affect automated replies to customer messages.';

COMMENT ON COLUMN user_profiles.subscription_updated_at IS 
'Timestamp when subscription status was last changed';

-- Set all existing users to subscribed by default
UPDATE user_profiles 
SET subscription = 'subscribed', 
    subscription_updated_at = CURRENT_TIMESTAMP
WHERE subscription IS NULL;

-- Verification query
SELECT 
    subscription,
    COUNT(*) as user_count
FROM user_profiles
GROUP BY subscription;
