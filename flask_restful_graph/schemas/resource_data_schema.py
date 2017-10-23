from marshmallow import Schema, fields, post_load

from flask_restful_graph.models.resource_data import ResourceData


class ResourceDataSchema(Schema):
    type = fields.Str()
    id = fields.Str()
    attributes = fields.Dict()
    relationships = fields.Dict()
    links = fields.Dict()

    def serialize(self, node, next_traversal=True):
        resource = node.to_resource(next_traversal)
        data, errors = self.dump(resource)
        if not errors:
            return data
        else:
            raise ValueError(errors)

    @post_load
    def make_resource(self, data):
        return ResourceData(data)
