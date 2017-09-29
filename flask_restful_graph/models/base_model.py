import os

from py2neo import Graph
from py2neo.ogm import GraphObject


class BaseModel(GraphObject):
    graph = Graph(password=os.environ.get('TEST_GRAPH_PASSWORD'))

    def to_resource(self, next_traversal):
        self.type = self.__primarylabel__
        self.id = str(self.__primaryvalue__)
        return self

    @property
    def attributes(self):
        pass

    @property
    def links(self):
        pass

    @property
    def relationships(self):
        return self._GraphObject__ogm.related

    @property
    def meta(self):
        pass
