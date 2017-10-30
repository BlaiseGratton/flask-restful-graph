from marshmallow import fields
from py2neo.ogm import RelatedTo

from .base_model import BaseModel
from flask_restful_graph.schemas.schema_factory import \
        register_model_property as register


class User(BaseModel):

    email = register('User', 'email', fields.Email)
    first_name = register('User', 'first_name', fields.Str)
    last_name = register('User', 'first_name', fields.Str)

    groups = RelatedTo('flask_restful_graph.models.Group', 'MEMBER_OF')

    def __init__(self, email, **kwargs):
        self.email = email
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)
