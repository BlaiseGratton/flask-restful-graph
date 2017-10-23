from flask import url_for
from py2neo.ogm import GraphObject, RelatedObjects
import stringcase

from flask_restful_graph.schemas import ResourceDataSchema

from .resource_data import ResourceData

data_schema = ResourceDataSchema()


class BaseModel(GraphObject):

    def to_resource(self, next_traversal):
        return ResourceData(self, next_traversal)

    @property
    def attributes(self):
        attributes = {}

        for prop in self.__class__.__dict__:
            if (prop[0] is not '_' and type(self.__getattribute__(prop))
                    is not RelatedObjects):
                attributes[stringcase.camelcase(prop)] = \
                    self.__getattribute__(prop)

        return attributes

    @property
    def links(self):
        links = {}

        links['self'] = url_for(
            self.__class__.__name__.lower() + 'resource',
            id=self.__primaryvalue__
        )
        return links

    def get_relationships(self):
        relationships = {}

        # this is a dictionary of groups of relationships
        # e.g. {(-1, 'MEMBER_OF'): <py2neo.ogm.RelatedObjects object>}
        related_groups = self._GraphObject__ogm.related

        for related_set in related_groups:
            direction = 'inbound' if related_set[0] is -1 else 'outbound'
            label = related_set[1]
            related_nodes = [data_schema.serialize(n, next_traversal=False)
                             for n in related_groups[related_set]]
            relationships[label] = {
                'direction': direction,
                'data': related_nodes
            }

        return relationships

    @property
    def meta(self):
        pass
