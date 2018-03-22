from .visitor import Visitor, GenericVisitor
from .boolean import *


__all__ = ("bad_references", "well_formed", "validate")


class References(GenericVisitor):
    def __init__(self):
        self.defined = set()
        self.redefined = set()
        self.referenced = set()

    def visit_Grammar(self, node):
        for rule in node.values("rule"):
            self.visit(rule)

    def visit_Rule(self, node):
        name = node["name"].value
        if name in self.defined:
            self.redefined.add(name)
        else:
            self.defined.add(name)
        self.visit(node["body"])

    def visit_Identifier(self, node):
        self.referenced.add(node.value)


def bad_references(grammar):
    ref = References()
    ref.visit(grammar)
    return list(ref.redefined), list(ref.referenced - ref.defined)


class Nullable(Visitor):
    def visit_Grammar(self, node):
        equations = {}
        for rule in node.values("rule"):
            var = Var(rule["name"].value, "nullable")
            equations[var] = self.visit(rule["body"])
        return solve(equations)

    def visit_Rule(self, node):
        raise NotImplementedError("visit_Rule")

    def visit_Choice(self, node):
        return Or([self.visit(i) for i in node.values("alt")])

    def visit_Sequence(self, node):
        return And([self.visit(i) for i in node.values("item")])

    def visit_Epsilon(self, node):
        return true

    def visit_And(self, node):
        return self.visit(node["expr"])

    def visit_Not(self, node):
        return Not(self.visit(node["expr"]))

    def visit_Optional(self, node):
        return true

    def visit_Repeat(self, node):
        return true

    def visit_Repeat1(self, node):
        return self.visit(node["expr"])

    def visit_Append(self, node):
        return self.visit(node["expr"])

    def visit_Rappend(self, node):
        return self.visit(node["expr"])

    def visit_Extend(self, node):
        return self.visit(node["expr"])

    def visit_Rextend(self, node):
        return self.visit(node["expr"])

    def visit_Ignore(self, node):
        return self.visit(node["expr"])

    def visit_Identifier(self, node):
        return Var(node.value, "nullable")

    def visit_Tag(self, node):
        return true

    def visit_Literal(self, node):
        return false

    def visit_Class(self, node):
        return false

    def visit_Nothing(self, node):
        return false

    def visit_Range(self, node):
        return false

    def visit_Char(self, node):
        return false

    def visit_escape(self, node):
        raise NotImplementedError("visit_escape")

    def visit_octal(self, node):
        raise NotImplementedError("visit_octal")

    def visit_char(self, node):
        raise NotImplementedError("visit_char")

    def visit_Any(self, node):
        return false


_nullable = Nullable()


class WellFormed(Visitor):
    def visit_Grammar(self, node):
        equations = _nullable.visit(node)
        for rule in node.values("rule"):
            var = Var(rule["name"].value, "well_formed")
            equations[var] = self.visit(rule["body"])
        return solve(equations)

    def visit_Rule(self, node):
        raise NotImplementedError("visit_Rule")

    def visit_Choice(self, node):
        return And([self.visit(i) for i in node.values("alt")])

    def visit_Sequence(self, node):
        items = node.values("item")
        terms = [self.visit(items[0])]
        null = []
        for t, n in zip(items[1:], items[:-1]):
            null.append(_nullable.visit(n))
            terms.append(Or([Not(And(list(null))), self.visit(t)]))
        return And(terms)

    def visit_Epsilon(self, node):
        return true

    def visit_And(self, node):
        return self.visit(node["expr"])

    def visit_Not(self, node):
        return self.visit(node["expr"])

    def visit_Optional(self, node):
        return self.visit(node["expr"])

    def visit_Repeat(self, node):
        return And([self.visit(node["expr"]),
                    Not(_nullable.visit(node["expr"]))])

    def visit_Repeat1(self, node):
        return self.visit(node["expr"])

    def visit_Append(self, node):
        return self.visit(node["expr"])

    def visit_Rappend(self, node):
        return self.visit(node["expr"])

    def visit_Extend(self, node):
        return self.visit(node["expr"])

    def visit_Rextend(self, node):
        return self.visit(node["expr"])

    def visit_Ignore(self, node):
        return self.visit(node["expr"])

    def visit_Identifier(self, node):
        return Var(node.value, "well_formed")

    def visit_Tag(self, node):
        return true

    def visit_Literal(self, node):
        return true

    def visit_Class(self, node):
        return true

    def visit_Nothing(self, node):
        return true

    def visit_Range(self, node):
        return true

    def visit_Char(self, node):
        return true

    def visit_escape(self, node):
        raise NotImplementedError("visit_escape")

    def visit_octal(self, node):
        raise NotImplementedError("visit_octal")

    def visit_char(self, node):
        raise NotImplementedError("visit_char")

    def visit_Any(self, node):
        return true


_well_formed = WellFormed()


def well_formed(grammar):
    env = _well_formed.visit(grammar)
    bad = []
    for var, expr in env.items():
        if var.ns != "well_formed":
            continue
        if not expr.unwrap():
            bad.append(var.name)
    return bad


def validate(grammar):
    redefined, undefined = bad_references(grammar)
    if redefined:
        raise ValueError(
            "Rules {} redefined".format(", ".join(sorted(redefined))))
    if undefined:
        raise ValueError(
            "Rules {} undefined".format(", ".join(sorted(undefined))))
    bad = well_formed(grammar)
    if bad:
        raise ValueError(
            "Rules {} is not well-formed".format(", ".join(sorted(bad))))
