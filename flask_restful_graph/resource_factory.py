from flask_restful import Resource
from .models import BaseModel


BaseModel.build_schemas()


def get_individual(cls, graph):

    def get_by_id(self, id):
        return cls.select(graph, id).first()

    return get_by_id


def get_collection(cls, graph):

    def get_by_type(self):
        return cls.select(graph)

    return get_by_type


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def get_individual_and_collection_resources(self, cls):
        get = get_individual(cls, self.graph)

        individual_resource = type(
            cls.__name__ + 'Resource',
            (Resource,),
            {
                'get': lambda self, id: get(self, id).serialize()
            }
        )

        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        get_all = get_collection(cls, self.graph)

        collection_resource = type(
            collection_name + 'Resource',
            (Resource,),
            {
                'get': lambda self: [n.serialize() for n in get_all(self)]
            }
        )

        return individual_resource, collection_resource

    def get_relationship_resources(self, related_models):
        resources = []

        # was having closure issues with `relationship` name in the loop, so
        # captured it in a closure
        def set_relationship(relationship, func):
            def _get(self, id):
                return [n.serialize() for n in
                        getattr(func(self, id), relationship)]
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
                    relationship_resource = type(
                        model_name + relationship.title() +
                        'RelationshipResource',
                        (Resource,),
                        {
                            'get': set_relationship(relationship, get)
                        }
                    )

                    related_resource = type(
                        model_name + relationship.title() + 'Resource',
                        (Resource,),
                        {
                            'get': set_relationship(relationship, get)
                        }
                    )
                else:
                    relationship_resource = type(
                        model_name + relationship + 'RelationshipResource',
                        (Resource,),
                        {
                            'get': lambda self, id:
                                getattr(
                                    get(self, id),
                                    relationship
                                ).serialize()
                        }
                    )

                    related_resource = type(
                        model_name + relationship.title() + 'Resource',
                        (Resource,),
                        {
                            'get': lambda self, id:
                                getattr(
                                    get(self, id),
                                    relationship
                                ).serialize()
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
