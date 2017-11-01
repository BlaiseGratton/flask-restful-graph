from flask_restful import Resource
from .models import BaseModel


BaseModel.build_schemas()


def get_individual(cls, graph):

    def get_by_id(self, id):
        node = cls.select(graph, id).first()
        return node.serialize()

    get_by_id.__name__ += '_' + cls.__name__.lower()
    return get_by_id


def get_collection(cls, graph):

    def get_by_type(self):
        nodes = cls.select(graph)
        resource_data = {
            n.__primaryvalue__: n.serialize() for n in nodes
        }
        return resource_data

    get_by_type.__name__ += '_' + cls.__name__.lower()
    return get_by_type


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def get_individual_and_collection_resources(self, cls):
        individual_resource = type(
            cls.__name__ + 'Resource',
            (Resource,),
            {
                'get': get_individual(cls, self.graph)
            }
        )

        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        collection_resource = type(
            collection_name + 'Resource',
            (Resource,),
            {
                'get': get_collection(cls, self.graph)
            }
        )

        return individual_resource, collection_resource

    def get_relationship_resources(self, related_models):
        resources = []

        for model_name in related_models:
            for relationship, plural in related_models[model_name].iteritems():
                resources.append('/{}/<int:id>/relationships/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

                resources.append('/{}/<int:id>/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

        return resources
