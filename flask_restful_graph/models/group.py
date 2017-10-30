from marshmallow import fields
from py2neo.ogm import RelatedFrom

from .base_model import BaseModel


class Group(BaseModel):
    title = BaseModel.add_model_prop('Group', 'title', fields.Str)

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title

    __pluralname__ = 'Groups'
