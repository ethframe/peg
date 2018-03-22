__all__ = ("Visitor", "GenericVisitor")


class Visitor:
    def visit(self, node):
        return getattr(self, "visit_" + node.name)(node)


class GenericVisitor:
    def visit(self, node):
        getattr(self, "visit_" + node.name, self.generic_visit)(node)

    def generic_visit(self, node):
        for _, v in node:
            self.visit(v)
