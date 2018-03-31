__all__ = ("Visitor", "GenericVisitor", "ClassVisitor")


class Visitor:
    def visit(self, node):
        return getattr(self, "visit_" + node.name)(node)


class GenericVisitor:
    def visit(self, node):
        getattr(self, "visit_" + node.name, self.generic_visit)(node)

    def generic_visit(self, node):
        for _, v in node:
            self.visit(v)


class ClassVisitor:
    def visit(self, node):
        return getattr(self, "visit_" + node.__class__.__name__)(node)
