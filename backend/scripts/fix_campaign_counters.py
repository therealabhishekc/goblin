#!/usr/bin/env python3
"""
Script to recalculate campaign counters based on actual recipient statuses.

This script fixes campaign-level counters that may have become out of sync
before the fix was applied to update_recipient_status().

Usage:
    python scripts/fix_campaign_counters.py
    python scripts/fix_campaign_counters.py --campaign-id <UUID>
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db_session
from app.models.marketing import MarketingCampaignDB, CampaignRecipientDB
from sqlalchemy import func, and_


def recalculate_campaign_counters(campaign_id=None):
    """
    Recalculate campaign counters based on actual recipient statuses
    
    Args:
        campaign_id: Optional UUID of specific campaign to fix. If None, fixes all campaigns.
    """
    with get_db_session() as db:
        # Get campaigns to fix
        query = db.query(MarketingCampaignDB)
        if campaign_id:
            query = query.filter(MarketingCampaignDB.id == campaign_id)
        
        campaigns = query.all()
        
        if not campaigns:
            print("❌ No campaigns found")
            return
        
        print(f"📊 Found {len(campaigns)} campaign(s) to recalculate\n")
        
        total_fixed = 0
        for campaign in campaigns:
            print(f"Processing: {campaign.name} (ID: {campaign.id})")
            print(f"  Current counters:")
            print(f"    Sent: {campaign.messages_sent}")
            print(f"    Delivered: {campaign.messages_delivered}")
            print(f"    Read: {campaign.messages_read}")
            print(f"    Failed: {campaign.messages_failed}")
            print(f"    Pending: {campaign.messages_pending}")
            
            # Count recipients by status
            recipient_counts = db.query(
                func.count().filter(CampaignRecipientDB.status == 'sent').label('sent'),
                func.count().filter(CampaignRecipientDB.status == 'delivered').label('delivered'),
                func.count().filter(CampaignRecipientDB.status == 'read').label('read'),
                func.count().filter(CampaignRecipientDB.status == 'failed').label('failed'),
                func.count().filter(CampaignRecipientDB.status == 'pending').label('pending'),
                func.count().filter(CampaignRecipientDB.status == 'queued').label('queued'),
                func.count().filter(CampaignRecipientDB.status == 'skipped').label('skipped')
            ).filter(
                CampaignRecipientDB.campaign_id == campaign.id
            ).first()
            
            # Calculate totals
            # Note: delivered and read statuses mean the message was also sent
            actual_sent = (recipient_counts.sent or 0) + (recipient_counts.delivered or 0) + (recipient_counts.read or 0)
            actual_delivered = (recipient_counts.delivered or 0) + (recipient_counts.read or 0)
            actual_read = recipient_counts.read or 0
            actual_failed = recipient_counts.failed or 0
            actual_pending = recipient_counts.pending or 0
            
            print(f"  Actual counts:")
            print(f"    Sent: {actual_sent}")
            print(f"    Delivered: {actual_delivered}")
            print(f"    Read: {actual_read}")
            print(f"    Failed: {actual_failed}")
            print(f"    Pending: {actual_pending}")
            
            # Check if update needed
            needs_update = (
                campaign.messages_sent != actual_sent or
                campaign.messages_delivered != actual_delivered or
                campaign.messages_read != actual_read or
                campaign.messages_failed != actual_failed or
                campaign.messages_pending != actual_pending
            )
            
            if needs_update:
                # Update campaign counters
                campaign.messages_sent = actual_sent
                campaign.messages_delivered = actual_delivered
                campaign.messages_read = actual_read
                campaign.messages_failed = actual_failed
                campaign.messages_pending = actual_pending
                
                print(f"  ✅ Updated counters")
                total_fixed += 1
            else:
                print(f"  ✓ Counters already correct")
            
            print()
        
        # Commit all changes
        if total_fixed > 0:
            db.commit()
            print(f"🎉 Fixed {total_fixed} campaign(s)")
        else:
            print(f"✓ All campaigns already have correct counters")


def main():
    parser = argparse.ArgumentParser(
        description="Recalculate campaign counters based on actual recipient statuses"
    )
    parser.add_argument(
        '--campaign-id',
        type=str,
        help='UUID of specific campaign to fix (optional, defaults to all campaigns)'
    )
    
    args = parser.parse_args()
    
    try:
        recalculate_campaign_counters(campaign_id=args.campaign_id)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
