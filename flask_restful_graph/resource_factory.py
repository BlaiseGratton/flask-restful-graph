from flask import request
from flask_restful import Resource
from .models import BaseModel


BaseModel.build_schemas()


def get_top_level_links():
    """
    Get dictionary of 'self' link and optional 'related' link
    """
    links = {}
    links['self'] = request.url
    return links


def create_resource_endpoint(name, methods_dict):
    """
    Helper method to inherit from flask_restful.Resource for endpoints
    """
    return type(
        name + 'Resource',
        (Resource,),
        methods_dict
    )


def get_individual(cls, graph):
    """
    Return func for getting a node from graph by type and id
    """
    def get_by_id(self, id):
        return cls.select(graph, id).first()

    return get_by_id


def get_collection(cls, graph):
    """
    Return func for obtaining an iterable of nodes from graph of 1 type
    """
    def get_by_type(self):
        return cls.select(graph)

    return get_by_type


def make_resource_linkage(type_and_id):
    """
    Unpack type_and_id tuple into serializable dictionary
    """
    return {'type': type_and_id[0], 'id': type_and_id[1]}


def get_resource(func):
    """
    Return func for representing a single resource response
    """
    def make_response(self, id):
        response = {}
        response['data'], response['included'] = func(self, id).serialize()
        response['links'] = get_top_level_links()
        return response

    return make_response


def find_type_and_id(collection, node):
    return len(reduce(lambda item:
                      item.get_type_and_id() == node.get_type_and_id(),
               collection)
               ) > 0


def get_resources(func):
    """
    Return func for representing a collection of resource objects
    """
    def make_response(self):
        response = {
            'data': [],
            'included': []
        }

        for node in func(self):
            data, included = node.serialize()
            response['data'].append(data)
            print included
            for included_item in included:
                if not response['included'] or\
                   not find_type_and_id(response['included'], node):
                    response['included'].append(included_item)

        response['links'] = get_top_level_links()
        return response

    return make_response


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def get_individual_resource(self, cls):
        get = get_individual(cls, self.graph)

        return create_resource_endpoint(
            cls.__name__, {
                'get': get_resource(get)
            }
        )

    def get_resource_collection(self, cls):
        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        get_all = get_collection(cls, self.graph)

        return create_resource_endpoint(
            collection_name, {
                'get': get_resources(get_all)
            }
        )

    def get_individual_and_collection_resources(self, cls):
        return (self.get_individual_resource(cls),
                self.get_resource_collection(cls))

    def get_relationship_resources(self, related_models):
        resources = []

        # was having closure issues with `relationship` name in the loop, so
        # captured it in a closure
        def get_relationships(relationship, func):
            def _get(self, id):
                relationships = getattr(func(self, id), relationship)

                data = [make_resource_linkage(x.get_type_and_id())
                        for x in relationships]

                links = get_top_level_links()

                return {
                    'links': links,
                    'data': data
                }

            return _get

        for model_name in related_models:
            # obtain reference to class for OGM use
            module = __import__('flask_restful_graph.models',
                                fromlist=[model_name])
            cls = getattr(module, model_name)

            # returns function for getting individual resource by id
            get = get_individual(cls, self.graph)

            for relationship, is_plural in\
                    related_models[model_name].iteritems():

                # build urls for resource's relationships and entities
                relationship_url = ('/{}/<int:id>/relationships/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

                related_property_url = ('/{}/<int:id>/{}'.format(
                                    model_name.lower() + 's',
                                    relationship))

                # extend Resource for each url
                if is_plural:
                    relationship_resource = create_resource_endpoint(
                        model_name + relationship + 'Relationship', {
                            'get': get_relationships(relationship, get)
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relationship, {
                            'get': get_relationships(relationship, get)
                        }
                    )
                else:
                    relationship_resource = create_resource_endpoint(
                        model_name + relationship + 'Relationship', {
                            'get': lambda self, id:
                                getattr(get(self, id), relationship)
                                .serialize()
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relationship, {
                            'get': lambda self, id:
                                getattr(get(self, id), relationship)
                                .serialize()
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
