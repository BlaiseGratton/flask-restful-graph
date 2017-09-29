from flask import request
from flask_restful import Resource
from py2neo.ogm import Property, RelatedFrom

from .base_model import BaseModel
from flask_restful_graph.schemas import ResourceSchema


resource_schema = ResourceSchema()


class Group(BaseModel):
    title = Property()

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title


class GroupResource(Resource):
    def get(self, id):
        group = Group.select(Group.graph, id).first()
        resource = resource_schema.serialize(group)
        print resource
        return {
            'id': group.__primaryvalue__,
            'title': group.title,
            'members': {m.email: m.__primaryvalue__ for m in group.members}
        }


class GroupsResource(Resource):
    def get(self):
        groups = Group.select(Group.graph)
        return {g.title: g.__primaryvalue__ for g in groups}

    def post(self):
        json = request.get_json()
        title = json['title']
        group = Group(title=title)
        group.__class__.graph.push(group)
        return True
