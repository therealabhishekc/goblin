"""
Unified S3 Service for WhatsApp Business API
Handles data archival, retrieval, and connection validation for S3 storage
"""
import os
import json
import boto3
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy import text
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.logging import logger

class S3Service:
    """Unified S3 service for archival, retrieval, and validation"""
    
    def __init__(self):
        try:
            self.s3_client = boto3.client('s3')
            self.bucket_name = os.getenv('S3_DATA_BUCKET')
            self.region = os.getenv('AWS_REGION', 'us-east-1')
            self.archive_threshold_days = int(os.getenv('ARCHIVE_THRESHOLD_DAYS', '90'))
            
            if not self.bucket_name:
                raise ValueError("S3_DATA_BUCKET environment variable not set")
            
            # Test connection on initialization
            self._test_connection()
            logger.info(f"✅ S3 service initialized for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("❌ AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 service: {e}")
            raise
    
    # =============================================================================
    # CONNECTION VALIDATION METHODS
    # =============================================================================
    
    def _test_connection(self):
        """Test S3 connection and permissions"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("✅ S3 bucket connection verified")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise ValueError(f"S3 connection error: {e}")
    
    def validate_connection(self) -> dict:
        """Validate S3 connection and return detailed status"""
        validation_result = {
            'connected': False,
            'bucket_exists': False,
            'permissions_valid': False,
            'errors': [],
            'bucket_name': self.bucket_name,
            'region': self.region
        }
        
        # Check environment variables
        if not self.bucket_name:
            validation_result['errors'].append("S3_DATA_BUCKET environment variable not set")
            return validation_result
        
        try:
            # Initialize S3 client
            s3_client = boto3.client('s3', region_name=self.region)
            validation_result['connected'] = True
            
            # Test bucket existence
            try:
                s3_client.head_bucket(Bucket=self.bucket_name)
                validation_result['bucket_exists'] = True
                logger.info(f"✅ S3 bucket '{self.bucket_name}' found")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    validation_result['errors'].append(f"Bucket '{self.bucket_name}' does not exist")
                elif error_code == '403':
                    validation_result['errors'].append(f"Access denied to bucket '{self.bucket_name}'")
                else:
                    validation_result['errors'].append(f"Bucket access error: {e}")
                return validation_result
            
            # Test permissions
            try:
                # Test list permission
                s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
                
                # Test put permission with a test object
                test_key = "test/connection_test.txt"
                s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=test_key,
                    Body=b"Connection test",
                    Metadata={'test': 'true'}
                )
                
                # Test get permission
                s3_client.get_object(Bucket=self.bucket_name, Key=test_key)
                
                # Clean up test object
                s3_client.delete_object(Bucket=self.bucket_name, Key=test_key)
                
                validation_result['permissions_valid'] = True
                logger.info("✅ S3 permissions validated (list, put, get, delete)")
                
            except ClientError as e:
                validation_result['errors'].append(f"Permission test failed: {e}")
                
        except NoCredentialsError:
            validation_result['errors'].append("AWS credentials not found")
        except Exception as e:
            validation_result['errors'].append(f"S3 connection failed: {e}")
        
        return validation_result
    
    def validate_iam_permissions(self) -> dict:
        """Check if IAM permissions are correctly configured"""
        try:
            iam_client = boto3.client('iam', region_name=self.region)
            sts_client = boto3.client('sts', region_name=self.region)
            
            # Get current identity
            identity = sts_client.get_caller_identity()
            
            result = {
                'identity': identity,
                'required_permissions': [
                    's3:GetObject',
                    's3:PutObject', 
                    's3:DeleteObject',
                    's3:ListBucket',
                    's3:GetObjectVersion'
                ],
                'validation_status': 'manual_check_required'
            }
            
            logger.info(f"Current AWS identity: {identity}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to validate IAM permissions: {e}")
            return {'error': str(e)}
    
    # =============================================================================
    # DATA ARCHIVAL METHODS
    # =============================================================================
    
    async def archive_old_messages(self):
        """Archive messages older than threshold to S3"""
        from app.core.database import SessionLocal
        
        cutoff_date = datetime.now() - timedelta(days=self.archive_threshold_days)
        
        with SessionLocal() as db:
            # Query old messages
            query = text("""
                SELECT id, phone_number, message_content, message_type, 
                       timestamp, media_url, status
                FROM messages 
                WHERE timestamp < :cutoff_date
                ORDER BY timestamp
                LIMIT 1000
            """)
            
            result = db.execute(query, {"cutoff_date": cutoff_date})
            messages = result.fetchall()
            
            if not messages:
                logger.info("No messages to archive")
                return
            
            # Group messages by date for efficient S3 storage
            messages_by_date = {}
            for msg in messages:
                date_key = msg.timestamp.strftime('%Y/%m/%d')
                if date_key not in messages_by_date:
                    messages_by_date[date_key] = []
                
                messages_by_date[date_key].append({
                    'id': msg.id,
                    'phone_number': msg.phone_number,
                    'message_content': msg.message_content,
                    'message_type': msg.message_type,
                    'timestamp': msg.timestamp.isoformat(),
                    'media_url': msg.media_url,
                    'status': msg.status
                })
            
            # Upload to S3 and delete from database
            archived_ids = []
            for date_key, date_messages in messages_by_date.items():
                s3_key = f"messages/year={date_key.split('/')[0]}/month={date_key.split('/')[1]}/day={date_key.split('/')[2]}/messages_{date_key.replace('/', '')}.json"
                
                try:
                    # Upload to S3
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Body=json.dumps(date_messages, default=str),
                        ContentType='application/json',
                        Metadata={
                            'archived_date': datetime.now().isoformat(),
                            'message_count': str(len(date_messages))
                        }
                    )
                    
                    # Collect IDs for deletion
                    archived_ids.extend([msg['id'] for msg in date_messages])
                    logger.info(f"Archived {len(date_messages)} messages to {s3_key}")
                    
                except Exception as e:
                    logger.error(f"Failed to archive messages for {date_key}: {e}")
                    continue
            
            # Delete archived messages from database
            if archived_ids:
                delete_query = text("DELETE FROM messages WHERE id = ANY(:ids)")
                db.execute(delete_query, {"ids": archived_ids})
                db.commit()
                logger.info(f"Deleted {len(archived_ids)} archived messages from database")
    
    async def archive_old_media_files(self):
        """Archive media files from URLs to S3"""
        from app.core.database import SessionLocal
        
        cutoff_date = datetime.now() - timedelta(days=30)  # Archive media after 30 days
        
        with SessionLocal() as db:
            query = text("""
                SELECT id, media_url, message_type, timestamp
                FROM messages 
                WHERE media_url IS NOT NULL 
                AND timestamp < :cutoff_date
                AND media_archived = false
                LIMIT 100
            """)
            
            result = db.execute(query, {"cutoff_date": cutoff_date})
            media_messages = result.fetchall()
            
            for msg in media_messages:
                try:
                    # Download media from original URL
                    # This is a simplified example - implement proper media download
                    media_data = await self._download_media(msg.media_url)
                    
                    if media_data:
                        # Generate S3 key for media
                        date_path = msg.timestamp.strftime('%Y/%m')
                        file_ext = self._get_file_extension(msg.message_type)
                        s3_key = f"media/{msg.message_type}s/year={msg.timestamp.year}/month={msg.timestamp.month:02d}/msg_{msg.id}{file_ext}"
                        
                        # Upload to S3
                        self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=s3_key,
                            Body=media_data,
                            Metadata={
                                'original_url': msg.media_url,
                                'message_id': str(msg.id),
                                'archived_date': datetime.now().isoformat()
                            }
                        )
                        
                        # Update database to mark as archived
                        update_query = text("""
                            UPDATE messages 
                            SET media_archived = true, archived_media_url = :s3_url
                            WHERE id = :msg_id
                        """)
                        s3_url = f"s3://{self.bucket_name}/{s3_key}"
                        db.execute(update_query, {"s3_url": s3_url, "msg_id": msg.id})
                        
                        logger.info(f"Archived media for message {msg.id} to {s3_key}")
                
                except Exception as e:
                    logger.error(f"Failed to archive media for message {msg.id}: {e}")
            
            db.commit()
    
    async def _download_media(self, url: str) -> bytes:
        """Download media from URL (implement based on your media source)"""
        # Implement actual media download logic
        # This could be from WhatsApp Business API, local storage, etc.
        pass
    
    def _get_file_extension(self, message_type: str) -> str:
        """Get file extension based on message type"""
        extensions = {
            'image': '.jpg',
            'document': '.pdf',
            'audio': '.ogg',
            'video': '.mp4'
        }
        return extensions.get(message_type, '.bin')
    
    async def run_archival_job(self):
        """Run complete archival process"""
        logger.info("Starting data archival job")
        
        try:
            await self.archive_old_messages()
            await self.archive_old_media_files()
            logger.info("Data archival job completed successfully")
        except Exception as e:
            logger.error(f"Data archival job failed: {e}")
            raise
    
    # =============================================================================
    # DATA RETRIEVAL METHODS
    # =============================================================================
    
    async def retrieve_archived_messages(
        self, 
        phone_number: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve archived messages from S3"""
        try:
            messages = []
            objects_processed = 0
            
            # Build S3 prefix for date range
            prefix = "messages/"
            if start_date:
                year = start_date.year
                month = start_date.month
                prefix = f"messages/year={year}/month={month:02d}/"
            
            # List objects in bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if objects_processed >= limit // 10:  # Limit files to avoid too much processing
                        break
                    
                    # Get object from S3
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
                    # Parse JSON content
                    content = response['Body'].read().decode('utf-8')
                    file_messages = json.loads(content)
                    
                    # Filter messages
                    for msg in file_messages:
                        # Filter by phone number if specified
                        if phone_number and msg.get('phone_number') != phone_number:
                            continue
                        
                        # Filter by date range
                        msg_date = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                        if start_date and msg_date < start_date:
                            continue
                        if end_date and msg_date > end_date:
                            continue
                        
                        messages.append(msg)
                        
                        if len(messages) >= limit:
                            break
                    
                    objects_processed += 1
                    if len(messages) >= limit:
                        break
                
                if len(messages) >= limit:
                    break
            
            logger.info(f"✅ Retrieved {len(messages)} archived messages")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve archived messages: {e}")
            raise
    
    async def retrieve_archived_media(self, message_id: str) -> Optional[bytes]:
        """Retrieve archived media file by message ID"""
        try:
            # Search for media file
            prefix = f"media/"
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if f"msg_{message_id}" in obj['Key']:
                        # Found the media file
                        response = self.s3_client.get_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        
                        media_data = response['Body'].read()
                        logger.info(f"✅ Retrieved media for message {message_id}")
                        return media_data
            
            logger.warning(f"⚠️  Media not found for message {message_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve media for message {message_id}: {e}")
            raise
    
    async def search_archived_conversations(
        self, 
        phone_number: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Search archived conversations for a specific phone number"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return await self.retrieve_archived_messages(
            phone_number=phone_number,
            start_date=start_date,
            end_date=end_date,
            limit=500
        )
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        try:
            stats = {
                'total_objects': 0,
                'total_size_bytes': 0,
                'message_files': 0,
                'media_files': 0,
                'storage_classes': {}
            }
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.bucket_name):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    stats['total_objects'] += 1
                    stats['total_size_bytes'] += obj['Size']
                    
                    if obj['Key'].startswith('messages/'):
                        stats['message_files'] += 1
                    elif obj['Key'].startswith('media/'):
                        stats['media_files'] += 1
                    
                    # Track storage classes
                    storage_class = obj.get('StorageClass', 'STANDARD')
                    stats['storage_classes'][storage_class] = stats['storage_classes'].get(storage_class, 0) + 1
            
            # Convert bytes to human readable
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
            stats['total_size_gb'] = round(stats['total_size_bytes'] / (1024 * 1024 * 1024), 2)
            
            logger.info(f"✅ Storage stats: {stats['total_objects']} objects, {stats['total_size_gb']} GB")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get storage statistics: {e}")
            raise
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def test_connection_cli(self):
        """CLI function to test S3 connection"""
        result = self.validate_connection()
        
        print("S3 Connection Validation Results:")
        print("=" * 40)
        print(f"Bucket Name: {result['bucket_name']}")
        print(f"Region: {result['region']}")
        print(f"Connected: {'✅' if result['connected'] else '❌'}")
        print(f"Bucket Exists: {'✅' if result['bucket_exists'] else '❌'}")
        print(f"Permissions Valid: {'✅' if result['permissions_valid'] else '❌'}")
        
        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  ❌ {error}")
        else:
            print("\n✅ All checks passed! S3 is properly connected.")
        
        return result


# =============================================================================
# GLOBAL INSTANCE AND FACTORY FUNCTIONS
# =============================================================================

# Global instance
_s3_service = None

def get_s3_service() -> S3Service:
    """Get or create S3 service instance"""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service

# Legacy compatibility functions
def get_s3_retrieval_service() -> S3Service:
    """Legacy compatibility - returns unified S3 service"""
    return get_s3_service()

def test_s3_connection():
    """CLI function to test S3 connection"""
    try:
        service = get_s3_service()
        return service.test_connection_cli()
    except Exception as e:
        print(f"❌ Failed to initialize S3 service: {e}")
        return {
            'connected': False,
            'bucket_exists': False,
            'permissions_valid': False,
            'errors': [str(e)]
        }

# =============================================================================
# CLI AND DIRECT EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_s3_connection()
        elif command == "archive":
            service = get_s3_service()
            asyncio.run(service.run_archival_job())
        elif command == "stats":
            service = get_s3_service()
            stats = asyncio.run(service.get_storage_statistics())
            print(json.dumps(stats, indent=2))
        else:
            print("Usage: python s3_service.py [test|archive|stats]")
    else:
        # Default: run connection test
        test_s3_connection()
