from .visitor import Visitor, GenericVisitor
from .peg import *


__all__ = ("generate_visitor", "generate_py_parser", "generate_parser")


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


class PyParserVisitor(Visitor):
    def visit_Grammar(self, node):
        rules = [
            "def make_parser():",
            "    g = Grammar()",
        ]
        for rule in node.values("rule"):
            rules.append("    " + self.visit(rule))
        rules.extend([
            "    return g({!r})".format(node.values("rule")[0]["name"].value)
        ])
        return "\n".join(rules)

    def visit_Rule(self, node):
        return "g({!r}, {})".format(node["name"].value,
                                    self.visit(node["body"]))

    def visit_Sequence(self, node):
        items = []
        for item in node.values("item"):
            if item.name in ("Choice", "Class"):
                items.append("({})".format(self.visit(item)))
            else:
                items.append(self.visit(item))
        return " * ".join(items)

    def visit_Choice(self, node):
        alts = []
        for alt in node.values("alt"):
            alts.append(self.visit(alt))
        return " | ".join(alts)

    def visit_Class(self, node):
        items = []
        for item in node.values("item"):
            items.append(self.visit(item))
        return " | ".join(items)

    def visit_Repeat(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).rep()".format(self.visit(node["expr"]))
        return self.visit(node["expr"]) + ".rep()"

    def visit_Repeat1(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).rep1()".format(self.visit(node["expr"]))
        return self.visit(node["expr"]) + ".rep1()"

    def visit_Optional(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).opt()".format(self.visit(node["expr"]))
        return self.visit(node["expr"]) + ".opt()"

    def visit_Not(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Class"):
            return "~({})".format(self.visit(node["expr"]))
        return "~" + self.visit(node["expr"])

    def visit_Tag(self, node):
        return "Tag({!r})".format(node.value)

    def visit_Identifier(self, node):
        return "g({!r})".format(node.value)

    def visit_Append(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).app({!r})".format(self.visit(node["expr"]),
                                           node["name"].value)
        return "{}.app({!r})".format(self.visit(node["expr"]),
                                     node["name"].value)

    def visit_Rappend(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).rapp({!r})".format(self.visit(node["expr"]),
                                            node["name"].value)
        return "{}.rapp({!r})".format(self.visit(node["expr"]),
                                      node["name"].value)

    def visit_Extend(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).ext()".format(self.visit(node["expr"]))
        return "{}.ext()".format(self.visit(node["expr"]))

    def visit_Rextend(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).rext()".format(self.visit(node["expr"]))
        return "{}.rext()".format(self.visit(node["expr"]))

    def visit_Ignore(self, node):
        if node["expr"].name in ("Sequence", "Choice", "Not", "Class"):
            return "({}).ign()".format(self.visit(node["expr"]))
        return "{}.ign()".format(self.visit(node["expr"]))

    def visit_Range(self, node):
        return "CharRange({!r}, {!r})".format(node["start"].value,
                                              node["end"].value)

    def visit_Char(self, node):
        return "Literal({!r})".format(self.visit(node["char"]))

    def visit_Literal(self, node):
        return "Literal({!r})".format("".join(self.visit(c)
                                              for c in node.values("char")))

    def visit_Any(self, node):
        return "Any()"

    def visit_escape(self, node):
        return {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "'": "'",
            '"': '"',
            "[": "[",
            "]": "]",
            "\\": "\\",
        }[node.value]

    def visit_octal(self, node):
        return chr(int(node.value, 8))

    def visit_char(self, node):
        return node.value


def generate_py_parser(grammar):
    visitor = PyParserVisitor()
    return visitor.visit(grammar)


class ParserVisitor(Visitor):
    def __init__(self):
        self.grammar = Grammar()

    def visit_Grammar(self, node):
        self.grammar = Grammar()
        for rule in node.values("rule"):
            self.visit(rule)
        return self.grammar(node.values("rule")[0]["name"].value)

    def visit_Rule(self, node):
        self.grammar(node["name"].value, self.visit(node["body"]))

    def visit_Choice(self, node):
        items = node.values("alt")
        alt = self.visit(items[-1])
        for item in reversed(items[:-1]):
            alt = Choice(self.visit(item), alt)
        return alt

    def visit_Sequence(self, node):
        items = node.values("item")
        seq = self.visit(items[-1])
        for item in reversed(items[:-1]):
            seq = Sequence(self.visit(item), seq)
        return seq

    def visit_Epsilon(self, node):
        return Epsilon()

    def visit_And(self, node):
        return And(self.visit(node["expr"]))

    def visit_Not(self, node):
        return Not(self.visit(node["expr"]))

    def visit_Optional(self, node):
        return Optional(self.visit(node["expr"]))

    def visit_Repeat(self, node):
        return Repeat(self.visit(node["expr"]))

    def visit_Repeat1(self, node):
        return Repeat1(self.visit(node["expr"]))

    def visit_Append(self, node):
        return Append(self.visit(node["expr"]), node["name"].value)

    def visit_Rappend(self, node):
        return Rappend(self.visit(node["expr"]), node["name"].value)

    def visit_Extend(self, node):
        return Extend(self.visit(node["expr"]))

    def visit_Rextend(self, node):
        return Rextend(self.visit(node["expr"]))

    def visit_Ignore(self, node):
        return Ignore(self.visit(node["expr"]))

    def visit_Identifier(self, node):
        return self.grammar(node.value)

    def visit_Tag(self, node):
        return Tag(node.value)

    def visit_Literal(self, node):
        return Literal("".join(self.visit(n) for n in node.values("char")))

    def visit_Class(self, node):
        items = node.values("item")
        alt = self.visit(items[-1])
        for item in reversed(items[:-1]):
            alt = Choice(self.visit(item), alt)
        return alt

    def visit_Nothing(self, node):
        return Nothing()

    def visit_Range(self, node):
        return CharRange(self.visit(node["start"]), self.visit(node["end"]))

    def visit_Char(self, node):
        return Literal(self.visit(node["char"]))

    def visit_escape(self, node):
        return {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "'": "'",
            '"': '"',
            "[": "[",
            "]": "]",
            "\\": "\\",
        }[node.value]

    def visit_octal(self, node):
        return chr(int(node.value, 8))

    def visit_char(self, node):
        return node.value

    def visit_Any(self, node):
        return Any()


def generate_parser(grammar):
    visitor = ParserVisitor()
    return visitor.visit(grammar)
