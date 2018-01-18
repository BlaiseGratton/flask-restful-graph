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
    try:
        module = __import__(
            'flask_restful_graph.models',
            fromlist=[model_name]
        )
        return getattr(module, model_name)
    except AttributeError:
        raise ValueError(
            'Requested model "{}" not found in module {}'.format(
                model_name, module.__name__)
        )


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


def not_found(error_message):
    """
    Return 404 status code with info about attempted lookup
    """
    response = jsonify({'errors': [{'detail': error_message}]})
    response.status_code = 404
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

                # get any included relationships in the request and
                # check if they exist (else 404)
                if 'relationships' in body['data']:
                    added_relationships = body['data']['relationships']
                    relationships = []

                    # 'entities' is either a single resource linkage object
                    # or a list of resource linkage objects
                    # so we need to check types :(
                    for prop_name, entities in added_relationships.iteritems():
                        related_models = BaseModel.related_models[cls.__name__]

                        if prop_name not in related_models:
                            return bad_request('{} model does not contain \
                                    relationship "{}"'.format(
                                        cls.__name__, prop_name
                                    ))

                        try:
                            if isinstance(entities['data'], dict):
                                # this boolean means it's a to-many collection
                                if related_models[prop_name]:
                                    return bad_request(
                                        'Property "{}" on {} entity is not \
                                         a collection but was submitted as \
                                         one'.format(prop_name, cls.__name__))

                                related_cls = \
                                    get_class_from_model_name(
                                        str(entities['data']['type'].title())
                                    )
                                get_node_by_id = \
                                    get_individual_node(related_cls, graph)

                                node_id = int(entities['data']['id'])
                                node = get_node_by_id(None, node_id)

                                if not node:
                                    return not_found('Requested node of\
                                                    type {} with id {}\
                                                    not found'.format(
                                                        cls.__name__, node_id
                                                    ))
                                else:
                                    relationships.append((prop_name, node))

                            # it is a list of resource linkage objects
                            else:
                                # this boolean means it's a to-many collection
                                if not related_models[prop_name]:
                                    return bad_request(
                                        'Property "{}" on {} entity is a \
                                         collection but was not submitted \
                                         as one'.format(
                                             prop_name, cls.__name__)
                                        )

                                model_name = str(entities['data'][0]['type'])
                                related_cls = get_class_from_model_name(model_name.title())
                                get_node_by_id = \
                                    get_individual_node(related_cls, graph)

                                for related in entities['data']:
                                    node_id = int(related['id'])
                                    node = get_node_by_id(None, node_id)

                                    if not node:
                                        return not_found(
                                            'Requested node of type {} \
                                             with id {} not found'.format(
                                                cls.__name__, node_id
                                            ))
                                    else:
                                        relationships.append((prop_name, node))

                        except ValueError as e:
                            return bad_request('Couldn\'t parse "id"\
                                                property to an int')
                        except KeyError:
                            return bad_request(
                                    'Malformed resource linkage in\
                                     "relationships" member')

                        print prop_name, entities

                new_node = cls()

                for attribute, value in data.iteritems():
                    setattr(new_node, attribute, value)

                try:
                    for prop_name, node in relationships:
                        getattr(new_node, prop_name).add(node)
                    graph.push(new_node)

                except ConstraintError as e:
                    return bad_request(e.message)

                response = {}
                response['links'] = 'fix meeeee'
                response['data'], response['included'] = new_node.serialize()

                return response

            else:
                return bad_request(
                    *['{}: {}'.format(attribute, error)
                      for attribute, error_list in errors.iteritems()
                      for error in error_list])

        except ValueError as e:
            return bad_request(e.message)

        except KeyError as e:
            return bad_request('KeyError: missing key "{}"'.format(e.message))

    return post


###############################################################################
#                                                                             #
#                 PATCH helpers                                               #
#                                                                             #
###############################################################################

