from flask import Flask
from flask_restful import Api

from models.group import GroupResource, GroupsResource
from models.user import UserResource, UsersResource


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)

api.add_resource(GroupsResource, '/groups/')
api.add_resource(GroupResource, '/groups/<int:id>')
api.add_resource(UsersResource, '/users/')
api.add_resource(UserResource, '/users/<int:id>')
