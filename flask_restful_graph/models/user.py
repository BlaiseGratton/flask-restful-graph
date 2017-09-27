from flask import request
from flask_restful import Resource
from py2neo.ogm import Property

from .base_model import BaseModel


class User(BaseModel):
    id = Property()
    email = Property()
    first_name = Property()
    last_name = Property()

    def __init__(self, email, **kwargs):
        self.email = email
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)


class UserResource(Resource):
    def get(self, id):
        user = User.select(User.graph, id).first()
        return {id: user.email}


class UsersResource(Resource):
    def get(self):
        users = User.select(User.graph)
        return {user._id: user.email for user in users}

    def post(self):
        json = request.get_json()
        email = json['email']
        first_name = json['first_name']
        user = User(email=email, first_name=first_name)
        user.__class__.graph.push(user)
        return True
