import pymongo
import os

MONGO_URL = os.environ.get('MONGODB_URI')
CLIENT = pymongo.MongoClient(MONGO_URL)

db = CLIENT["honeytoken"]
token_collection =db["tokens"]
alerts_collection =db["alerts"]

def add_token(token,email,redirect):
    new_entry = {'token': token,
                 'email': email,
                 'redirect':redirect}
    token_collection.insert_one(new_entry)

def add_alert(alert):
    alerts_collection.insert_one(alert)

def get_alerts(token):
    alert_list=[]
    cursor = alerts_collection.find({'token': token})
    for document in cursor:
        alert_list.append([document['ip'],document['country'],document['region'],document['city'],document['isp'],document['time']])
    return alert_list

def get_tokens():
    token_list = []
    cursor = token_collection.find({})
    for document in cursor:
          token_list.append(document['token'])
    return token_list

def get_mail_address(token):
     cursor = token_collection.find({'token': token})
     return cursor[0].get('email')

def get_redirect_address(token):
     cursor = token_collection.find({'token': token})
     return cursor[0].get('redirect')
