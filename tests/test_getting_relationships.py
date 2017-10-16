import os
from unittest import TestCase

from py2neo import Graph

from flask_restful_graph.resource_schema import ResourceDataSchema


class TestSerializingNodes(TestCase):
    def setUp(self):
        self.data_schema = ResourceDataSchema()
        self.graph = Graph(password=os.environ.get('TEST_GRAPH_PASSWORD'))
