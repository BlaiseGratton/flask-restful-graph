
class ResourceData(object):

    def __init__(self, node, next_traversal=False):

        try:
            self.type = node.__primarylabel__.lower()
            self.id = str(node.__primaryvalue__)
            self.attributes = node.attributes
            self.links = node.links

            if next_traversal:
                self.relationships = node.get_relationships()

        except AttributeError:
            self.type = node['type']
            self.id = node['id']
            self.attributes = node['attributes']
            self.links = node['links']

    def to_model(self):
        pass
