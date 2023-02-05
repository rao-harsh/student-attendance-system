from pymongo import MongoClient
from django.conf import settings
import urllib.parse

MONGO_JWT_SETTINGS = settings.MONGO_JWT_SETTINGS

password = urllib.parse.quote(MONGO_JWT_SETTINGS['db_pass'])
username = urllib.parse.quote(MONGO_JWT_SETTINGS['db_user'])
db_name = MONGO_JWT_SETTINGS['db_name']
db_host_mongo = MONGO_JWT_SETTINGS['db_host']

if 'db_port' in MONGO_JWT_SETTINGS:
    db_port_mongo = MONGO_JWT_SETTINGS['db_port']

    mongo_uri = "mongodb://{username}:{password}@{db_host}:{db_port_mongo}/{db_name}".format(
        username=username, password=password, db_host=db_host_mongo,
        db_port_mongo=db_port_mongo, db_name=db_name)
else:
    mongo_uri = "mongodb+srv://{username}:{password}@{host}/{db_name}".format(
        username=username, password=password, host=db_host_mongo, db_name=db_name)

client = MongoClient("mongodb://localhost:27017")
database = client[db_name]

auth_collection = MONGO_JWT_SETTINGS['auth_collection'] if 'auth_collection' in MONGO_JWT_SETTINGS else "user_profile"

fields = MONGO_JWT_SETTINGS['fields'] if 'fields' in MONGO_JWT_SETTINGS else ()

jwt_secret = MONGO_JWT_SETTINGS['jwt_secret'] if 'jwt_secret' in MONGO_JWT_SETTINGS else 'secret'

jwt_life = MONGO_JWT_SETTINGS['jwt_life'] if 'jwt_life' in MONGO_JWT_SETTINGS else 7

# secondary_username_field = MONGO_JWT_SETTINGS['secondary_username_field'] if 'secondary_username_field' in MONGO_JWT_SETTINGS and MONGO_JWT_SETTINGS['secondary_username_field'] != 'email' else None

