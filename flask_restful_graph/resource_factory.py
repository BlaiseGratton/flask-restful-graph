from flask_restful import Resource
from .models import BaseModel


BaseModel.build_schemas()


def create_resource(name, methods_dict):
    return type(
        name + 'Resource',
        (Resource,),
        methods_dict
    )


def get_individual(cls, graph):
    def get_by_id(self, id):
        return cls.select(graph, id).first()
    return get_by_id


def get_collection(cls, graph):
    def get_by_type(self):
        return cls.select(graph)
    return get_by_type


def make_resource_linkage(type_and_id):
    return {'type': type_and_id[0], 'id': type_and_id[1]}


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def get_individual_and_collection_resources(self, cls):
        get = get_individual(cls, self.graph)

        individual_resource = create_resource(
            cls.__name__, {
                'get': lambda self, id: get(self, id).serialize()
            }
        )

        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        get_all = get_collection(cls, self.graph)

        collection_resource = create_resource(
            collection_name, {
                'get': lambda self: [n.serialize() for n in get_all(self)]
            }
        )

        return individual_resource, collection_resource

    def get_relationship_resources(self, related_models):
        resources = []

        # was having closure issues with `relationship` name in the loop, so
        # captured it in a closure
        def get_relationships(relationship, func):
            def _get(self, id):
                relationships = getattr(func(self, id), relationship)
                data = [make_resource_linkage(x.get_type_and_id())
                        for x in relationships]
                return {'data': data}

            return _get

        for model_name in related_models:
            # obtain reference to class for OGM use
            module = __import__('flask_restful_graph.models',
                                fromlist=[model_name])
            cls = getattr(module, model_name)

            # function for getting individual resource
            get = get_individual(cls, self.graph)

            for relationship, plural in related_models[model_name].iteritems():
                # build urls for resource's relationships and entities
                relationship_url = ('/{}/<int:id>/relationships/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

                related_property_url = ('/{}/<int:id>/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

                # extend Resource for each url
                if plural:
                    relationship_resource = create_resource(
                        model_name + relationship + 'Relationship', {
                            'get': get_relationships(relationship, get)
                        }
                    )

                    related_resource = create_resource(
                        model_name + relationship, {
                            'get': get_relationships(relationship, get)
                        }
                    )
                else:
                    relationship_resource = create_resource(
                        model_name + relationship + 'Relationship', {
                            'get': lambda self, id:
                                getattr(get(self, id), relationship)
                                .serialize()
                        }
                    )

                    related_resource = create_resource(
                        model_name + relationship, {
                            'get': lambda self, id:
                                getattr(get(self, id), relationship)
                                .serialize()
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
