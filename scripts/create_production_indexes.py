#!/usr/bin/env python3
"""
Create Production Indexes Script
This script creates the unique index on username for production environment
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

async def create_production_indexes():
    """Create indexes for production environment"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🔧 Creating production indexes...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        
        # Create unique index on username for production
        users_collection = 'users_prod'
        print(f"📋 Collection: {users_collection}")
        
        try:
            # Create unique index on username
            await db[users_collection].create_index([("profile.username", 1)], unique=True, sparse=True)
            print("  ✅ Created unique index on profile.username")
        except Exception as e:
            print(f"  ⚠️  Warning creating username index: {str(e)}")
        
        try:
            # Create unique index on email
            await db[users_collection].create_index([("auth.email", 1)], unique=True, sparse=True)
            print("  ✅ Created unique index on auth.email")
        except Exception as e:
            print(f"  ⚠️  Warning creating email index: {str(e)}")
        
        try:
            # Create index on providerId
            await db[users_collection].create_index([("auth.providerId", 1)], sparse=True)
            print("  ✅ Created index on auth.providerId")
        except Exception as e:
            print(f"  ⚠️  Warning creating providerId index: {str(e)}")
        
        print("\n✅ Production indexes created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating production indexes: {str(e)}")
        raise
    finally:
        client.close()

async def main():
    """Main function"""
    try:
        # Load environment variables
        load_dotenv()
        
        print("🔧 Create Production Indexes Script")
        print("=" * 40)
        
        # Run the index creation
        await create_production_indexes()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 