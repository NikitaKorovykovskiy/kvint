from motor.motor_asyncio import AsyncIOMotorClient

class MongoDBService:
    def __init__(self, uri="mongodb://mongodb:27017", db_name="report_db"):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    async def get_data_by_phone(self, phone):
        return await self.db.calls.find({"phone": phone}).to_list(None)

mongo_service = MongoDBService()
