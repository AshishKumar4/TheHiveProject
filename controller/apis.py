from flask import *
from flask_restful import *
from collections import defaultdict

class Contests(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['database']
        self.session = kwargs['session']

    def get(self):
        """
        Arguments:

        """
        return {}, 200

    def post(self):
        """
        Request format:
        {
        }
        """
        obj = request.get_json(force=True)
        try:
            return {"status":"done"}, 200
        except Exception as e:
            print("Error occured in Contest post", e)
            return {'status':e}, 500
    
    def delete(self):
        return {'status':'done'}, 200

class Participant(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['database']
        self.session = kwargs['session']

    def get(self):
        """
        Arguments:
        
        """
        return {}, 200

    def post(self):
        """
        Request format:
        {
        }
        """
        obj = request.get_json(force=True)
        try:
            return {"status":"done"}, 200
        except Exception as e:
            print("Error occured in Participant post", e)
            return {'status':e}, 500

    def delete(self):
        return {'status':'done'}, 200

class Submission(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['database']
        self.session = kwargs['session']

    def get(self):
        """
        Arguments:
        
        """
        return {}, 200

    def post(self):
        """
        Request format:
        {
        }
        """
        obj = request.get_json(force=True)
        try:
            return {"status":"done"}, 200
        except Exception as e:
            print("Error occured in Submission post", e)
            return {'status':e}, 500

    def delete(self):
        return {'status':'done'}, 200

class Organizer(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['database']
        self.session = kwargs['session']

    def get(self):
        """
        Arguments:
        
        """
        return {}, 200

    def post(self):
        """
        Request format:
        {
        }
        """
        obj = request.get_json(force=True)
        try:
            return {"status":"done"}, 200
        except Exception as e:
            print("Error occured in Organizer post", e)
            return {'status':e}, 500

    def delete(self):
        return {'status':'done'}, 200

class User(Resource):
    def __init__(self, **kwargs):
        self.db = kwargs['database']
        self.session = kwargs['session']

    def get(self):
        """
        Arguments:
        
        """
        return {}, 200

    def post(self):
        """
        Request format:
        {
        }
        """
        obj = request.get_json(force=True)
        try:
            return {"status":"done"}, 200
        except Exception as e:
            print("Error occured in User post", e)
            return {'status':e}, 500
            
    def delete(self):
        return {'status':'done'}, 200