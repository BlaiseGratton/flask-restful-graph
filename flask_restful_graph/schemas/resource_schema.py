from marshmallow import Schema, fields


class ResourceSchema(Schema):
    type = fields.Str()
    id = fields.Str()
    attributes = fields.Dict()
    relationships = fields.Dict()
    links = fields.Dict()
    included = fields.Dict()
    meta = fields.Dict()

    def serialize(self, node, next_traversal=True):
        resource = node.to_resource(next_traversal)
        data, errors = self.dump(resource)
        if not errors:
            return data
        else:
            raise ValueError(errors)
