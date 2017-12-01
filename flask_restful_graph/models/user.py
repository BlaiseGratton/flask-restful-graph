from marshmallow import fields
from py2neo.ogm import RelatedTo

from .base_model import BaseModel


class User(BaseModel):

    email = BaseModel.add_model_prop('User', 'email', fields.Email)
    first_name = BaseModel.add_model_prop('User', 'first_name', fields.Str)
    last_name = BaseModel.add_model_prop('User', 'last_name', fields.Str)

    groups = BaseModel.add_relationship(
                'User',
                RelatedTo('flask_restful_graph.models.Group', 'MEMBER_OF'),
                related_name='groups',
                plural=True)
