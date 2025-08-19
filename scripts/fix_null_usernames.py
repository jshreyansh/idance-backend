#!/usr/bin/env python3
"""
Fix Null Usernames Script
This script fixes existing users with null usernames by generating unique usernames
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import re
import random
import string

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

async def generate_unique_username(db, users_collection: str, base_name: str) -> str:
    """
    Generate a unique username based on the user's name
    """
    # Clean the base name: remove special chars, convert to lowercase
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', base_name.lower())
    
    # If clean name is empty, use 'user'
    if not clean_name:
        clean_name = 'user'
    
    # Try the clean name first
    username = clean_name
    counter = 1
    
    # Keep trying until we find a unique username
    while True:
        existing_user = await db[users_collection].find_one({"profile.username": username})
        if not existing_user:
            return username
        
        # If username exists, append a number
        username = f"{clean_name}{counter}"
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 1000:
            # Generate random username as fallback
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"user{random_suffix}"
            existing_user = await db[users_collection].find_one({"profile.username": username})
            if not existing_user:
                return username

async def fix_null_usernames():
    """Fix users with null usernames"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🔧 Fixing null usernames...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        
        # Get environment from env or default to development
        environment = os.getenv('ENVIRONMENT', 'development')
        print(f"🌍 Environment: {environment}")
        
        # Determine collection name based on environment
        if environment == 'production':
            users_collection = 'users_prod'
        elif environment == 'test':
            users_collection = 'users_test'
        else:
            users_collection = 'users'
        
        print(f"📋 Collection: {users_collection}")
        
        # Find users with null usernames
        null_username_users = await db[users_collection].find({
            "$or": [
                {"profile.username": None},
                {"profile.username": {"$exists": False}},
                {"profile": {"$exists": False}}
            ]
        }).to_list(length=None)
        
        print(f"🔍 Found {len(null_username_users)} users with null usernames")
        
        if not null_username_users:
            print("✅ No users with null usernames found!")
            return
        
        # Fix each user
        fixed_count = 0
        for user in null_username_users:
            try:
                user_id = user['_id']
                
                # Determine base name for username generation
                base_name = None
                
                # Try to get name from profile.displayName
                if user.get('profile', {}).get('displayName'):
                    base_name = user['profile']['displayName']
                # Try to get name from auth.email
                elif user.get('auth', {}).get('email'):
                    base_name = user['auth']['email'].split('@')[0]
                else:
                    base_name = 'user'
                
                # Generate unique username
                username = await generate_unique_username(db, users_collection, base_name)
                
                # Update the user
                update_result = await db[users_collection].update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "profile.username": username,
                            "updatedAt": datetime.utcnow()
                        }
                    },
                    upsert=False
                )
                
                if update_result.modified_count > 0:
                    fixed_count += 1
                    print(f"  ✅ Fixed user {user_id}: {username}")
                else:
                    print(f"  ⚠️  No changes for user {user_id}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing user {user.get('_id', 'unknown')}: {str(e)}")
        
        print(f"\n📊 Summary:")
        print(f"  - Total users with null usernames: {len(null_username_users)}")
        print(f"  - Successfully fixed: {fixed_count}")
        print(f"  - Failed: {len(null_username_users) - fixed_count}")
        
        if fixed_count > 0:
            print(f"\n✅ Successfully fixed {fixed_count} users!")
        else:
            print(f"\n⚠️  No users were fixed.")
        
    except Exception as e:
        print(f"❌ Error fixing null usernames: {str(e)}")
        raise
    finally:
        client.close()

async def main():
    """Main function"""
    try:
        # Load environment variables
        load_dotenv()
        
        print("🔧 Fix Null Usernames Script")
        print("=" * 40)
        
        # Run the fix
        await fix_null_usernames()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 