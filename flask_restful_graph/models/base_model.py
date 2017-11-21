from flask import url_for
from marshmallow import Schema
from py2neo.ogm import GraphObject, Property, RelatedObjects
import stringcase


registered_models = {}


class BaseModel(GraphObject):

    #####################################################################
    #                                                                   #
    #           Registering marshalled properties and related models    #

    schemas = {}
    related_models = {}

    @classmethod
    def add_model_prop(cls, model_name, prop_name,
                       marshal_property, **kwargs):
        try:
            model = registered_models[model_name]
        except KeyError:
            model = {}
            registered_models[model_name] = model

        # by default, (un)marshal every property to/from camelcased form
        if 'load_from' not in kwargs and 'dump_to' not in kwargs:
            camelcased = stringcase.camelcase(prop_name)
            model[prop_name] = marshal_property(
                    load_from=camelcased, dump_to=camelcased, **kwargs)
        else:
            model[prop_name] = marshal_property(**kwargs)

        return Property()

    @classmethod
    def build_schemas(cls):
        for model_name in registered_models:
            cls.schemas[model_name] = type(
                model_name + 'Schema',
                (Schema,),
                registered_models[model_name])()

    @classmethod
    def add_relationship(cls, model_name, relationship_definition,
                         related_name, plural):
        try:
            cls.related_models[model_name][related_name] = plural
        except KeyError:
            cls.related_models[model_name] = {related_name: plural}
        return relationship_definition

    #####################################################################
    #                                                                   #
    #           Serializing                                             #

    def serialize(self, next_traversal=False):
        data = {}
        included, relationships = self.get_relationships()
        self_links = self.get_self_links()

        data['type'], data['id'] = self.get_type_and_id()
        data['attributes'] = self.get_attributes()
        data['relationships'] = relationships
        data['links'] = self_links

        return data, included

    #####################################################################
    #                                                                   #
    #           Helper methods for serializing                          #

    def get_attributes(self):
        return BaseModel.schemas[self.__class__.__name__].dump(self).data

    def get_type_and_id(self):
        return self.__primarylabel__.lower(), str(self.__primaryvalue__)

    def get_self_links(self, collection=False):
        links = {}

        try:
            links['self'] = url_for(
                self.__class__.__name__.lower() + 'resource',
                id=self.__primaryvalue__)
        except RuntimeError as e:
            print 'Cannot access "links" property outside application context!'
            print e

        return links

    def get_related_links(self):
        pass

    def get_relationships(self):
        relationships = {}
        included = []

        related = [p for p in self.__class__.__dict__
                   if type(getattr(self, p)) is RelatedObjects]

        for related_set in related:

            try:
                relationships[related_set] = {
                    'links': {
                        'self': url_for(
                            self.__class__.__name__.lower() + related_set +
                            'relationshipresource',
                            id=self.__primaryvalue__),
                        'related': url_for(
                            self.__class__.__name__.lower() + related_set +
                            'resource',
                            id=self.__primaryvalue__)
                    },
                    'data': []
                }
            except RuntimeError as e:
                print 'Cannot access "links" property outside application context!'
                print e

                relationships[related_set] = {
                    'links': {},
                    'data': []
                }

            for node in getattr(self, related_set):
                serialized_node = {}
                serialized_node['type'], \
                    serialized_node['id'] = node.get_type_and_id()

                relationships[related_set]['data']\
                    .append(serialized_node.copy())

                serialized_node['attributes'] = node.get_attributes()
                included.append(serialized_node)

        return included, relationships

    def get_meta(self):
        pass
