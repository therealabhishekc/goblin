"""
Example of how to connect using Secrets Manager password
(This is NOT currently implemented in your app)
"""
import boto3
import json
from botocore.exceptions import ClientError

def get_secret_manager_password():
    """Retrieve database password from AWS Secrets Manager"""
    secret_name = f"rds-db-credentials/whatsapp-postgres-{environment}"
    region_name = "us-east-1"
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret['password']
    except ClientError as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise

def create_database_url_with_secrets():
    """Create database URL using Secrets Manager password"""
    password = get_secret_manager_password()
    url = f"postgresql://postgres:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return url
