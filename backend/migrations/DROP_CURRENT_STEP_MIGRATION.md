# Migration: Drop current_step Column

## Overview
This migration removes the `current_step` column from the `conversation_state` table. Step tracking is now handled through the `context` JSONB field instead.

## Reason for Change
- **Simplification**: The `current_step` column was redundant since:
  - Conversation flow is tracked via `conversation_flow` (template name)
  - Step progression can be stored in the flexible `context` JSON field
  - Reduces schema complexity without losing functionality

## What Changed

### Database Schema
**Removed Column:**
- `conversation_state.current_step` (VARCHAR(50))

**Step Tracking Now Uses:**
- `context->>'current_step'` (stored in JSONB field)
- Default value: `"initial"`

### Code Changes

#### Models (`app/models/conversation.py`)
- Removed `current_step` from `ConversationStateDB` table model
- Removed `current_step` from `ConversationStateCreate` schema
- Removed `current_step` from `ConversationStateUpdate` schema
- Removed `current_step` from `ConversationStateResponse` schema

#### Services (`app/services/conversation_service.py`)
- Removed `initial_step` parameter from `start_conversation()`
- Removed `current_step` parameter from `update_conversation()`
- Step tracking now handled via context updates

#### Message Handler (`app/services/message_handler.py`)
- Changed from `conversation.current_step` to `conversation.context.get("current_step", "initial")`
- Step updates now go through `context_update={"current_step": next_step}`

## Running the Migration

### On AWS RDS (Production)

```bash
cd backend/migrations

# Set environment variables (or use .env file)
export DB_HOST=your-rds-endpoint.amazonaws.com
export DB_NAME=your_database
export DB_USER=your_user
export DB_PASSWORD=your_password

# Run migration
python drop_current_step_column.py
```

### Rollback (if needed)

```bash
python drop_current_step_column.py --rollback
```

**Note:** Rollback will add the column back with default value `'initial'`, but you'll need to manually update the column values if you have active conversations.

## Verification

After migration, verify the column is gone:

```sql
-- Check column doesn't exist
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'conversation_state' 
AND column_name = 'current_step';
-- Should return no rows

-- Verify conversations still work
SELECT 
    phone_number,
    conversation_flow,
    context->>'current_step' as current_step_from_context,
    last_interaction
FROM conversation_state
LIMIT 5;
```

## Impact

### Zero Data Loss
- All step information is preserved in the `context` field
- Existing conversations continue to work seamlessly
- New conversations automatically use context-based tracking

### Backward Compatibility
- Old code referencing `conversation.current_step` has been updated
- All references now use `conversation.context.get("current_step", "initial")`

## Testing Checklist

- [ ] Migration runs successfully on test database
- [ ] Column is dropped without errors
- [ ] Existing conversations can be retrieved
- [ ] New conversations are created successfully
- [ ] Step progression works (button selections advance steps)
- [ ] Template switching preserves context
- [ ] Text input handling uses correct step
- [ ] App deploys and starts without errors

## Files Modified

```
backend/app/models/conversation.py
backend/app/services/conversation_service.py
backend/app/services/message_handler.py
backend/migrations/drop_current_step_column.py (new)
backend/migrations/DROP_CURRENT_STEP_MIGRATION.md (new)
```

## Related Documentation

- [Database Schema Guide](../../docs/DATABASE_SCHEMA_GUIDE.md)
- [Template System Architecture](../../docs/TEMPLATE_SYSTEM_ARCHITECTURE.md)
- [Conversation Implementation](../../CONVERSATION_IMPLEMENTATION_COMPLETE.md)
