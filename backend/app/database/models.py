"""
SQLAlchemy models for PostgreSQL database tables.
These are the actual database table definitions.

DEPRECATED: This models file has been replaced by individual model files in app/models/
Use the newer model files instead:
- app/models/user.py (UserProfileDB)
- app/models/whatsapp.py (WhatsAppMessageDB)
- app/models/business.py (BusinessMetricsDB)
- app/models/marketing.py (CampaignDB, CampaignRecipientDB)
- app/models/conversation.py (ConversationStateDB, WorkflowTemplateDB)

This file only provides backwards compatibility imports.
"""

# Import the actual models from their new locations for backwards compatibility
from app.models.user import UserProfileDB as UserProfile
from app.models.whatsapp import WhatsAppMessageDB as WhatsAppMessage
from app.models.business import BusinessMetricsDB as BusinessMetrics
from app.models.conversation import ConversationStateDB as ConversationState
from app.models.conversation import WorkflowTemplateDB as WorkflowTemplate

# Export for backwards compatibility
__all__ = [
    'UserProfile', 
    'WhatsAppMessage', 
    'BusinessMetrics',
    'ConversationState',
    'WorkflowTemplate'
]

