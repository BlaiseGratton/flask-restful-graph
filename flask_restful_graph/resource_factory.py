from flask import request
from flask_restful import Resource
from .models import BaseModel


BaseModel.build_schemas()


def get_class_from_model_name(model_name):
    """
    Obtain OGM class object from string name
    """
    module = __import__(
        'flask_restful_graph.models',
        fromlist=[model_name]
    )
    return getattr(module, model_name)


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


def get_individual_node(cls, graph):
    """
    Return func for getting a node from graph by type and id
    """
    def get_node_by_id(self, id):
        return cls.select(graph, id).first()

    return get_node_by_id


def get_node_collection(cls, graph):
    """
    Return func for obtaining an iterable of nodes from graph of 1 type
    """
    def get_nodes_by_type(self):
        return cls.select(graph)

    return get_nodes_by_type


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
        response['links'] = get_top_level_links()
        response['data'], response['included'] = func(self, id).serialize()
        return response

    return make_response


def contains_type_and_id(collection, type_and_id):
    """
    Search collection for combo of type and id identifying a resource
    """
    for item in collection:
        if (item['type'], item['id']) == type_and_id:
            return True


def get_resources(func):
    """
    Return func for representing a collection of resource objects
    """
    def make_response(self):
        response = {
            'links': get_top_level_links(),
            'data': [],
            'included': []
        }

        for node in func(self):
            data, included = node.serialize()
            response['data'].append(data)
            for included_item in included:
                type_and_id = included_item['type'], included_item['id']
                if not response['included'] or\
                   not contains_type_and_id(response['included'], type_and_id):
                    response['included'].append(included_item)

        return response

    return make_response


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


def get_related_resources(relationship, func):
    def _get(self, id):
        related_nodes = getattr(func(self, id), relationship)

        data = [node.serialize()[0] for node in related_nodes]

        links = get_top_level_links()

        return {
            'links': links,
            'data': data
        }

    return _get


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def get_individual_resource(self, cls):
        get = get_individual_node(cls, self.graph)

        return create_resource_endpoint(
            cls.__name__, {
                'get': get_resource(get)
            }
        )

    def get_resource_collection(self, cls):
        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        get_all = get_node_collection(cls, self.graph)

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

        for model_name in related_models:
            cls = get_class_from_model_name(model_name)

            get_node = get_individual_node(cls, self.graph)

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
                            'get': get_relationships(relationship, get_node)
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relationship, {
                            'get': get_related_resources(
                                    relationship, get_node)
                        }
                    )
                else:
                    relationship_resource = create_resource_endpoint(
                        model_name + relationship + 'Relationship', {
                            'get': lambda self, id:
                                getattr(get_node(self, id), relationship)
                                .serialize()
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relationship, {
                            'get': lambda self, id:
                                getattr(get_node(self, id), relationship)
                                .serialize()
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
