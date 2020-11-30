import pymongo
import json
from pymongo.write_concern import WriteConcern
# from pymodm import * #MongoModel, fields
from pymodm import EmbeddedMongoModel, MongoModel, fields, ReferenceField

class Admin(MongoModel):
    userId = fields.CharField(primary_key=True)
    status = fields.CharField()
    password = fields.CharField()
    otp = fields.CharField()
    emailId = fields.EmailField()
    firstName = fields.CharField()
    lastName = fields.CharField()
    
class User(MongoModel):
    userId = fields.CharField(primary_key=True)
    status = fields.CharField()
    password = fields.CharField()

    apiKey = fields.CharField()

    otp = fields.CharField()
    emailId = fields.EmailField()
    firstName = fields.CharField()
    lastName = fields.CharField()

class Run(EmbeddedMongoModel):
    runId = fields.CharField(primary_key=True)
    experimentId = fields.ReferenceField('Experiment')
    config = fields.CharField()
    priorityClient = fields.CharField()
    wandbUrl = fields.CharField()
    results = fields.CharField()
    status = fields.CharField()

class Experiment(MongoModel):
    experimentId = fields.CharField(primary_key=True)
    userId = fields.ReferenceField('User')
    config = fields.CharField()
    totalCounts = fields.IntegerField()
    pendingCounts = fields.IntegerField()
    priorityClient = fields.CharField(default='')
    priority = fields.IntegerField()

class Client(MongoModel):
    clientId = fields.CharField(primary_key=True)
    userId = fields.ReferenceField('User')
    resources = fields.CharField()

class RunningQueue(MongoModel):
    userId = fields.ReferenceField('User')
    clientId = fields.ReferenceField('Client')
    experimentId = fields.ReferenceField('Experiment')
    run = fields.EmbeddedDocumentField(Run, required=True)

class CompletedQueue(MongoModel):
    userId = fields.ReferenceField('User')
    clientId = fields.ReferenceField('Client')
    experimentId = fields.ReferenceField('Experiment')
    run = fields.EmbeddedDocumentField(Run, required=True)

class CentralMind(MongoModel):
    mindId = fields.CharField(primary_key=True)
