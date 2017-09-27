import os

from py2neo import Graph
from py2neo.ogm import GraphObject


class BaseModel(GraphObject):
    graph = Graph(password=os.environ.get('TEST_GRAPH_PASSWORD'))
