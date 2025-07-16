from motor.motor_asyncio import AsyncIOMotorClient

# Directly declare the working MongoDB URI here
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

class Database:
    client: AsyncIOMotorClient = None

    @staticmethod
    def get_database():
        assert Database.client is not None, "Database client is not connected."
        return Database.client[DB_NAME]

async def connect_to_mongo():
    Database.client = AsyncIOMotorClient(MONGO_URI)
    print("Connected to MongoDB")

async def close_mongo_connection():
    Database.client.close()
    print("Disconnected from MongoDB") 