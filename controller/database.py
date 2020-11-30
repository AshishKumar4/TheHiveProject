import pymongo
from bson.objectid import ObjectId
from bson import SON
import hashlib
import json
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import re
import time
import secrets

from pymodm.connection import connect

import mongoDefs
import logger
import pymodm
from functools import wraps
from datetime import date
import os

# Connect to MongoDB and call the connection "my-app".

config = json.loads(open('config.json', 'r').read())
log = logger.Logger('logs/dblogs.json')

UPLOAD_FOLDER = 'uploads'


def classToDict(obj, default=None, resolveRef=False):
    """
    Wraps class into a dict, assigning 'default' value to fields not existing in the obj
    """
    final = {}
    refClass = obj.__class__
    refItems = vars(refClass)
    for key in refItems:
        if key[0] == '_' or key in ['DoesNotExist', 'MultipleObjectsReturned', 'objects']:
            continue
        if key in obj:
            final[key] = getattr(obj, key)
            if resolveRef == False and type(getattr(refClass, key)) == pymodm.fields.ReferenceField:
                # print("REFERENCE FIELD!!!")
                final[key] = final[key].to_son()['_id']#getattr(final[key], key)
                # print("FINAL KEY", final[key])
            if type(type(final[key])) in [pymodm.base.models.MongoModelMetaclass, pymodm.base.models.TopLevelMongoModelMetaclass]:
                final[key] = classToDict(final[key])
        else:
            final[key] = default
    return final


def applyFilter(origObj, filters):
    """
    format of filter :
        [
            key1,
            key2,
            key3,
            {
                key4:
                [
                    key4.1,
                    key4.2,
                    {
                        key4.3:
                        [
                            key4.3.1
                            ...
                        ]
                    }
                ]
            }
        ]
    """
    newObj = {}
    for f in filters:
        if type(f) == dict:
            keys = list(f.keys())
            assert len(keys) == 1, "There can only be one key in a subkey"
            key = keys[0]
            if key in origObj:
                nobj = applyFilter(origObj[key], f[key])
            else:
                nobj = None
            newObj[key] = nobj
        else:
            if f in origObj:
                newObj[f] = origObj[f]
            else:
                newObj[f] = None
    return newObj

def setObjectAttributes(Object, data, exclude=[]):
    status = 'complete'
    for key in data:
        val = data[key]
        keys = key.split('-')
        obj = Object
        for k in range(1, len(keys)):
            obj = getattr(obj, keys[k-1])
        if val != 'None' and val != None and val != '' and keys[-1] not in exclude:
            setattr(obj, keys[-1], val)
        elif keys[-1] in obj.__dict__ and getattr(obj, keys[-1]) in [None, '']:
            print(keys[-1])
            status = 'incomplete'
    return Object, status

def filenameSanitizer(string):
    string = string.replace('-', '_')
    string = secure_filename(string)
    return string

def setObjectFileAttributes(Object, files, filenamePrefix, exclude=[]):
    status = 'complete'
    for key in files:
        val = files[key]
        if val.filename == '':
            continue
        keys = key.split('-')
        obj = Object
        for k in range(1, len(keys)):
            obj = getattr(obj, keys[k-1])
        if val != 'None' and val != None and val != '' and keys[-1] not in exclude:
            dirname = os.path.join(
                UPLOAD_FOLDER, 
                filenamePrefix, 
                filenameSanitizer(key),
            )
            if os.path.exists(dirname) == False:
                os.makedirs(dirname)
            filename = os.path.join(
                dirname,
                filenameSanitizer(val.filename)
            )
            val.save(filename)
            setattr(obj, keys[-1], '/' + filename)
        elif keys[-1] in obj.__dict__ and getattr(obj, keys[-1]) in [None, '']:
            print(keys[-1])
            status = 'incomplete'
    return Object, status

def manage_error(returns=1):
    def wrapper(func):
        @wraps(func)
        def function_wrapper(*args, **kwarg):
            try:
                result = func(*args, **kwarg)
                return result
            except Exception as e:
                log.error(func.__name__, None, None, e)
                if returns == 1:
                    return None
                elif returns == 2:
                    return None, False
        return function_wrapper
    return wrapper

