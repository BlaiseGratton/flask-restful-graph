from flask import Flask
from flask_restful import Api

from models.group import Group
from models.user import User
from resource_factory import ResourceFactory


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)

resource_factory = ResourceFactory()


group_resource, groups_resource = \
    resource_factory.get_individual_and_collection_resources(Group)

user_resource, users_resource = \
    resource_factory.get_individual_and_collection_resources(User)


api.add_resource(groups_resource, '/groups/')
api.add_resource(group_resource, '/groups/<int:id>')
api.add_resource(users_resource, '/users/')
api.add_resource(user_resource, '/users/<int:id>')
