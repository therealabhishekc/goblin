#!/usr/bin/env python3
"""
Test script to validate S3 connection for WhatsApp Business API
"""
import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.s3_service import test_s3_connection, get_s3_service

async def test_archival_service():
    """Test the archival service"""
    print("\n" + "="*50)
    print("TESTING ARCHIVAL SERVICE")
    print("="*50)
    
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

async def test_retrieval_service():
    """Test the retrieval service"""
    print("\n" + "="*50)
    print("TESTING RETRIEVAL SERVICE")
    print("="*50)
    
    try:
        s3_service = get_s3_service()
        print("✅ S3 service initialized successfully")
        
        # Test getting storage stats
        stats = await s3_service.get_storage_statistics()
        print(f"✅ Storage stats retrieved: {stats['total_objects']} objects")
        
        return True
        
    except Exception as e:
        print(f"❌ S3 service failed: {e}")
        return False

def check_environment_variables():
    """Check required environment variables"""
    print("\n" + "="*50)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("="*50)
    
    required_vars = {
        'S3_DATA_BUCKET': 'S3 bucket name for data storage',
        'AWS_REGION': 'AWS region (defaults to us-east-1)',
        'AWS_ACCESS_KEY_ID': 'AWS access key (or use IAM role)',
        'AWS_SECRET_ACCESS_KEY': 'AWS secret key (or use IAM role)'
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                # Don't show actual keys
                print(f"✅ {var}: *** (set)")
            else:
                print(f"✅ {var}: {value}")
        else:
            if var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
                print(f"⚠️  {var}: Not set (using IAM role or default credentials)")
            else:
                print(f"❌ {var}: Not set - {description}")
                all_good = False
    
    return all_good

async def main():
    """Run all tests"""
    print("WhatsApp Business API - S3 Connection Test")
    print("="*60)
    
    # Check environment variables
    env_ok = check_environment_variables()
    
    # Test S3 connection
    connection_result = test_s3_connection()
    
    # Test archival service
    archival_ok = await test_archival_service()
    
    # Test retrieval service (only if connection is working)
    retrieval_ok = False
    if connection_result.get('connected') and connection_result.get('bucket_exists'):
        retrieval_ok = await test_retrieval_service()
    else:
        print("\n❌ Skipping retrieval test due to connection issues")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if (env_ok and connection_result.get('connected') and 
        connection_result.get('bucket_exists') and 
        connection_result.get('permissions_valid') and
        archival_ok and retrieval_ok):
        print("🎉 ALL TESTS PASSED! S3 is properly connected for archival and retrieval.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
