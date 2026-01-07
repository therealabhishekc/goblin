"""
Interactive Message Handler
Processes user messages and manages conversation flows
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.conversation_service import ConversationService
from app.whatsapp_api import send_whatsapp_message
from app.core.logging import logger

class InteractiveMessageHandler:
    """Handles interactive conversation messages"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.conv_service = ConversationService(db_session)
    
    async def handle_text_message(
        self,
        phone_number: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Handle incoming text message
        
        Returns:
            Processing result
        """
        # Check if user has active conversation
        conversation = self.conv_service.get_conversation(phone_number)
        
        if conversation:
            # Continue existing conversation
            return await self._continue_conversation(phone_number, text, conversation)
        else:
            # Try to match keyword and start new conversation
            return await self._start_new_conversation(phone_number, text)
    
    async def handle_interactive_message(
        self,
        phone_number: str,
        interactive_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle button/list selection
        
        Args:
            phone_number: Customer phone
            interactive_data: Button or list selection data
        """
        # Extract selection
        if interactive_data.get("type") == "button_reply":
            selection_id = interactive_data["button_reply"]["id"]
        elif interactive_data.get("type") == "list_reply":
            selection_id = interactive_data["list_reply"]["id"]
        else:
            return {"status": "unsupported"}
        
        conversation = self.conv_service.get_conversation(phone_number)
        if not conversation:
            logger.warning(f"⚠️ No conversation for interactive message from {phone_number}")
            return {"status": "no_conversation"}
        
        # Process selection based on current step
        return await self._process_selection(phone_number, selection_id, conversation)
    
    async def _start_new_conversation(
        self,
        phone_number: str,
        text: str
    ) -> Dict[str, Any]:
        """Start a new conversation based on keyword"""
        
        # Find matching template
        template = self.conv_service.find_template_by_keyword(text)
        
        if not template:
            logger.info(f"📭 No template matched for: {text}")
            return {"status": "no_match"}
        
        # Start conversation
        conversation = self.conv_service.start_conversation(
            phone_number=phone_number,
            template_name=template.template_name
        )
        
        # Send initial menu
        await self._send_menu(phone_number, template.menu_structure)
        
        return {
            "status": "conversation_started",
            "template": template.template_name
        }
    
    async def _continue_conversation(
        self,
        phone_number: str,
        text: str,
        conversation: Any
    ) -> Dict[str, Any]:
        """Continue existing conversation"""
        
        template = self.conv_service.get_template(conversation.conversation_flow)
        if not template:
            logger.error(f"❌ Template not found: {conversation.conversation_flow}")
            self.conv_service.end_conversation(phone_number)
            return {"status": "error"}
        
        # Get current step definition
        steps = template.menu_structure.get("steps", {})
        current_step_def = steps.get(conversation.current_step, {})
        
        # Validate input if needed
        if current_step_def.get("validation") == "number":
            try:
                quantity = int(text)
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                await send_whatsapp_message(
                    phone_number,
                    {"type": "text", "text": {"body": "❌ Please enter a valid number"}}
                )
                return {"status": "invalid_input"}
        
        # Store input in context
        context_key = current_step_def.get("context_key", "user_input")
        context_update = {context_key: text}
        
        # Move to next step
        next_step = current_step_def.get("next_step")
        if not next_step:
            logger.error(f"❌ No next step defined for {conversation.current_step}")
            return {"status": "error"}
        
        # Update conversation
        self.conv_service.update_conversation(
            phone_number=phone_number,
            current_step=next_step,
            context_update=context_update
        )
        
        # Send next prompt
        next_step_def = steps.get(next_step, {})
        prompt = next_step_def.get("prompt", "Continue...")
        
        # Replace placeholders with context values
        prompt = self._format_prompt(prompt, conversation.context)
        
        await send_whatsapp_message(
            phone_number,
            {"type": "text", "text": {"body": prompt}}
        )
        
        # Check if conversation should end
        if next_step_def.get("end_conversation"):
            self.conv_service.end_conversation(phone_number)
            return {"status": "conversation_completed"}
        
        return {"status": "step_advanced", "next_step": next_step}
    
    async def _process_selection(
        self,
        phone_number: str,
        selection_id: str,
        conversation: Any
    ) -> Dict[str, Any]:
        """Process button or list selection"""
        
        template = self.conv_service.get_template(conversation.conversation_flow)
        if not template:
            return {"status": "error"}
        
        # Get step definition
        steps = template.menu_structure.get("steps", {})
        current_step_def = steps.get(conversation.current_step, {})
        
        # Determine next step based on selection
        next_steps = current_step_def.get("next_steps", {})
        
        if selection_id in next_steps:
            # Switch template if needed
            next_value = next_steps[selection_id]
            
            if next_value.endswith("_flow"):
                # Start a different flow
                template_name = next_value.replace("_flow", "")
                self.conv_service.update_conversation(
                    phone_number=phone_number,
                    new_template=template_name,
                    current_step="initial",
                    context_update={"previous_selection": selection_id}
                )
                
                # Send new menu
                new_template = self.conv_service.get_template(template_name)
                if new_template:
                    await self._send_menu(phone_number, new_template.menu_structure)
            else:
                # Move to next step in current flow
                self.conv_service.update_conversation(
                    phone_number=phone_number,
                    current_step=next_value,
                    context_update={"selection": selection_id}
                )
        
        return {"status": "selection_processed"}
    
    async def _send_menu(self, phone_number: str, menu_structure: Dict[str, Any]):
        """Send WhatsApp interactive menu"""
        
        menu_type = menu_structure.get("type")
        
        if menu_type == "button":
            # Send button message
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": menu_structure.get("body"),
                    "action": menu_structure.get("action")
                }
            }
        elif menu_type == "list":
            # Send list message
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": menu_structure.get("body"),
                    "action": menu_structure.get("action")
                }
            }
        else:
            # Send text message
            message = {
                "type": "text",
                "text": {"body": menu_structure.get("body", {}).get("text", "Menu")}
            }
        
        await send_whatsapp_message(phone_number, message)
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Replace placeholders in prompt with context values"""
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        return prompt