def patch_resource(cls, graph):

    def patch(self, id):
        body = request.get_json()
        schema = BaseModel.schemas[cls.__name__]

        if not body:
            return bad_request('No JSON body provided')

        try:
            entity_id = body['data']['id']
            try:
                if int(id) is not int(entity_id):
                    return bad_request('Provided "id" property\
                                        for resource does not match url')
            except (TypeError, ValueError):
                return bad_request('Could not interpret "id" property')

        except KeyError:
            return bad_request('"id" property not provided for resource')

        try:
            if body['data']['type'] != cls.__name__.lower():
                return bad_request('"type" member does not match resource')

            data, errors = schema.load(body['data'].get('attributes', {}))

            relationships = []

            if not errors:
                # get any included relationships in the request and
                # check if they exist (else 404)
                if 'relationships' in body['data']:
                    added_relationships = body['data']['relationships']

                    # 'entities' is either a single resource linkage object
                    # or a list of resource linkage objects
                    # so we need to check types :(
                    for prop_name, entities in added_relationships.iteritems():
                        related_models = BaseModel.related_models[cls.__name__]

                        if prop_name not in related_models:
                            return bad_request('{} model does not contain \
                                    relationship "{}"'.format(
                                        cls.__name__, prop_name
                                    ))

                        try:
                            if isinstance(entities['data'], dict):
                                if related_models[prop_name]['is_plural']:
                                    return bad_request(
                                        'Property "{}" on {} entity is not \
                                         a collection but was submitted as \
                                         one'.format(prop_name, cls.__name__))

                                related_cls = \
                                    get_class_from_model_name(
                                        str(entities['data']['type'].title())
                                    )
                                get_node_by_id = \
                                    get_individual_node(related_cls, graph)

                                node_id = int(entities['data']['id'])
                                node = get_node_by_id(None, node_id)

                                if not node:
                                    return not_found('Requested node of\
                                                    type {} with id {}\
                                                    not found'.format(
                                                        cls.__name__, node_id
                                                    ))
                                else:
                                    relationships.append((prop_name, node))

                            # it is a list of resource linkage objects
                            else:
                                if not related_models[prop_name]['is_plural']:
                                    return bad_request(
                                        'Property "{}" on {} entity is a \
                                         collection but was not submitted \
                                         as one'.format(
                                             prop_name, cls.__name__)
                                        )

                                model_name = str(entities['data'][0]['type'])
                                related_cls = get_class_from_model_name(model_name.title())
                                get_node_by_id = \
                                    get_individual_node(related_cls, graph)

                                for related in entities['data']:
                                    node_id = int(related['id'])
                                    node = get_node_by_id(None, node_id)

                                    if not node:
                                        return not_found(
                                            'Requested node of type {} \
                                             with id {} not found'.format(
                                                cls.__name__, node_id
                                            ))
                                    else:
                                        relationships.append((prop_name, node))

                        except ValueError as e:
                            return bad_request(
                                'Couldn\'t parse "id" property to an int')

                        except KeyError:
                            return bad_request(
                                'Malformed resource linkage in \
                                "relationships" member')

                        print prop_name, entities

                entity = cls.select(graph, id).first()

                for attribute, value in data.iteritems():
                    setattr(entity, attribute, value)

                if relationships:
                    # including relationships in PATCH request entirely
                    # replaces any existing relationships
                    for prop_name, _ in relationships:
                        getattr(entity, prop_name).clear()

                    try:

                        for prop_name, node in relationships:
                            getattr(entity, prop_name).add(node)
                        graph.push(entity)

                    except ConstraintError as e:
                        return bad_request(e.message)

                response = {}
                response['links'] = 'fix meeeee'
                response['data'], response['included'] = entity.serialize()

                return response

            else:
                return bad_request(
                    *['{}: {}'.format(attribute, error)
                      for attribute, error_list in errors.iteritems()
                      for error in error_list])

        except ValueError as e:
            return bad_request(e.message)

        except KeyError as e:
            return bad_request('KeyError: missing key "{}"'.format(e.message))

    return patch


def patch_relationship(relation, cls, graph, is_plural):

    def patch(self, id):
        body = request.get_json()

        if not body or 'data' not in body:
            return bad_request('No JSON data body provided')

        entity = cls.select(graph, id).first()

        if not entity:
            return not_found(
                'Did not find resource of type "{}" with id "{}"'
                .format(cls.__name__, id)
            )

        if is_plural:
            relationships = []

            # get any included relationships in the request and
            # check if they exist (else 404)
            related_cls = get_class_from_model_name(
                BaseModel.related_models[cls.__name__][relation]['class_name']
                .split('.')[-1]
            )

            try:
                for type_and_id in body['data']:
                    node_id = int(type_and_id.get('id'))
                    node = related_cls.select(graph, node_id).first()

                    if not node:
                        return not_found(
                            'Requested node of type {} with id {}\
                            not found'.format(cls.__name__, node_id))
                    else:
                        relationships.append(node)

                # clear existing related nodes regardless if request has any
                getattr(entity, relation).clear()

                if relationships:
                    try:
                        for node in relationships:
                            getattr(entity, relation).add(node)
                        graph.push(entity)

                    except ConstraintError as e:
                        return bad_request(e.message)

            except TypeError:
                return bad_request('"data" member was not iterable')

        else:
            pass

        response = {}
        response['links'] = 'fix meeeee'
        response['data'], response['included'] = entity.serialize()

        return response

    return patch


###############################################################################
#                                                                             #
#                                                                             #
#                                                                             #
###############################################################################


class ResourceFactory(object):

    def __init__(self, graph):
        self.graph = graph

    def make_individual_resource(self, cls):
        get_node = get_individual_node(cls, self.graph)

        return create_resource_endpoint(
            cls.__name__, {
                'get': get_resource(get_node),
                'patch': patch_resource(cls, self.graph)
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

            for relation, rel_def in related_models[model_name].iteritems():
                # build urls for resource's relationships and entities
                relationship_url = '/{}/<int:id>/relationships/{}'.format(
                                    model_name.lower() + 's',
                                    relation)

                related_property_url = '/{}/<int:id>/{}'.format(
                                    model_name.lower() + 's', relation)

                # extend Resource for each url
                if rel_def['is_plural']:
                    relationship_resource = create_resource_endpoint(
                        model_name + relation + 'Relationship', {
                            'get': get_relationships(relation, get_node),
                            'patch': patch_relationship(
                                relation,
                                cls,
                                self.graph,
                                rel_def['is_plural'])
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
                            'get': get_resource(get_node)
                        }
                    )

                    related_resource = create_resource_endpoint(
                        model_name + relation, {
                            'get': get_resource(get_node)
                        }
                    )

                resources.append((relationship_resource, relationship_url))
                resources.append((related_resource, related_property_url))

        return resources
