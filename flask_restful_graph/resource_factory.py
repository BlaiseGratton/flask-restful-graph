from flask import jsonify, request
from flask_restful import Resource
from py2neo import ConstraintError

from .models import BaseModel


BaseModel.build_schemas()


###############################################################################
#                                                                             #
#                Utility functions                                            #
#                                                                             #
###############################################################################


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


def contains_type_and_id(collection, type_and_id):
    """
    Search collection for combo of type and id identifying a resource
    """
    for item in collection:
        if (item['type'], item['id']) == type_and_id:
            return True


###############################################################################
#                                                                             #
#                 Error object helpers                                        #
#                                                                             #
###############################################################################


def bad_request(*error_messages):
    """
    Return 400 status code with list of error messages
    """
    error_object = {'errors': []}

    for message in error_messages:
        error_object['errors'].append({'detail': message})

    response = jsonify(error_object)
    response.status_code = 400
    return response


###############################################################################
#                                                                             #
#                 GET helpers                                                 #
#                                                                             #
###############################################################################


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
    def get(self, id):
        relationships = getattr(func(self, id), relationship)

        data = [make_resource_linkage(x.get_type_and_id())
                for x in relationships]

        links = get_top_level_links()

        return {
            'links': links,
            'data': data
        }

    return get


def get_related_resources(relationship, func):
    def get(self, id):
        related_nodes = getattr(func(self, id), relationship)

        data = [node.serialize()[0] for node in related_nodes]

        links = get_top_level_links()

        return {
            'links': links,
            'data': data
        }

    return get


###############################################################################
#                                                                             #
#                 POST helpers                                                #
#                                                                             #
###############################################################################


def post_to_resource(cls, graph):
    def post(self):
        body = request.get_json()
        schema = BaseModel.schemas[cls.__name__]

        try:
            if body['data']['type'] != cls.__name__.lower():
                return bad_request('"type" member does not match resource')

            data, errors = schema.load(body['data']['attributes'])

            if not data:
                return bad_request('No matching attributes submitted')

            elif not errors:
                new_node = cls()

                for attribute, value in data.iteritems():
                    setattr(new_node, attribute, value)

                graph.push(new_node)

                response = {}
                response['links'] = 'fix meeeee'
                response['data'], response['included'] = new_node.serialize()

                return response

            else:
                return bad_request(
                    *['{}: {}'.format(attribute, error)
                      for attribute, error_list in errors.iteritems()
                      for error in error_list])

        except (ConstraintError, ValueError) as e:
            return bad_request(e.message)

        except KeyError as e:
            return bad_request('KeyError: missing key "{}"'.format(e.message))

    return post


###############################################################################
#                                                                             #
#                                                                             #
#                                                                             #
###############################################################################


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def make_individual_resource(self, cls):
        get = get_individual_node(cls, self.graph)

        return create_resource_endpoint(
            cls.__name__, {
                'get': get_resource(get)
            }
        )

    def make_resource_collection(self, cls):
        collection_name = cls.__pluralname__ if hasattr(cls, '__pluralname__')\
            else cls.__name__ + 's'

        get_all = get_node_collection(cls, self.graph)

        return create_resource_endpoint(
            collection_name, {
                'get': get_resources(get_all),
                'post': post_to_resource(cls, self.graph)
            }
        )

    def make_individual_and_collection_resources(self, cls):
        return (self.make_individual_resource(cls),
                self.make_resource_collection(cls))

    def make_relationship_resources(self, related_models):
        resources = []

        for model_name in related_models:
            cls = get_class_from_model_name(model_name)
            get_node = get_individual_node(cls, self.graph)

            for relation, is_plural in related_models[model_name].iteritems():

                # build urls for resource's relationships and entities
                relationship_url = '/{}/<int:id>/relationships/{}'.format(
                                    model_name.lower() + 's',
                                    relation)

                related_property_url = '/{}/<int:id>/{}'.format(
                                    model_name.lower() + 's', relation)

                # extend Resource for each url
                if is_plural:
                    relationship_resource = create_resource_endpoint(
                        model_name + relation + 'Relationship', {
                            'get': get_relationships(relation, get_node)
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relation, {
                            'get': get_related_resources(
                                    relation, get_node)
                        }
                    )
                else:
                    relationship_resource = create_resource_endpoint(
                        model_name + relation + 'Relationship', {
                            'get': lambda self, id:
                                getattr(get_node(self, id), relation)
                                .serialize()
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relation, {
                            'get': lambda self, id:
                                getattr(get_node(self, id), relation)
                                .serialize()
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
