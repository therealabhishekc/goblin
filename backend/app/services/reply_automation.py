"""
Intelligent Reply Automation System
Handles business logic for automatic replies based on message content and context
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, time
from app.core.logging import logger
from app.services.sqs_service import send_outgoing_message

class ReplyRule:
    """Represents a single reply rule"""
    
    def __init__(self, name: str, condition: str, reply_type: str, reply_data: Dict[str, Any], 
                 priority: int = 0, active: bool = True):
        self.name = name
        self.condition = condition
        self.reply_type = reply_type
        self.reply_data = reply_data
        self.priority = priority
        self.active = active

class BusinessHours:
    """Business hours configuration"""
    
    def __init__(self, start_time: time = time(9, 0), end_time: time = time(17, 0), 
                 weekdays_only: bool = True):
        self.start_time = start_time
        self.end_time = end_time
        self.weekdays_only = weekdays_only
    
    def is_business_hours(self, dt: datetime = None) -> bool:
        """Check if current time is within business hours"""
        if dt is None:
            dt = datetime.now()
        
        # Check weekday if required
        if self.weekdays_only and dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        current_time = dt.time()
        return self.start_time <= current_time <= self.end_time

class ReplyAutomation:
    """Main reply automation engine"""
    
    def __init__(self):
        self.rules: List[ReplyRule] = []
        self.business_hours = BusinessHours()
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default reply rules"""
        
        # Greeting rules
        self.rules.extend([
            ReplyRule(
                name="greeting_hi",
                condition=r"\b(hi|hello|hey|greetings)\b",
                reply_type="text",
                reply_data={
                    "type": "text",
                    "content": "Hello! 👋 Welcome to our WhatsApp Business. How can I help you today?"
                },
                priority=10
            ),
            
            ReplyRule(
                name="greeting_good_morning",
                condition=r"\b(good morning|morning)\b",
                reply_type="text",
                reply_data={
                    "type": "text",
                    "content": "Good morning! ☀️ Hope you're having a great day. How can I assist you?"
                },
                priority=10
            ),
            
            # Business hours response
            ReplyRule(
                name="business_hours_closed",
                condition="*",  # Always matches (will be filtered by business hours)
                reply_type="template",
                reply_data={
                    "type": "text",
                    "content": "Thank you for contacting us! 🕒 Our business hours are 9 AM - 5 PM (Mon-Fri). We'll respond to your message during business hours. For urgent matters, please call us directly."
                },
                priority=1
            ),
            
            # FAQ responses
            ReplyRule(
                name="faq_hours",
                condition=r"\b(hours|open|close|timing|schedule)\b",
                reply_type="text",
                reply_data={
                    "type": "text",
                    "content": "🕒 Our business hours are:\nMonday - Friday: 9:00 AM - 5:00 PM\nSaturday - Sunday: Closed\n\nFor urgent matters outside business hours, please call us directly."
                },
                priority=8
            ),
            
            ReplyRule(
                name="faq_pricing",
                condition=r"\b(price|cost|rate|pricing|how much|fee)\b",
                reply_type="document",
                reply_data={
                    "type": "text",
                    "content": "Great question about our pricing! 💰 Let me send you our detailed pricing information. One moment please..."
                },
                priority=7
            ),
            
            ReplyRule(
                name="faq_support",
                condition=r"\b(support|help|issue|problem|bug|error)\b",
                reply_type="text",
                reply_data={
                    "type": "text",
                    "content": "I'm here to help! 🛠️ Could you please describe the specific issue you're experiencing? The more details you provide, the better I can assist you."
                },
                priority=7
            ),
            
            # Contact information
            ReplyRule(
                name="contact_info",
                condition=r"\b(contact|phone|email|address|location)\b",
                reply_type="location",
                reply_data={
                    "type": "text",
                    "content": "📞 Here's how to reach us:\nPhone: +1 (555) 123-4567\nEmail: support@company.com\nAddress: 123 Business St, City, State 12345"
                },
                priority=6
            ),
            
            # Fallback responses
            ReplyRule(
                name="fallback_unknown",
                condition="*",  # Matches anything (lowest priority)
                reply_type="text",
                reply_data={
                    "type": "text",
                    "content": "Thank you for your message! 😊 I'll make sure our team reviews this and gets back to you soon. For immediate assistance, you can also call us during business hours."
                },
                priority=0
            )
        ])
    
    async def process_incoming_message(self, phone_number: str, message_text: str, 
                                     message_type: str = "text", user_context: Dict = None) -> Optional[str]:
        """
        Process incoming message and generate automated reply
        
        Args:
            phone_number: Sender's phone number
            message_text: The message content
            message_type: Type of message (text, image, etc.)
            user_context: Additional user context from database
            
        Returns:
            Message ID if reply was queued, None if no reply needed
        """
        try:
            if not message_text or message_type != "text":
                # Only process text messages for now
                logger.info(f"Skipping auto-reply for non-text message from {phone_number}")
                return None
            
            # Normalize message text
            normalized_text = message_text.lower().strip()
            
            # Find matching rule
            matching_rule = self._find_matching_rule(normalized_text)
            
            if not matching_rule:
                logger.info(f"No matching rule found for message: '{message_text[:50]}...'")
                return None
            
            # Check business hours for certain rules
            if matching_rule.name == "business_hours_closed" and self.business_hours.is_business_hours():
                logger.info("Business hours - skipping closed hours message")
                return None
            
            # Generate and send reply
            reply_message_id = await self._send_automated_reply(
                phone_number, 
                matching_rule,
                message_context={"original_message": message_text, "user_context": user_context}
            )
            
            if reply_message_id:
                logger.info(f"✅ Auto-reply sent to {phone_number} using rule '{matching_rule.name}': {reply_message_id}")
            
            return reply_message_id
            
        except Exception as e:
            logger.error(f"❌ Error processing auto-reply for {phone_number}: {e}")
            return None
    
    def _find_matching_rule(self, message_text: str) -> Optional[ReplyRule]:
        """Find the highest priority matching rule"""
        
        matching_rules = []
        
        for rule in self.rules:
            if not rule.active:
                continue
                
            if self._rule_matches(rule.condition, message_text):
                matching_rules.append(rule)
        
        if not matching_rules:
            return None
        
        # Return highest priority rule
        return max(matching_rules, key=lambda r: r.priority)
    
    def _rule_matches(self, condition: str, message_text: str) -> bool:
        """Check if a rule condition matches the message"""
        
        if condition == "*":
            return True
        
        # Use regex matching
        try:
            return bool(re.search(condition, message_text, re.IGNORECASE))
        except re.error:
            logger.warning(f"Invalid regex pattern: {condition}")
            return False
    
    async def _send_automated_reply(self, phone_number: str, rule: ReplyRule, 
                                  message_context: Dict = None) -> Optional[str]:
        """Send automated reply based on rule"""
        
        try:
            # Prepare reply data
            reply_data = rule.reply_data.copy()
            
            # Add automation metadata
            metadata = {
                "rule_name": rule.name,
                "reply_type": rule.reply_type,
                "automated": True,
                "timestamp": datetime.now().isoformat(),
                "priority": "high" if rule.priority > 5 else "normal"
            }
            
            if message_context:
                metadata["context"] = message_context
            
            # Queue the reply message
            message_id = await send_outgoing_message(
                phone_number=phone_number,
                message_data=reply_data,
                metadata=metadata
            )
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Error sending automated reply: {e}")
            return None
    
    def add_custom_rule(self, rule: ReplyRule):
        """Add a custom reply rule"""
        self.rules.append(rule)
        logger.info(f"Added custom rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"Removed rule: {rule_name}")
                return True
        return False
    
    def update_business_hours(self, start_time: time, end_time: time, weekdays_only: bool = True):
        """Update business hours configuration"""
        self.business_hours = BusinessHours(start_time, end_time, weekdays_only)
        logger.info(f"Updated business hours: {start_time} - {end_time}, weekdays only: {weekdays_only}")
    
    def get_active_rules(self) -> List[Dict[str, Any]]:
        """Get list of all active rules"""
        return [
            {
                "name": rule.name,
                "condition": rule.condition,
                "reply_type": rule.reply_type,
                "priority": rule.priority,
                "active": rule.active
            }
            for rule in self.rules if rule.active
        ]

# Global instance
reply_automation = ReplyAutomation()