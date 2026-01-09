"""
AWS Lambda function to expire old agent sessions
Triggered by EventBridge every 5 minutes
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any
import logging

# Import AWS and HTTP libraries
try:
    import boto3
    from sqlalchemy import create_engine, text
    import httpx
except ImportError as e:
    print(f"Import error: {e}")
    raise

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')

def lambda_handler(event, context):
    """
    Main Lambda handler - expires old agent sessions
    """
    logger.info("🕒 Agent expiration check starting...")
    
    try:
        # Create database connection
        db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(db_url, pool_pre_ping=True)
        
        # Expire old sessions
        expired_sessions = expire_sessions(engine)
        
        # Send WhatsApp notifications
        if expired_sessions:
            notifications_sent = send_whatsapp_notifications(expired_sessions)
            logger.info(f"✅ Expired {len(expired_sessions)} sessions, sent {notifications_sent} notifications")
        else:
            logger.info("✅ No sessions to expire")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Agent expiration check completed',
                'expired_count': len(expired_sessions),
                'notifications_sent': notifications_sent if expired_sessions else 0
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error in lambda handler: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing agent expiration',
                'error': str(e)
            })
        }

def expire_sessions(engine) -> List[Dict[str, Any]]:
    """
    Find and expire sessions that are past their expiration time
    
    Returns:
        List of expired session data with phone numbers
    """
    try:
        with engine.connect() as conn:
            # Update expired sessions and return their data
            result = conn.execute(text("""
                UPDATE agent_sessions
                SET 
                    status = 'ended',
                    ended_at = NOW()
                WHERE status IN ('waiting', 'active')
                  AND expires_at <= NOW()
                RETURNING 
                    id,
                    conversation_id,
                    agent_id,
                    agent_name,
                    status,
                    started_at,
                    expires_at
            """))
            
            conn.commit()
            
            expired = result.fetchall()
            
            if not expired:
                return []
            
            # Get phone numbers for notifications
            expired_sessions = []
            for row in expired:
                # Get phone number from conversation
                conv_result = conn.execute(text("""
                    SELECT phone_number
                    FROM conversation_state
                    WHERE id = :conv_id
                """), {"conv_id": row[1]})
                
                phone_row = conv_result.fetchone()
                
                if phone_row:
                    expired_sessions.append({
                        'session_id': str(row[0]),
                        'conversation_id': str(row[1]),
                        'agent_id': row[2],
                        'agent_name': row[3],
                        'phone_number': phone_row[0],
                        'started_at': row[5].isoformat() if row[5] else None,
                        'expires_at': row[6].isoformat() if row[6] else None
                    })
                    
                    # Add system message to session
                    conn.execute(text("""
                        INSERT INTO agent_messages (session_id, sender_type, message_text)
                        VALUES (:session_id, 'system', 'Session expired after 22 hours')
                    """), {"session_id": row[0]})
                
                conn.commit()
            
            logger.info(f"💀 Expired {len(expired_sessions)} sessions")
            return expired_sessions
            
    except Exception as e:
        logger.error(f"❌ Error expiring sessions: {e}", exc_info=True)
        raise

def send_whatsapp_notifications(sessions: List[Dict[str, Any]]) -> int:
    """
    Send WhatsApp notifications to customers about expired sessions
    
    Args:
        sessions: List of expired session data
        
    Returns:
        Number of successful notifications
    """
    sent_count = 0
    
    for session in sessions:
        try:
            phone_number = session['phone_number']
            
            # Send notification via WhatsApp API
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{WHATSAPP_API_URL}/api/messaging/send",
                    json={
                        "phone_number": phone_number,
                        "message": {
                            "type": "text",
                            "content": (
                                "⏰ Your chat session has expired after 22 hours.\n\n"
                                "Type 'menu' to return to the main menu."
                            )
                        }
                    }
                )
                
                if response.status_code == 200:
                    sent_count += 1
                    logger.info(f"✅ Notification sent to {phone_number}")
                else:
                    logger.warning(f"⚠️ Failed to notify {phone_number}: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"❌ Error sending notification to {session.get('phone_number')}: {e}")
            continue
    
    return sent_count
