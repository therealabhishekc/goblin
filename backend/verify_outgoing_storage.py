"""
Verification script for outgoing message storage
Run this after implementing the changes to verify everything works
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy import select, func, text

def verify_outgoing_storage():
    """Verify that outgoing messages are being stored"""
    
    print("🔍 Verifying outgoing message storage implementation...")
    print("=" * 70)
    
    try:
        from app.core.database import SessionLocal
        from app.models.whatsapp import WhatsAppMessageDB
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("   Make sure you're running from the backend directory")
        return False
    
    db = SessionLocal()
    
    try:
        # Check 1: Verify direction column exists
        print("\n1️⃣  Checking if 'direction' column exists...")
        try:
            result = db.execute(text("SELECT direction FROM whatsapp_messages LIMIT 1")).fetchone()
            print("   ✅ 'direction' column exists in database")
        except Exception as e:
            print(f"   ❌ 'direction' column not found: {e}")
            print("   → ACTION REQUIRED: Run database migration!")
            print("   → Execute: psql -f backend/migrations/add_direction_column.sql")
            return False
        
        # Check 2: Verify message counts
        print("\n2️⃣  Checking message counts...")
        total_count = db.query(func.count(WhatsAppMessageDB.id)).scalar()
        print(f"   Total messages: {total_count}")
        
        incoming_count = db.query(func.count(WhatsAppMessageDB.id)).filter(
            WhatsAppMessageDB.direction == "incoming"
        ).scalar()
        print(f"   Incoming messages: {incoming_count}")
        
        outgoing_count = db.query(func.count(WhatsAppMessageDB.id)).filter(
            WhatsAppMessageDB.direction == "outgoing"
        ).scalar()
        print(f"   Outgoing messages: {outgoing_count}")
        
        if outgoing_count == 0:
            print("\n   ⚠️  WARNING: No outgoing messages found yet")
            print("   → This is normal if no messages have been sent since deployment")
            print("   → Send a test message via API: POST /messaging/send/text")
            print("   → Then run this script again")
        else:
            print(f"\n   ✅ SUCCESS: Found {outgoing_count} outgoing messages!")
        
        # Check 3: Verify recent outgoing messages
        print("\n3️⃣  Checking recent outgoing messages (last 24 hours)...")
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_outgoing = db.query(WhatsAppMessageDB).filter(
            WhatsAppMessageDB.direction == "outgoing",
            WhatsAppMessageDB.timestamp >= recent_cutoff
        ).order_by(WhatsAppMessageDB.timestamp.desc()).limit(5).all()
        
        if recent_outgoing:
            print(f"   Found {len(recent_outgoing)} recent outgoing messages:")
            for msg in recent_outgoing:
                print(f"   • {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | To: {msg.to_phone} | Type: {msg.message_type} | Status: {msg.status}")
        else:
            print("   No recent outgoing messages in last 24 hours")
        
        # Check 4: Verify index exists
        print("\n4️⃣  Checking database index...")
        try:
            index_query = text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'whatsapp_messages' 
                AND indexname = 'idx_messages_direction'
            """)
            result = db.execute(index_query).fetchone()
            if result:
                print("   ✅ Index 'idx_messages_direction' exists")
            else:
                print("   ⚠️  Index 'idx_messages_direction' not found")
                print("   → Consider creating index: CREATE INDEX idx_messages_direction ON whatsapp_messages(direction);")
        except Exception as e:
            print(f"   ⚠️  Could not check index: {e}")
        
        # Check 5: Verify model has direction field
        print("\n5️⃣  Checking model definition...")
        try:
            test_msg = WhatsAppMessageDB()
            if hasattr(test_msg, 'direction'):
                print("   ✅ WhatsAppMessageDB model has 'direction' attribute")
            else:
                print("   ❌ WhatsAppMessageDB model missing 'direction' attribute")
                print("   → Check backend/app/models/whatsapp.py")
                return False
        except Exception as e:
            print(f"   ⚠️  Could not verify model: {e}")
        
        # Final summary
        print("\n" + "=" * 70)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 70)
        
        if outgoing_count > 0:
            print("✅ VERIFICATION COMPLETE: Implementation is working correctly!")
            print(f"   {outgoing_count} outgoing messages are being stored in the database")
        else:
            print("✅ VERIFICATION MOSTLY COMPLETE: Implementation looks good")
            print("   ⚠️  No outgoing messages found yet - send test messages to fully verify")
        
        print("\n💡 Next steps:")
        print("   1. Send test messages via API")
        print("   2. Monitor application logs for storage confirmations")
        print("   3. Check conversation history includes both directions")
        return True
            
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    result = verify_outgoing_storage()
    sys.exit(0 if result else 1)
