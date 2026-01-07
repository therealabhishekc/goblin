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
        # First check if this text matches any trigger keyword
        # This allows users to restart conversations by typing trigger words
        template = self.conv_service.find_template_by_keyword(text)
        
        if template:
            # User typed a trigger keyword - start/restart that conversation
            logger.info(f"🎯 Trigger keyword '{text}' matched template '{template.template_name}'")
            
            # End any existing conversation
            conversation = self.conv_service.get_conversation(phone_number)
            if conversation:
                logger.info(f"🔄 Ending existing conversation to start new one")
                self.conv_service.end_conversation(phone_number)
            
            # Start new conversation
            return await self._start_new_conversation(phone_number, text)
        
        # Check if user has active conversation
        conversation = self.conv_service.get_conversation(phone_number)
        
        if conversation:
            # Continue existing conversation
            return await self._continue_conversation(phone_number, text, conversation)
        else:
            # No conversation and no keyword match
            logger.info(f"📭 No template or conversation for: '{text}'")
            return {"status": "no_match"}
    
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
        
        logger.info(f"🔎 Looking for template matching text: '{text}'")
        
        # Find matching template
        template = self.conv_service.find_template_by_keyword(text)
        
        if not template:
            logger.info(f"📭 No template matched for: '{text}'")
            return {"status": "no_match"}
        
        logger.info(f"✅ Found template: {template.template_name}")
        
        # Start conversation
        conversation = self.conv_service.start_conversation(
            phone_number=phone_number,
            template_name=template.template_name
        )
        
        logger.info(f"🗣️ Conversation started for {phone_number}, sending initial message...")
        
        # Send initial menu/message
        try:
            # Check if template has a menu to send
            menu_type = template.menu_structure.get("type")
            
            if menu_type in ["button", "list"]:
                # Send interactive menu
                await self._send_menu(phone_number, template.menu_structure)
                logger.info(f"✅ Interactive menu sent successfully to {phone_number}")
            else:
                # Send text message
                body_text = template.menu_structure.get("body", {}).get("text", "")
                if body_text:
                    await send_whatsapp_message(
                        phone_number,
                        {"type": "text", "content": body_text}
                    )
                    logger.info(f"✅ Text message sent successfully to {phone_number}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send initial message: {e}", exc_info=True)
            # Clean up the conversation since we couldn't send the menu
            self.conv_service.end_conversation(phone_number)
            raise
        
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
        
        # Check if user wants to return to main menu
        if text.lower().strip() in ["menu", "main menu", "back"]:
            # End current conversation and start main menu
            self.conv_service.end_conversation(phone_number)
            return await self._start_new_conversation(phone_number, "hi")
        
        # Check if this step has next_steps (button/list selection expected, not text)
        if "next_steps" in current_step_def:
            logger.warning(f"⚠️ Text received but button/list selection expected at step {conversation.current_step}")
            await send_whatsapp_message(
                phone_number,
                {"type": "text", "content": "Please select one of the options from the menu above."}
            )
            return {"status": "awaiting_selection"}
        
        # Validate input if needed
        if current_step_def.get("validation") == "number":
            try:
                quantity = int(text)
                if quantity <= 0:
                    raise ValueError()
            except ValueError:
                await send_whatsapp_message(
                    phone_number,
                    {"type": "text", "content": "❌ Please enter a valid number"}
                )
                return {"status": "invalid_input"}
        
        # Store input in context
        context_key = current_step_def.get("context_key", "user_input")
        context_update = {context_key: text}
        
        # Move to next step
        next_step = current_step_def.get("next_step")
        if not next_step:
            logger.warning(f"⚠️ No next step defined for {conversation.current_step}, ending conversation")
            # End conversation gracefully
            await send_whatsapp_message(
                phone_number,
                {"type": "text", "content": "Thank you! Type 'menu' to return to the main menu."}
            )
            self.conv_service.end_conversation(phone_number)
            return {"status": "conversation_ended"}
        
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
            {"type": "text", "content": prompt}
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
            logger.error(f"❌ Template not found: {conversation.conversation_flow}")
            return {"status": "error"}
        
        # Get step definition
        steps = template.menu_structure.get("steps", {})
        current_step_def = steps.get(conversation.current_step, {})
        
        # Determine next step based on selection
        next_steps = current_step_def.get("next_steps", {})
        
        logger.info(f"🔘 Processing selection '{selection_id}' at step '{conversation.current_step}'")
        logger.debug(f"Available next_steps: {next_steps}")
        
        if selection_id not in next_steps:
            logger.warning(f"⚠️ Selection '{selection_id}' not found in next_steps")
            return {"status": "invalid_selection"}
        
        next_value = next_steps[selection_id]
        logger.info(f"🎯 Next destination: {next_value}")
        
        # Check if this is a switch to another template
        # If next_value matches a template name, start that template
        next_template = self.conv_service.get_template(next_value)
        
        if next_template:
            # Switch to new template flow
            logger.info(f"🔄 Switching to template: {next_value}")
            self.conv_service.end_conversation(phone_number)
            
            # Start new conversation with the target template
            new_conversation = self.conv_service.start_conversation(
                phone_number=phone_number,
                template_name=next_value
            )
            
            # Send the new template's menu
            await self._send_menu(phone_number, next_template.menu_structure)
            
            return {
                "status": "template_switched",
                "new_template": next_value
            }
        else:
            # Move to next step within current template
            logger.info(f"➡️ Moving to step: {next_value}")
            self.conv_service.update_conversation(
                phone_number=phone_number,
                current_step=next_value,
                context_update={"selection": selection_id}
            )
            
            # Get next step definition and send appropriate message
            next_step_def = steps.get(next_value, {})
            
            if "prompt" in next_step_def:
                prompt = next_step_def["prompt"]
                await send_whatsapp_message(
                    phone_number,
                    {"type": "text", "content": prompt}
                )
            
            return {"status": "step_advanced", "next_step": next_value}
    
    async def _send_menu(self, phone_number: str, menu_structure: Dict[str, Any]):
        """Send WhatsApp interactive menu"""
        
        logger.info(f"📤 Preparing to send menu to {phone_number}, type: {menu_structure.get('type')}")
        
        menu_type = menu_structure.get("type")
        
        if menu_type == "button":
            # Send button message
            body_text = menu_structure.get("body", {}).get("text", "Please select an option")
            action = menu_structure.get("action", {})
            
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body_text},
                    "action": action
                }
            }
            logger.info(f"📋 Sending button message with {len(action.get('buttons', []))} buttons")
            logger.debug(f"Button message: {message}")
            
        elif menu_type == "list":
            # Send list message
            body_text = menu_structure.get("body", {}).get("text", "Please select an option")
            action = menu_structure.get("action", {})
            
            message = {
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {"text": body_text},
                    "action": action
                }
            }
            logger.info(f"📋 Sending list message")
            logger.debug(f"List message: {message}")
            
        else:
            # Send text message
            text_content = menu_structure.get("body", {}).get("text", "Menu")
            message = {
                "type": "text",
                "content": text_content
            }
            logger.info(f"📋 Sending text message")
            logger.debug(f"Text message: {message}")
        
        logger.info(f"🚀 Calling send_whatsapp_message for {phone_number}")
        result = await send_whatsapp_message(phone_number, message)
        logger.info(f"✅ send_whatsapp_message returned: {result}")
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Replace placeholders in prompt with context values"""
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
        return prompt