class Database:
    def __init__(self, url="mongodb://localhost:27017/hive"):
        try:
            connect(url, alias="default")

        except Exception as e:
            print("Connection with MongoDB Failed!")
            print(e)
        return
    
    @manage_error()
    def initDefaultObjects(self):
        pass

    @manage_error()
    def initFresh(self):
        print("Initializing Database a fresh")
        connect("mongodb://localhost:27017/hive", alias="hive")
        mongoDefs.User(
            userId=config['superAdminUser'],
            password=generate_password_hash(config['superAdminPass']),
            status='admin',
            apiKey=secrets.token_hex(64),
            otp=secrets.token_hex(10),
            emailId=config['emailId'],
            firstName=config['name'],
        ).save()

        mongoDefs.Admin(
            userId=config['superAdminUser'],
            password=generate_password_hash(config['superAdminPass']),
            status='admin',
            otp=secrets.token_hex(10),
            emailId=config['emailId'],
            firstName=config['name'],
        ).save()
        print("Done!")

    @manage_error(returns=2)
    def validateAdmin(self, username, password):
        user = mongoDefs.Admin.objects.get({'_id': username})
        actPassHash = user.password
        res = check_password_hash(actPassHash, password)
        if res is False:
            return None, False
        status = user.status
        return status, True

    @manage_error()
    def userExists(self, data):
        if mongoDefs.User.objects.raw({'_id': data['username']}).count() != 0:
            return 2
        elif mongoDefs.User.objects.raw({'emailId': data['emailId']}).count() != 0:
            return 3
        return 0

    @manage_error()
    def createUserSimple(self, data):
        mongoDefs.User(
            userId=data['username'],
            password=generate_password_hash(data['password']),
            status='unverified',
            apiKey=secrets.token_hex(64),
            otp=data['otp'],
            emailId=data['emailId'],
        ).save()
        return 1

    @manage_error(returns=2)
    def getUser(self, userId, todict=True, filters=None):
        user = mongoDefs.User.objects.get({'_id': userId})
        if todict:
            user = classToDict(user)
        if filters is not None:
            user = applyFilter(user, filters)
        return user, True

    @manage_error(returns=2)
    def saveUser(self, data, files):
        user = mongoDefs.User.objects.get({'_id': data['userId']})
        if user is None:
            return None, False
        user, status = setObjectAttributes(user, data, ['userId', 'emailId'])
        user.status = status
        user, status = setObjectFileAttributes(user, files, 'user/' + user.userId, ['userId', 'emailId'])
        user.save()
        user = classToDict(user)
        return user, True


    @manage_error(returns=2)
    def validateUser(self, username, password):
        user = mongoDefs.User.objects.get({'_id': username})
        actPassHash = user.password
        res = check_password_hash(actPassHash, password)
        if res is False:
            return None, False
        status = user.status
        return status, True

    @manage_error(returns=2)
    def verifyOtpUser(self, username, otp):
        user = mongoDefs.User.objects.get({'_id': username})
        if user.otp == otp:
            user.status = 'incomplete'
            user.save()
            return user.status, True
        return "nonexistant", False

    @manage_error()
    def getOTPbyEmail(self, email):
        user = mongoDefs.User.objects.get({'emailId': email})
        return user.otp, user.userId

    @manage_error(returns=2)
    def getAllUsers(self, filters):
        users = mongoDefs.User.objects.all()
        users = [applyFilter(classToDict(i), filters) for i in users]
        return users, True

    @manage_error(returns=2)
    def validateApiKey(self, apiKey):
        user = mongoDefs.User.objects.get({'apiKey':apiKey})
        return user, True

    @manage_error(returns=2)
    def getFullRunningQueue(self, userId, todict=True, resolveRef=True):
        # user = mongoDefs.User.objects.get({'_id': userId})
        queue = mongoDefs.RunningQueue.objects.raw({'userId':userId})
        if todict == True:
            queue = [classToDict(i, resolveRef=resolveRef) for i in queue]
        return queue, True

    @manage_error(returns=2)
    def getFullCompletedQueue(self, userId, todict=True, resolveRef=True):
        queue = mongoDefs.CompletedQueue.objects.raw({'userId':userId})
        if todict == True:
            queue = [classToDict(i, resolveRef=resolveRef) for i in queue]
        return queue, True

    @manage_error(returns=2)
    def getPendingExperiments(self, userId, todict=True):
        queue = [i for i in mongoDefs.Experiment.objects.raw({'userId':userId}) if i.pendingCounts > 0]
        if todict == True:
            queue = [classToDict(i) for i in queue]
        return queue, True
    
    @manage_error(returns=2)
    def getClientRunning(self, clientId, todict=True, resolveRef=True):
        queue = mongoDefs.RunningQueue.objects.raw({'clientId':clientId})
        if todict == True:
            queue = [classToDict(i, resolveRef=resolveRef) for i in queue]
        return queue, True

    @manage_error(returns=2)
    def getClientCompleted(self, clientId, todict=True, resolveRef=True):
        queue = mongoDefs.CompletedQueue.objects.raw({'clientId':clientId})
        if todict == True:
            queue = [classToDict(i, resolveRef=resolveRef) for i in queue]
        return queue, True
    
    @manage_error(returns=2)
    def getClientStatus(self, clientId, todict=True, resolveRef=False):
        client = mongoDefs.Client.objects.get({'_id':clientId})
        clientRunning, status = self.getClientRunning(clientId, todict=todict, resolveRef=resolveRef)
        if status == False:
            raise "Error"
        clientDone, status = self.getClientCompleted(clientId, todict=todict, resolveRef=resolveRef)
        if status == False:
            raise "Error"

        if todict == True:
            client = classToDict(client)
        return {
            'client':client, 
            'running':clientRunning,
            'done':clientDone
        }, True

    @manage_error(returns=2)
    def getAllClientStatus(self, userId, todict=True, resolveRef=False):
        clients = mongoDefs.Client.objects.raw({'userId':userId})
        clientStats = []
        for client in clients:
            result, status = self.getClientStatus(client.clientId, todict=todict, resolveRef=resolveRef)
            if status == False:
                raise "Error"
            clientStats.append(result)
        return clientStats, True
