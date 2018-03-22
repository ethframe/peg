from .visitor import GenericVisitor


class Tags(GenericVisitor):
    def __init__(self):
        self.tags = []

    def visit_Tag(self, node):
        if node.value not in self.tags:
            self.tags.append(node.value)


def generate_visitor(grammar):
    tags = Tags()
    tags.visit(grammar)
    visitor = ["class TreeVisitor(Visitor):"]
    for tag in tags.tags:
        visitor.extend([
            "    def visit_{}(self, node):".format(tag),
            "        raise NotImplementedError(\"visit_{}\")".format(tag),
            "",
        ])
    return "\n".join(visitor)
