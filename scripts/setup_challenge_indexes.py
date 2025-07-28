#!/usr/bin/env python3
"""
Setup script for challenge system database indexes
Run this script to create optimized indexes for the challenge collections
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

async def setup_challenge_indexes():
    """Create indexes for challenge collections"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    print("🔧 Setting up challenge system indexes...")
    
    # Indexes for challenges collection
    print("📊 Creating indexes for 'challenges' collection...")
    
    # Index for active challenges query (most common)
    await db['challenges'].create_index([
        ("isActive", 1),
        ("startTime", 1),
        ("endTime", 1)
    ], name="active_challenges")
    
    # Index for challenge type and difficulty filtering
    await db['challenges'].create_index([
        ("type", 1),
        ("difficulty", 1)
    ], name="challenge_type_difficulty")
    
    # Index for admin queries (createdBy)
    await db['challenges'].create_index([
        ("createdBy", 1),
        ("createdAt", -1)
    ], name="admin_challenges")
    
    # Index for date range queries
    await db['challenges'].create_index([
        ("startTime", 1),
        ("endTime", 1)
    ], name="date_range")
    
    # Index for sorting by creation date
    await db['challenges'].create_index([
        ("createdAt", -1)
    ], name="created_at_desc")
    
    print("✅ 'challenges' indexes created successfully!")
    
    # Indexes for challenge_submissions collection
    print("📊 Creating indexes for 'challenge_submissions' collection...")
    
    # Compound index for challenge submissions (most common query)
    await db['challenge_submissions'].create_index([
        ("challengeId", 1),
        ("userId", 1)
    ], name="challenge_user_submission", unique=True)
    
    # Index for submission date queries
    await db['challenge_submissions'].create_index([
        ("submittedAt", -1)
    ], name="submission_date")
    
    # Index for score-based leaderboard queries
    await db['challenge_submissions'].create_index([
        ("challengeId", 1),
        ("totalScore", -1)
    ], name="leaderboard_score")
    
    # Index for user's submission history
    await db['challenge_submissions'].create_index([
        ("userId", 1),
        ("submittedAt", -1)
    ], name="user_submissions")
    
    print("✅ 'challenge_submissions' indexes created successfully!")
    
    # Indexes for user_badges collection
    print("📊 Creating indexes for 'user_badges' collection...")
    
    # Index for user's badges
    await db['user_badges'].create_index([
        ("userId", 1),
        ("earnedAt", -1)
    ], name="user_badges")
    
    # Index for badge type queries
    await db['user_badges'].create_index([
        ("badgeName", 1),
        ("userId", 1)
    ], name="badge_user", unique=True)
    
    print("✅ 'user_badges' indexes created successfully!")
    
    # Indexes for leaderboards collection
    print("📊 Creating indexes for 'leaderboards' collection...")
    
    # Index for challenge leaderboards
    await db['leaderboards'].create_index([
        ("challengeId", 1),
        ("rank", 1)
    ], name="challenge_leaderboard")
    
    # Index for global leaderboards
    await db['leaderboards'].create_index([
        ("period", 1),
        ("rank", 1)
    ], name="global_leaderboard")
    
    print("✅ 'leaderboards' indexes created successfully!")
    
    print("\n🎉 All challenge system indexes created successfully!")
    
    # Print index information
    print("\n📋 Index Summary:")
    collections = ['challenges', 'challenge_submissions', 'user_badges', 'leaderboards']
    
    for collection_name in collections:
        print(f"\n📊 {collection_name} indexes:")
        indexes = await db[collection_name].list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['key']}")
    
    client.close()

async def verify_indexes():
    """Verify that indexes were created correctly"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    print("\n🔍 Verifying indexes...")
    
    collections = ['challenges', 'challenge_submissions', 'user_badges', 'leaderboards']
    
    for collection_name in collections:
        try:
            indexes = await db[collection_name].list_indexes().to_list(length=None)
            print(f"✅ {collection_name}: {len(indexes)} indexes found")
        except Exception as e:
            print(f"❌ {collection_name}: Error - {e}")
    
    client.close()

if __name__ == "__main__":
    print("🚀 Challenge System Database Setup")
    print("=" * 50)
    
    asyncio.run(setup_challenge_indexes())
    asyncio.run(verify_indexes())
    
    print("\n✅ Setup complete! Your challenge system is ready for data.") 