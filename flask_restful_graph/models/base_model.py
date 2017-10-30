from flask import url_for
from marshmallow import Schema
from py2neo.ogm import GraphObject, Property
import stringcase


registered_models = {}


class BaseModel(GraphObject):

    schemas = {}

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

    #####################################################################
    #                                                                   #
    #                                                                   #
    #                                                                   #
    #####################################################################

    def serialize(self, next_traversal=False):
        resource = {}

        data = {}
        data['id'] = str(self.__primaryvalue__)
        data['type'] = self.__primarylabel__.lower()
        data['attributes'] = self.get_attributes()
        resource['data'] = data

        return resource

    #####################################################################
    #                                                                   #
    #                                                                   #
    #                                                                   #
    #####################################################################

    def get_attributes(self):
        return BaseModel.schemas[self.__class__.__name__].dump(self).data

    def get_links(self):
        links = {}

        try:
            links['self'] = url_for(
                self.__class__.__name__.lower() + 'resource',
                id=self.__primaryvalue__
            )
        except RuntimeError as e:
            print 'Cannot access "links" property outside application context!'
            print e

        return links

    def get_relationships(self):
        relationships = {}

        # this is a dictionary of groups of relationships
        # e.g. {(-1, 'MEMBER_OF'): <py2neo.ogm.RelatedObjects object>}
        related_groups = self._GraphObject__ogm.related

        for related_set in related_groups:
            direction = 'inbound' if related_set[0] is -1 else 'outbound'
            label = related_set[1]
            related_nodes = []
            # [BaseModel.SCHEMAS.serialize(n, next_traversal=False)
            #  for n in related_groups[related_set]]
            relationships[label] = {
                'direction': direction,
                'data': related_nodes
            }

        return relationships

    def get_meta(self):
        pass
