import json
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import boto3
import requests
import urllib.parse as urlparse
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Lambda handler for media archival"""
    try:
        logger.info(f"Starting media archival with event: {json.dumps(event)}")
        
        media_service = MediaArchivalService()
        result = media_service.archive_old_media()
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Media archival completed successfully',
                'archived_files': result['archived_files'],
                'total_size_mb': result['total_size_mb'],
                'failed_downloads': result['failed_downloads'],
                'timestamp': datetime.now().isoformat(),
                'environment': os.environ.get('ENVIRONMENT', 'unknown')
            })
        }
        
        logger.info(f"Media archival completed: {result['archived_files']} files, {result['total_size_mb']} MB")
        return response
        
    except Exception as e:
        error_msg = f"Media archival failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

class MediaArchivalService:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.rds_client = boto3.client('rds')
        self.secrets_client = boto3.client('secretsmanager')
        self.bucket_name = os.environ['S3_DATA_BUCKET']
        self.db_url = os.environ['DATABASE_URL']
        self.media_threshold_days = int(os.environ.get('MEDIA_THRESHOLD_DAYS', '0'))
        self.batch_size = int(os.environ.get('BATCH_SIZE', '50'))
        self.secrets_name = os.environ.get('WHATSAPP_SECRETS_NAME')
        self.whatsapp_token = None
        
        logger.info(f"Initialized with bucket: {self.bucket_name}, threshold: {self.media_threshold_days} days")
        
    def _get_iam_auth_token(self, hostname, port, username):
        """Generate IAM authentication token for RDS"""
        try:
            token = self.rds_client.generate_db_auth_token(
                DBHostname=hostname,
                Port=port,
                DBUsername=username,
                Region=os.environ.get('AWS_REGION', 'us-east-1')
            )
            return token
        except Exception as e:
            logger.error(f"Failed to generate IAM auth token: {str(e)}")
            raise
    
    def _get_whatsapp_token(self):
        """Retrieve WhatsApp access token from Secrets Manager"""
        if self.whatsapp_token:
            return self.whatsapp_token
            
        try:
            if not self.secrets_name:
                logger.error("WHATSAPP_SECRETS_NAME environment variable not set")
                return None
                
            response = self.secrets_client.get_secret_value(SecretId=self.secrets_name)
            secrets = json.loads(response['SecretString'])
            self.whatsapp_token = secrets.get('WHATSAPP_TOKEN') or secrets.get('whatsapp_token')
            
            if not self.whatsapp_token:
                logger.error("WhatsApp token not found in secrets")
                return None
                
            logger.info("Successfully retrieved WhatsApp access token")
            return self.whatsapp_token
            
        except ClientError as e:
            logger.error(f"Failed to retrieve WhatsApp token from Secrets Manager: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting WhatsApp token: {str(e)}")
            return None
        
    def archive_old_media(self):
        """Archive old media files to S3"""
        # Parse database URL
        url = urlparse.urlparse(self.db_url)
        
        # Get IAM authentication token
        db_host = url.hostname
        db_port = url.port or 5432
        db_user = url.username or 'app_user'
        # Remove query string from path
        db_path = url.path.split('?')[0] if url.path else ''
        db_name = db_path[1:] if db_path else 'whatsapp_business_development'
        
        logger.info(f"Connecting to RDS at {db_host}:{db_port} as {db_user} using IAM authentication")
        
        # Generate IAM auth token
        auth_token = self._get_iam_auth_token(db_host, db_port, db_user)
        
        # Connect to database with IAM authentication
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=auth_token,
            host=db_host,
            port=db_port,
            sslmode='require',
            connect_timeout=30
        )
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.media_threshold_days)
            logger.info(f"Archiving media files older than {cutoff_date}")
            logger.info(f"Query parameters: cutoff_date={cutoff_date}, batch_size={self.batch_size} (type: {type(self.batch_size)})")
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get messages with media URLs that haven't been archived
                query = f"""
                    SELECT id, message_id, media_url, message_type, timestamp, from_phone
                    FROM whatsapp_messages 
                    WHERE media_url IS NOT NULL 
                    AND timestamp < %s
                    AND media_url NOT LIKE 's3://%%'
                    AND media_url != ''
                    AND media_url NOT LIKE '%%archived%%'
                    ORDER BY timestamp
                    LIMIT {self.batch_size}
                """
                
                cursor.execute(query, (cutoff_date,))
                media_messages = cursor.fetchall()
                
                if not media_messages:
                    logger.info("No media files to archive")
                    return {
                        'archived_files': 0,
                        'total_size_mb': 0,
                        'failed_downloads': 0
                    }
                
                logger.info(f"Found {len(media_messages)} media files to archive")
                
                archived_files = 0
                total_size = 0
                failed_downloads = 0
                
                for msg in media_messages:
                    try:
                        result = self._archive_single_media(msg, cursor)
                        if result['success']:
                            archived_files += 1
                            total_size += result['size']
                        else:
                            failed_downloads += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to archive media {msg['message_id']}: {str(e)}")
                        failed_downloads += 1
                        continue
                
                # Commit all database updates
                conn.commit()
                logger.info(f"Committed database updates for {archived_files} files")
                
                return {
                    'archived_files': archived_files,
                    'total_size_mb': round(total_size / (1024 * 1024), 2),
                    'failed_downloads': failed_downloads
                }
                
        finally:
            conn.close()
    
    def _archive_single_media(self, msg, cursor):
        """Archive a single media file"""
        try:
            # Get WhatsApp access token
            whatsapp_token = self._get_whatsapp_token()
            if not whatsapp_token:
                logger.warning(f"No WhatsApp token available for downloading media {msg['message_id']}")
                return {'success': False, 'size': 0}
            
            # Download media file with timeout and retry
            headers = {
                'Authorization': f'Bearer {whatsapp_token}',
                'User-Agent': 'WhatsApp-Archival-Bot/1.0'
            }
            
            response = requests.get(
                msg['media_url'], 
                timeout=60,
                headers=headers,
                stream=True,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                media_data = response.content
                
                if len(media_data) == 0:
                    logger.warning(f"Empty media file for message {msg['message_id']}")
                    return {'success': False, 'size': 0}
                
                # Generate S3 key with date partitioning
                date_path = msg['timestamp'].strftime('%Y/%m/%d')
                file_ext = self._get_file_extension(msg['message_type'], msg['media_url'])
                phone_hash = str(hash(msg['from_phone']))[-4:]  # Last 4 digits for organization
                
                s3_key = f"archived_media/{msg['message_type']}/{date_path}/{phone_hash}_{msg['message_id']}{file_ext}"
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=media_data,
                    ContentType=self._get_content_type(msg['message_type']),
                    ServerSideEncryption='AES256',
                    Metadata={
                        'original_url': msg['media_url'][:500],  # Truncate long URLs
                        'message_id': msg['message_id'],
                        'message_type': msg['message_type'],
                        'archived_at': datetime.now().isoformat(),
                        'file_size': str(len(media_data))
                    }
                )
                
                # Update database with S3 URL
                s3_url = f"s3://{self.bucket_name}/{s3_key}"
                cursor.execute("""
                    UPDATE whatsapp_messages 
                    SET media_url = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (s3_url, msg['id']))
                
                logger.info(f"Archived media: {s3_key} ({len(media_data)} bytes)")
                
                return {'success': True, 'size': len(media_data)}
                
            else:
                logger.warning(f"Failed to download media for message {msg['message_id']}: HTTP {response.status_code}")
                return {'success': False, 'size': 0}
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout downloading media for message {msg['message_id']}")
            return {'success': False, 'size': 0}
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error downloading media for message {msg['message_id']}: {str(e)}")
            return {'success': False, 'size': 0}
        except ClientError as e:
            logger.error(f"S3 error uploading media for message {msg['message_id']}: {str(e)}")
            return {'success': False, 'size': 0}
    
    def _get_file_extension(self, message_type, url):
        """Get file extension based on message type and URL"""
        # Try to get extension from URL first
        if url:
            try:
                path = urlparse.urlparse(url).path
                if '.' in path:
                    ext = '.' + path.split('.')[-1].lower()
                    if len(ext) <= 5:  # Reasonable extension length
                        return ext
            except:
                pass
        
        # Fallback to message type mapping
        extensions = {
            'image': '.jpg',
            'document': '.pdf',
            'audio': '.ogg',
            'video': '.mp4',
            'sticker': '.webp'
        }
        return extensions.get(message_type, '.bin')
    
    def _get_content_type(self, message_type):
        """Get content type based on message type"""
        content_types = {
            'image': 'image/jpeg',
            'document': 'application/pdf',
            'audio': 'audio/ogg',
            'video': 'video/mp4',
            'sticker': 'image/webp'
        }
        return content_types.get(message_type, 'application/octet-stream')
