from motor.motor_asyncio import AsyncIOMotorClient
import os

# Directly declare the working MongoDB URI here
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, test, production

class Database:
    client: AsyncIOMotorClient = None

    @staticmethod
    def get_database():
        assert Database.client is not None, "Database client is not connected."
        return Database.client[DB_NAME]
    
    @staticmethod
    def get_collection_name(base_name: str) -> str:
        """
        Get environment-specific collection name
        Examples:
        - development: users, challenges, dance_sessions
        - test: users_test, challenges_test, dance_sessions_test
        - production: users_prod, challenges_prod, dance_sessions_prod
        """
        if ENVIRONMENT == 'production':
            return f"{base_name}_prod"
        elif ENVIRONMENT == 'test':
            return f"{base_name}_test"
        else:
            return base_name  # development uses base names
    
    @staticmethod
    def get_environment() -> str:
        """Get current environment"""
        return ENVIRONMENT

async def connect_to_mongo():
    Database.client = AsyncIOMotorClient(MONGO_URI)
    print(f"✅ Connected to MongoDB (Environment: {ENVIRONMENT})")

async def close_mongo_connection():
    Database.client.close()
    print("✅ Disconnected from MongoDB") 