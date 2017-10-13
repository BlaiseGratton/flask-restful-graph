from py2neo.ogm import Property, RelatedTo

from .base_model import BaseModel


class User(BaseModel):
    email = Property()
    first_name = Property()
    last_name = Property()

    groups = RelatedTo('flask_restful_graph.models.Group', 'MEMBER_OF')

    def __init__(self, email, **kwargs):
        self.email = email
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)
