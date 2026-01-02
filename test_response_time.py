#!/usr/bin/env python3
"""
Test script to calculate and update response time average for business metrics.
This script will:
1. Calculate response time for today (or a specified date)
2. Update the business_metrics table with the calculated average
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db_session, init_database
from app.repositories.analytics_repository import AnalyticsRepository
from app.core.logging import logger

# Initialize database
init_database()

def test_response_time_calculation(days_back: int = 0):
    """
    Calculate and update response time for a specific day.
    
    Args:
        days_back: Number of days back from today (0 = today, 1 = yesterday, etc.)
    """
    target_date = datetime.utcnow() - timedelta(days=days_back)
    
    logger.info("=" * 80)
    logger.info(f"🧪 Testing Response Time Calculation for {target_date.date()}")
    logger.info("=" * 80)
    
    try:
        with get_db_session() as db:
            analytics_repo = AnalyticsRepository(db)
            
            # Get current metrics before update
            before_metrics = analytics_repo.get_metrics_by_date(target_date)
            if before_metrics:
                logger.info(f"📊 Current metrics for {target_date.date()}:")
                logger.info(f"   - Messages received: {before_metrics.total_messages_received}")
                logger.info(f"   - Responses sent: {before_metrics.total_responses_sent}")
                logger.info(f"   - Unique users: {before_metrics.unique_users}")
                logger.info(f"   - Response time avg: {before_metrics.response_time_avg_seconds}s")
            else:
                logger.info(f"⚠️  No metrics found for {target_date.date()} yet")
            
            # Calculate and update response time
            logger.info("\n🔄 Calculating response time average...")
            updated_metrics = analytics_repo.update_response_time_avg(target_date)
            
            if updated_metrics and updated_metrics.response_time_avg_seconds:
                logger.info("\n✅ Response time calculation completed successfully!")
                logger.info(f"📊 Updated metrics for {target_date.date()}:")
                logger.info(f"   - Response time avg: {updated_metrics.response_time_avg_seconds:.2f}s")
                logger.info(f"   - Response time avg: {updated_metrics.response_time_avg_seconds / 60:.2f} minutes")
            else:
                logger.info("\n⚠️  No response time data available for this date")
                logger.info("   This could mean:")
                logger.info("   - No incoming messages received")
                logger.info("   - No outgoing responses sent")
                logger.info("   - No matching conversation pairs found")
    
    except Exception as e:
        logger.error(f"❌ Error during test: {e}", exc_info=True)
        return False
    
    logger.info("=" * 80)
    return True

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test response time calculation for business metrics"
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=0,
        help='Number of days back from today (0 = today, 1 = yesterday, etc.)'
    )
    parser.add_argument(
        '--range',
        type=int,
        help='Calculate for a range of days (e.g., --range 7 for last 7 days)'
    )
    
    args = parser.parse_args()
    
    if args.range:
        logger.info(f"📅 Calculating response times for last {args.range} days\n")
        for days_back in range(args.range):
            test_response_time_calculation(days_back)
            print()  # Add spacing between days
    else:
        test_response_time_calculation(args.days_back)

if __name__ == "__main__":
    main()
