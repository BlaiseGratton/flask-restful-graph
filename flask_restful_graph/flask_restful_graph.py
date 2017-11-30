import os

from flask import Flask
from flask_restful import Api
from py2neo import Graph

from models import BaseModel, Group, User
from resource_factory import ResourceFactory


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)


def init_db(password):
    return Graph(password=password)


graph_password = os.environ.get('TEST_GRAPH_PASSWORD')
graph_connection = init_db(graph_password)
resource_factory = ResourceFactory(graph=graph_connection)


group_resource, groups_resource = \
    resource_factory.make_individual_and_collection_resources(Group)
user_resource, users_resource = \
    resource_factory.make_individual_and_collection_resources(User)
relationship_resources = \
    resource_factory.make_relationship_resources(BaseModel.related_models)

api.add_resource(groups_resource, '/groups/')
api.add_resource(group_resource, '/groups/<int:id>')
api.add_resource(users_resource, '/users/')
api.add_resource(user_resource, '/users/<int:id>')

for resource, url in relationship_resources:
    api.add_resource(resource, url)
