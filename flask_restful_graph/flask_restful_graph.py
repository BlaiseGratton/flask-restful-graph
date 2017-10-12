from flask import Flask
from flask_restful import Api

from models.group import Group, GroupsResource
from models.user import User, UsersResource
from resource_factory import ResourceFactory


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)

resource_factory = ResourceFactory()

api.add_resource(GroupsResource, '/groups/')
api.add_resource(
    resource_factory.get_individual_and_collection_resources(Group),
    '/groups/<int:id>')
api.add_resource(UsersResource, '/users/')
api.add_resource(
    resource_factory.get_individual_and_collection_resources(User),
    '/users/<int:id>')
