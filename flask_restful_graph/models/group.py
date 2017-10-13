from py2neo.ogm import Property, RelatedFrom

from .base_model import BaseModel


class Group(BaseModel):
    title = Property()

    members = RelatedFrom('flask_restful_graph.models.User', 'MEMBER_OF')

    def __init__(self, title, **kwargs):
        self.title = title

    __pluralname__ = 'Groups'
