#!/usr/bin/env python3
"""
Background jobs for challenge system automation
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from infra.mongo import Database
from services.challenge.service import ChallengeService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundJobService:
    """Service for handling background jobs and automation"""
    
    def __init__(self):
        self.challenge_service = ChallengeService()
    
    async def rotate_daily_challenges(self) -> dict:
        """
        Daily challenge rotation job
        - Deactivates expired challenges
        - Activates new challenges for today
        - Updates challenge statistics
        """
        try:
            logger.info("🔄 Starting daily challenge rotation...")
            
            # Get database connection
            db = Database.get_database()
            
            # 1. Deactivate expired challenges
            expired_count = await self._deactivate_expired_challenges()
            logger.info(f"✅ Deactivated {expired_count} expired challenges")
            
            # 2. Activate today's challenge (if none active)
            activated_count = await self._activate_today_challenge()
            logger.info(f"✅ Activated {activated_count} new challenges")
            
            # 3. Update challenge statistics
            updated_count = await self._update_challenge_statistics()
            logger.info(f"✅ Updated statistics for {updated_count} challenges")
            
            return {
                "success": True,
                "expired_deactivated": expired_count,
                "new_activated": activated_count,
                "statistics_updated": updated_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in challenge rotation: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _deactivate_expired_challenges(self) -> int:
        """Deactivate challenges that have ended"""
        db = Database.get_database()
        now = datetime.utcnow()
        
        result = await db['challenges'].update_many(
            {
                "endTime": {"$lt": now},
                "isActive": True
            },
            {
                "$set": {
                    "isActive": False,
                    "updatedAt": now
                }
            }
        )
        return result.modified_count
    
    async def _activate_today_challenge(self) -> int:
        """Activate a challenge for today if none is active"""
        db = Database.get_database()
        now = datetime.utcnow()
        
        # Check if there's already an active challenge
        active_challenge = await db['challenges'].find_one({
            "isActive": True,
            "startTime": {"$lte": now},
            "endTime": {"$gte": now}
        })
        
        if active_challenge:
            logger.info("ℹ️ Challenge already active for today")
            return 0
        
        # Find the next challenge to activate
        next_challenge = await db['challenges'].find_one({
            "isActive": False,
            "startTime": {"$gte": now},
            "endTime": {"$gte": now}
        }, sort=[("startTime", 1)])
        
        if next_challenge:
            # Activate the challenge
            await db['challenges'].update_one(
                {"_id": next_challenge["_id"]},
                {
                    "$set": {
                        "isActive": True,
                        "updatedAt": now
                    }
                }
            )
            logger.info(f"✅ Activated challenge: {next_challenge['title']}")
            return 1
        else:
            logger.warning("⚠️ No challenges available to activate")
            return 0
    
    async def _update_challenge_statistics(self) -> int:
        """Update challenge statistics (submissions, scores, etc.)"""
        db = Database.get_database()
        
        # Get all active challenges
        active_challenges = await db['challenges'].find({
            "isActive": True
        }).to_list(length=None)
        
        updated_count = 0
        
        for challenge in active_challenges:
            challenge_id = str(challenge["_id"])
            
            # Count submissions for this challenge
            submission_count = await db['challenge_submissions'].count_documents({
                "challengeId": challenge_id
            })
            
            # Calculate average score
            pipeline = [
                {"$match": {"challengeId": challenge_id}},
                {"$group": {
                    "_id": None,
                    "averageScore": {"$avg": "$totalScore"},
                    "topScore": {"$max": "$totalScore"}
                }}
            ]
            
            stats_result = await db['challenge_submissions'].aggregate(pipeline).to_list(length=1)
            
            avg_score = 0.0
            top_score = 0
            
            if stats_result:
                avg_score = stats_result[0].get("averageScore", 0.0) or 0.0
                top_score = stats_result[0].get("topScore", 0) or 0
            
            # Update challenge statistics
            await db['challenges'].update_one(
                {"_id": challenge["_id"]},
                {
                    "$set": {
                        "totalSubmissions": submission_count,
                        "averageScore": round(avg_score, 2),
                        "topScore": top_score,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            updated_count += 1
        
        return updated_count
    
    async def cleanup_old_data(self) -> dict:
        """Clean up old challenge data and submissions"""
        try:
            db = Database.get_database()
            now = datetime.utcnow()
            cutoff_date = now - timedelta(days=90)  # Keep 90 days of data
            
            # Clean up old submissions
            old_submissions = await db['challenge_submissions'].delete_many({
                "submittedAt": {"$lt": cutoff_date}
            })
            
            # Clean up old inactive challenges (older than 30 days)
            old_challenges = await db['challenges'].delete_many({
                "isActive": False,
                "endTime": {"$lt": now - timedelta(days=30)}
            })
            
            return {
                "success": True,
                "old_submissions_deleted": old_submissions.deleted_count,
                "old_challenges_deleted": old_challenges.deleted_count,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global background job service instance
background_job_service = BackgroundJobService() 