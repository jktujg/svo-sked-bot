from pymongo import MongoClient

from ..settings import settings


client = MongoClient(
    settings.DB_HOST,
    settings.DB_PORT,
    tz_aware=True,
    username=settings.DB_USERNAME.get_secret_value(),
    password=settings.DB_PASSWORD.get_secret_value(),
    authSource='admin',
    authMechanism='SCRAM-SHA-1',
)

db = client.svologbot
