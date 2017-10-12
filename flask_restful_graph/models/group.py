from flask import request
from flask_restful import Resource
from py2neo.ogm import Property, RelatedFrom

from .base_model import BaseModel
from flask_restful_graph.schemas import ResourceDataSchema


class Group(BaseModel):
    title = Property()

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title


data_schema = ResourceDataSchema()


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
