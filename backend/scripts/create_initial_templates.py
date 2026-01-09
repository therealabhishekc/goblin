"""
Script to create initial workflow templates
Run: python -m scripts.create_initial_templates

NOTE: Template definitions are left empty for you to fill in.
      Add your menu structures, trigger keywords, and steps as needed.
"""
from app.core.database import init_database, get_db_session
from app.services.conversation_service import ConversationService

def create_main_menu_template(service: ConversationService):
    """
    Create the main menu template for Govindji's Jewelry
    """
    
    menu_structure = {
        "type": "button",
        "body": {
            "text": "✨ Welcome to Govindji's, where you'll experience exquisite craftsmanship and unparalleled quality in Gold and Diamond jewelry that has been trusted for over six decades."
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "explore_collection",
                        "title": "💎 Explore Collection"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "talk_to_expert",
                        "title": "👨‍💼 Talk to Expert"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "visit_us",
                        "title": "📍 Visit Us"
                    }
                }
            ]
        },
        "steps": {
            "initial": {
                "next_steps": {
                    "explore_collection": "show_collection_categories",
                    "talk_to_expert": "connect_expert",
                    "visit_us": "show_location"
                }
            }
        }
    }
    
    service.create_template(
        template_name="main_menu",
        template_type="button",
        menu_structure=menu_structure,
        trigger_keywords=["hi", "hello", "hey", "start", "menu", "help"],
        is_active=True
    )
    
    print("✅ Created main_menu template for Govindji's Jewelry")

def create_additional_templates(service: ConversationService):
    """
    Create additional templates as needed
    
    TODO: Copy this function and create more templates
    """
    
    # Example template structure
    menu_structure = {
        "type": "button",
        "body": {
            "text": "TODO: Add your menu content here"
        },
        "action": {
            "buttons": []  # TODO: Add buttons
        },
        "steps": {}  # TODO: Add steps
    }
    
    # Uncomment and customize:
    # service.create_template(
    #     template_name="your_template_name",
    #     template_type="button",
    #     menu_structure=menu_structure,
    #     trigger_keywords=["keyword1", "keyword2"],
    #     is_active=True
    # )
    
    print("ℹ️  Additional templates not created yet - customize create_additional_templates()")

def main():
    """Create all initial templates"""
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║              Creating Initial Workflow Templates                             ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("⚠️  NOTE: Template structures are left empty for you to customize.")
    print("    Edit this file to add your menu content, buttons, and flows.")
    print("")
    
    init_database()
    
    with get_db_session() as db:
        service = ConversationService(db)
        
        # Create templates
        print("Creating templates...")
        print("")
        
        create_main_menu_template(service)
        create_additional_templates(service)
    
    print("")
    print("✅ Template creation script completed!")
    print("")
    print("Next steps:")
    print("  1. Edit scripts/create_initial_templates.py to customize templates")
    print("  2. Add your menu structures, buttons, and conversation flows")
    print("  3. Run this script again: python -m scripts.create_initial_templates")
    print("  4. Test by sending trigger keywords to your WhatsApp number")
    print("")
    print("For examples, see: COMPLETE_CONVERSATION_IMPLEMENTATION_GUIDE.md")
    print("")

if __name__ == "__main__":
    main()
