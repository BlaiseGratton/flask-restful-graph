from flask_restful import Resource
from .schemas import ResourceDataSchema

data_schema = ResourceDataSchema()


def get(cls):
    def get_by_id(self, id):
        node = cls.select(cls.graph, id).first()
        resource_data = data_schema.serialize(node)
        return {'data': resource_data}
    return get_by_id


class ResourceFactory(object):

    def get_individual_and_collection_resources(self, cls):
        return type(cls.__name__ + 'Resource', (Resource,), {'get': get(cls)})


class GroupsResource(Resource):
    def get(self):
        pass
        # groups = Group.select(Group.graph)
        # return {g.title: g.__primaryvalue__ for g in groups}

    def post(self):
        pass
        # json = request.get_json()
        # title = json['title']
        # group = Group(title=title)
        # group.__class__.graph.push(group)
        # return True
