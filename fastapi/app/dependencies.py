from motor.motor_asyncio import AsyncIOMotorClient

def get_db_connection():
    client = AsyncIOMotorClient('mongodb://mongo:27017')
    return client.bdProjet

def get_elasticsearch_client():
    # Logic to get an Elasticsearch client
    pass