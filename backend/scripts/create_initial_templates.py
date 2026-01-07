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
    Create additional templates for the button options
    """
    
    # Template 1: Explore Collection
    explore_structure = {
        "type": "text",
        "body": {
            "text": "💎 Explore Our Exquisite Collection\n\nAt Govindji's, we offer:\n\n🔸 Gold Jewelry - Traditional & Contemporary designs\n🔸 Diamond Jewelry - Stunning pieces for every occasion\n🔸 Bridal Collection - Make your special day unforgettable\n🔸 Custom Designs - Bring your vision to life\n\nVisit our showroom or website to view our complete collection.\n\nWould you like to speak with our jewelry consultant?"
        },
        "steps": {
            "initial": {
                "prompt": "Type 'yes' to speak with a consultant or 'menu' to return to main menu"
            }
        }
    }
    
    service.create_template(
        template_name="explore_collection",
        template_type="text",
        menu_structure=explore_structure,
        trigger_keywords=["collection", "jewelry", "explore", "catalog"],
        is_active=True
    )
    print("✅ Created explore_collection template")
    
    # Template 2: Talk to Expert
    expert_structure = {
        "type": "text",
        "body": {
            "text": "👨‍💼 Connect with Our Jewelry Experts\n\nOur experienced consultants are here to help you:\n\n✓ Find the perfect piece\n✓ Understand jewelry quality and craftsmanship\n✓ Custom design consultation\n✓ Repair and maintenance services\n\nPlease share your:\n1. Name\n2. What you're looking for\n\nOur expert will contact you shortly!"
        },
        "steps": {
            "initial": {
                "prompt": "Please share your name and requirement",
                "next_step": "collect_details"
            },
            "collect_details": {
                "prompt": "Thank you! Our expert will reach out to you within 24 hours.\n\nType 'menu' to return to main menu."
            }
        }
    }
    
    service.create_template(
        template_name="talk_to_expert",
        template_type="text",
        menu_structure=expert_structure,
        trigger_keywords=["expert", "consultant", "help", "advice"],
        is_active=True
    )
    print("✅ Created talk_to_expert template")
    
    # Template 3: Visit Us
    visit_structure = {
        "type": "text",
        "body": {
            "text": "📍 Visit Govindji's Showroom\n\n🏪 Address:\n[Your Showroom Address]\n[City, State, ZIP]\n\n⏰ Business Hours:\nMonday - Saturday: 10:00 AM - 8:00 PM\nSunday: 11:00 AM - 6:00 PM\n\n📞 Contact:\nPhone: [Your Phone Number]\nEmail: [Your Email]\n\n🚗 We're conveniently located with ample parking.\n\nWould you like directions? Type 'directions' or visit our website for Google Maps link.\n\nType 'menu' to return to main menu."
        },
        "steps": {
            "initial": {
                "prompt": "We look forward to seeing you!"
            }
        }
    }
    
    service.create_template(
        template_name="visit_us",
        template_type="text",
        menu_structure=visit_structure,
        trigger_keywords=["visit", "location", "address", "showroom", "store"],
        is_active=True
    )
    print("✅ Created visit_us template")

def main():
    """Create all initial templates"""
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║              Creating Govindji's Jewelry Templates                            ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("Creating interactive WhatsApp menu templates for Govindji's Jewelry...")
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
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                      Templates Created Successfully! ✅                       ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("📋 Templates Created:")
    print("  1. main_menu - Welcome screen with 3 options")
    print("  2. explore_collection - Collection information")
    print("  3. talk_to_expert - Connect with jewelry consultant")
    print("  4. visit_us - Showroom location and hours")
    print("")
    print("🔑 Trigger Keywords (case-insensitive):")
    print("  • hi, hello, hey → Main menu")
    print("  • collection, jewelry, explore → Collection info")
    print("  • expert, consultant, help → Talk to expert")
    print("  • visit, location, address → Visit us")
    print("")
    print("✅ Next Steps:")
    print("  1. Update 'Visit Us' template with actual address and phone number")
    print("  2. Test by sending 'hi' to your WhatsApp Business number")
    print("  3. Try clicking the buttons to test the flow")
    print("")
    print("📝 To update address/contact info:")
    print("  Edit the visit_structure in create_additional_templates()")
    print("  Then run this script again")
    print("")

if __name__ == "__main__":
    main()
