from marshmallow import fields
from py2neo.ogm import RelatedFrom

from .base_model import BaseModel
from flask_restful_graph.schemas.schema_factory import \
        register_model_property as register


class Group(BaseModel):
    title = register('Group', 'title', fields.Str)

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title

    __pluralname__ = 'Groups'
