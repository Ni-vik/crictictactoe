from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

MONGO_URI = settings.MONGODB_URL
DATABASE_NAME = settings.DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db['users']
invites_collection = db['games_invite']
games_collection = db['games']