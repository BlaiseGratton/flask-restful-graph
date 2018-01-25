from marshmallow import fields
from py2neo.ogm import RelatedFrom

from .base_model import BaseModel


class Group(BaseModel):

    title = BaseModel.add_prop('Group', 'title', fields.Str)

    members = BaseModel.add_relationship(
                'Group',
                RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF'),
                related_name='members',
                plural=True)

    admin = BaseModel.add_relationship(
                'Group',
                RelatedFrom('flask_restful_graph.models.User', 'ADMIN_OF'),
                related_name='admin',
                plural=False)

    __pluralname__ = 'Groups'
