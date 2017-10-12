from flask import request
from flask_restful import Resource
from py2neo.ogm import Property, RelatedFrom

from marshmallow_jsonapi import validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema


class Group(object):
    title = Property()

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title


class GroupSchema(Schema):
    title = fields.Str()


class GroupResource(Resource):
    def get(self, id):
        group = Group.select(Group.graph, id).first()
        resource = resource_schema.serialize(group)
        return resource


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
