import json
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import boto3
import urllib.parse as urlparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Lambda handler for message archival"""
    try:
        logger.info(f"Starting message archival with event: {json.dumps(event)}")
        
        archival_service = MessageArchivalService()
        result = archival_service.archive_old_messages()
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Message archival completed successfully',
                'archived_count': result['archived_count'],
                'execution_time_seconds': result['execution_time'],
                'timestamp': datetime.now().isoformat(),
                'environment': os.environ.get('ENVIRONMENT', 'unknown')
            })
        }
        
        logger.info(f"Archival completed: {result['archived_count']} messages in {result['execution_time']:.2f}s")
        return response
        
    except Exception as e:
        error_msg = f"Message archival failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

class MessageArchivalService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.environ['S3_DATA_BUCKET']
        self.db_url = os.environ['DATABASE_URL']
        self.archive_threshold_days = int(os.environ.get('ARCHIVE_THRESHOLD_DAYS', '90'))
        self.batch_size = int(os.environ.get('BATCH_SIZE', '1000'))
        
        logger.info(f"Initialized with bucket: {self.bucket_name}, threshold: {self.archive_threshold_days} days")
        
    def archive_old_messages(self):
        """Archive messages older than threshold to S3"""
        start_time = datetime.now()
        
        # Parse database URL
        url = urlparse.urlparse(self.db_url)
        
        # Connect to database
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432,
            connect_timeout=30
        )
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.archive_threshold_days)
            logger.info(f"Archiving messages older than {cutoff_date}")
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get old messages in batches
                query = """
                    SELECT id, message_id, from_phone, to_phone, message_type, 
                           content, media_url, status, timestamp, webhook_raw_data,
                           context_message_id, created_at, updated_at
                    FROM whatsapp_messages 
                    WHERE timestamp < %s
                    ORDER BY timestamp
                    LIMIT %s
                """
                
                cursor.execute(query, (cutoff_date, self.batch_size))
                messages = cursor.fetchall()
                
                if not messages:
                    logger.info("No messages to archive")
                    return {'archived_count': 0, 'execution_time': 0}
                
                logger.info(f"Found {len(messages)} messages to archive")
                
                # Group by date for S3 partitioning
                messages_by_date = self._group_messages_by_date(messages)
                
                archived_ids = []
                for date_key, date_messages in messages_by_date.items():
                    try:
                        # Create S3 key with Hive-style partitioning
                        year, month, day = date_key.split('-')
                        s3_key = f"archived_messages/year={year}/month={month}/day={day}/messages_{date_key.replace('-', '')}.json"
                        
                        # Convert to JSON serializable format
                        json_messages = self._prepare_messages_for_json(date_messages)
                        
                        # Upload to S3
                        self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            Body=json.dumps(json_messages, indent=2, default=str),
                            ContentType='application/json',
                            ServerSideEncryption='AES256',
                            Metadata={
                                'archived_at': datetime.now().isoformat(),
                                'message_count': str(len(date_messages)),
                                'date': date_key
                            }
                        )
                        
                        archived_ids.extend([str(msg['id']) for msg in date_messages])
                        logger.info(f"Archived {len(date_messages)} messages to s3://{self.bucket_name}/{s3_key}")
                        
                    except Exception as e:
                        logger.error(f"Failed to archive messages for date {date_key}: {str(e)}")
                        continue
                
                # Delete archived messages from database
                if archived_ids:
                    try:
                        # Convert to UUIDs for PostgreSQL
                        cursor.execute("""
                            DELETE FROM whatsapp_messages 
                            WHERE id::text = ANY(%s)
                        """, (archived_ids,))
                        
                        deleted_count = cursor.rowcount
                        conn.commit()
                        logger.info(f"Deleted {deleted_count} messages from database")
                        
                    except Exception as e:
                        logger.error(f"Failed to delete messages from database: {str(e)}")
                        conn.rollback()
                        raise
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    'archived_count': len(archived_ids),
                    'execution_time': execution_time
                }
                
        finally:
            conn.close()
    
    def _group_messages_by_date(self, messages):
        """Group messages by date for S3 partitioning"""
        groups = {}
        for msg in messages:
            date_key = msg['timestamp'].strftime('%Y-%m-%d')
            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(msg)
        return groups
    
    def _prepare_messages_for_json(self, messages):
        """Convert messages to JSON serializable format"""
        json_messages = []
        for msg in messages:
            json_msg = {
                'id': str(msg['id']),
                'message_id': msg['message_id'],
                'from_phone': msg['from_phone'],
                'to_phone': msg['to_phone'],
                'message_type': msg['message_type'],
                'content': msg['content'],
                'media_url': msg['media_url'],
                'status': msg['status'],
                'timestamp': msg['timestamp'].isoformat() if msg['timestamp'] else None,
                'context_message_id': msg['context_message_id'],
                'webhook_raw_data': msg['webhook_raw_data'],
                'created_at': msg['created_at'].isoformat() if msg['created_at'] else None,
                'updated_at': msg['updated_at'].isoformat() if msg['updated_at'] else None
            }
            json_messages.append(json_msg)
        return json_messages
