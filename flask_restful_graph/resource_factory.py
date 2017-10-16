from flask_restful import Resource

from .schemas import ResourceDataSchema


data_schema = ResourceDataSchema()


def get_individual(cls, graph):

    def get_by_id(self, id):
        node = cls.select(graph, id).first()
        resource_data = data_schema.serialize(node)
        return {'data': resource_data}
    get_by_id.__name__ += '_' + cls.__name__.lower()
    return get_by_id


def get_collection(cls, graph):

    def get_by_type(self):
        nodes = cls.select(graph)
        resource_data = {
            n.__primaryvalue__: data_schema.serialize(n) for n in nodes
        }
        return {'data': resource_data}
    get_by_type.__name__ += '_' + cls.__name__.lower()
    return get_by_type


class ResourceFactory(object):

    def get_individual_and_collection_resources(self, cls, graph):
        individual_resource = type(
            cls.__name__ + 'Resource',
            (Resource,),
            {
                'get': get_individual(cls, graph)
            }
        )

        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        collection_resource = type(
            collection_name + 'Resource',
            (Resource,),
            {
                'get': get_collection(cls, graph)
            }
        )

        return individual_resource, collection_resource
