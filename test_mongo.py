import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

async def test_connection():
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        # The following will raise an exception if the connection fails
        server_info = await client.server_info()
        print("✅ Connected to MongoDB Atlas!")
        print("Server info:", server_info)
    except Exception as e:
        print("❌ Connection failed:")
        print(e)

if __name__ == "__main__":
    asyncio.run(test_connection())