from unittest import TestCase
import json

from flask_restful_graph.flask_restful_graph import app, graph_connection
from flask_restful_graph.models import Group, User


HOST = 'http://localhost'

def get_by_id(cls, id):
    return cls.select(graph_connection, id).first()


class TestSerializingNodes(TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_requesting_relationships_1(self):
        rv = self.app.get('/users/8/relationships/groups')
        data = json.loads(rv.data)

        self.assertEqual(len(data), 2)
        self.assertEqual(data['data'][0]['type'], 'group')
        self.assertEqual(data['data'][0]['id'], '11')
        self.assertEqual(
            data['links']['self'],
            HOST + '/users/8/relationships/groups'
        )

    def test_getting_models_relationships_1(self):
        user = get_by_id(User, 8)

        included, relationships = user.get_relationships()

        self.assertEqual(included, [{
            'attributes': {
                'title': 'This is a group',
            },
            'type': 'group',
            'id': '11'
        }])

        self.assertEqual(relationships, {
            'groups': {
                'data': [
                    {
                        'type': 'group',
                        'id': '11'
                    }
                ],
                'links': {}
            }
        })

    def test_getting_models_relationships_2(self):
        group = get_by_id(Group, 11)

        included, relationships = group.get_relationships()

        self.assertEqual(included, [{
            'attributes': {
                'email': 'guy@place.com',
                'firstName': 'Guy'
            },
            'type': 'user',
            'id': '9'
        }, {
            'attributes': {
                'email': 'new4@place.com',
                'firstName': 'Guy'
            },
            'type': 'user',
            'id': '8'
            }])

        self.assertEqual(relationships, {
            'members': {
                'data': [
                    {
                        'type': 'user',
                        'id': '9'
                    }, {
                        'type': 'user',
                        'id': '8'
                    }
                ],
                'links': {}
            }
        })
