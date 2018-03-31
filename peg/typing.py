from collections import deque

from .visitor import Visitor


__all__ = ("infer_types", "gen_converter")


class Type:
    def __iter__(self):
        yield self

    def force(self):
        return self

    def merge(self, other):
        res = set(self)
        res.update(other)
        return make_or_type(res)

    def common(self):
        current = EmptyType()
        for t in self:
            current = current._common(t)
        return current

    def flat(self):
        raise TypeError()

    def ref(self):
        return None

    def unnamed(self):
        return self

    def resolve(self):
        return self


class EmptyType(Type):
    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self))

    def _common(self, other):
        return other

    def extend(self, other):
        return other.unnamed()


class StringType(Type):
    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self))

    def extend(self, other):
        res = set()
        for t in other:
            res.add(self._extend(t))
        return make_or_type(res)

    def _extend(self, other):
        if isinstance(other, (EmptyType, StringType, TermType)):
            return self
        raise TypeError()


class ContainerType(Type):
    def __init__(self, values, arrays):
        self._values = values
        self._key = tuple(sorted(self._values.items()))
        self._arrays = tuple(sorted(arrays))

    def __eq__(self, other):
        return type(self) is type(other) and self._key == other._key and \
            self._arrays == other._arrays

    def __hash__(self):
        return hash((type(self), self._values))


class NamedType(Type):
    def __init__(self, name):
        self._name = name

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def __repr__(self):
        return self._name

    def gen(self):
        return """class {}:
    @classmethod
    def from_node(cls, node):
        return cls()
""".format(self._name)

    def flat(self):
        return RefType(self._name)

    def unnamed(self):
        return EmptyType()

    def _common(self, other):
        if isinstance(other, NodeType):
            return other._common(self)
        if isinstance(other, NamedType):
            return self
        if isinstance(other, TermType):
            return other
        raise TypeError()

    def append(self, name, other):
        return NodeType(self._name, {name: other}, ())

    def extend(self, other):
        res = set()
        for t in other:
            res.add(self._extend(t.force()))
        return make_or_type(res)

    def _extend(self, other):
        if isinstance(other, (EmptyType, NamedType)):
            return self
        if isinstance(other, (StringType, TermType)):
            return TermType(self._name)
        if isinstance(other, (ContainerType, NodeType)):
            return NodeType(self._name, other._values, other._arrays)


class TermType(Type):
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return "\"{}\"".format(self._name)

    def gen(self):
        return """class {}:
    __slots__ = ("value",)
    
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_node(cls, node):
        return cls(node.value)
""".format(self._name)

    def gen_converter(self):
        return """    def visit_{0}(self, node):
        return {0}(node.value)
""".format(self._name)

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def flat(self):
        return RefType(self._name)

    def unnamed(self):
        return String()


class NodeType(Type):
    def __init__(self, name, values, arrays):
        self._name = name
        self._values = values
        self._key = tuple(sorted(self._values.items()))
        self._arrays = frozenset(arrays)

    def __repr__(self):
        return "{}({})".format(
            self._name,
            ", ".join(
                ("{}=[{}]" if k in self._arrays else "{}={}").format(k, v)
                for k, v in self._key
            )
        )

    def gen(self):
        slots = ", ".join('"{}"'.format(v) for v in self._values.keys())
        if len(self._values) == 1:
            slots = "({},)".format(slots)
        else:
            slots = "({})".format(slots)
        args = ", ".join(self._values.keys())
        fields = "\n        ".join(
            "self.{0} = {0}".format(v) for v in self._values.keys())
        node = ", ".join(
            "node[\"{}\"]".format(n) if n not in self._arrays else
            "node.values(\"{}\")".format(n)
            for n in self._values.keys()
        )
        return """class {}:
    __slots__ = {}

    def __init__(self, {}):
        {}

    @classmethod
    def from_node(cls, node):
        return cls({})
""".format(self._name, slots, args, fields, node)

    def gen_converter(self):
        node = ", ".join(
            "self.visit(node[\"{}\"])".format(n) if n not in self._arrays else
            "[self.visit(v) for n in node.values(\"{}\")]".format(n)
            for n in self._values.keys()
        )
        return """    def visit_{0}(self, node):
        return {0}({1})
""".format(self._name, node)

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name \
            and self._key == other._key and self._arrays == other._arrays

    def __hash__(self):
        return hash((type(self), self._name, self._key, self._arrays))

    def flat(self):
        return RefType(self._name)

    def unnamed(self):
        return ContainerType(self._values, self._arrays)

    def _common(self, other):
        if isinstance(other, NodeType):
            if self._name == other._name:
                values = dict(self._values)
                for k, v in other._values.items():
                    if k in values:
                        values[k] = make_or_type(set(values[k]) | set(v))
                    else:
                        values[k] = v
                return NodeType(
                    self._name, values, self._arrays | other._arrays
                )
        if isinstance(other, NamedType):
            if self._name == other._name:
                return self
        raise TypeError()

    def resolve(self):
        return NodeType(
            self._name, {k: v.resolve() for k, v in self._values.items()},
            self._arrays
        )

    def append(self, name, other):
        values = dict(self._values)
        if name in values:
            values[name] = values[name].merge(other)
            return NodeType(self._name, values, tuple(self._arrays) + (name,))
        else:
            values[name] = other
            return NodeType(self._name, values, self._arrays)


def make_or_type(ts):
    if len(ts) == 0:
        return None
    if len(ts) == 1:
        return ts.pop()
    return OrType(ts)


class OrType(Type):
    def __init__(self, ts):
        self._ts = frozenset(ts)

    def __repr__(self):
        return " | ".join(map(repr, self._ts))

    def __eq__(self, other):
        return type(self) is type(other) and self._ts == other._ts

    def __hash__(self):
        return hash((type(self), self._ts))

    def __iter__(self):
        return iter(self._ts)

    def flat(self):
        return make_or_type(set(t.flat() for t in self._ts))

    def unnamed(self):
        return make_or_type(set(t.unnamed() for t in self._ts))

    def resolve(self):
        res = set()
        for t in self._ts:
            res.update(t.resolve())
        return make_or_type(res) or ()

    def append(self, name, other):
        res = set()
        for t in self._ts:
            res.update(t.append(name, other))
        return make_or_type(res)

    def extend(self, other):
        res = set()
        for t in self._ts:
            res.update(t.extend(other))
        return make_or_type(res)


class RefType(Type):
    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return self._name

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def flat(self):
        return self

    def unnamed(self):
        return EmptyType()

    def name(self):
        return self._name


class RuleRefType(Type):
    def __init__(self, name, registry):
        self._name = name
        self._registry = registry
        self._refs = None

    def __repr__(self):
        return "*{}".format(self._name)

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def force(self):
        return self._registry.get(self._name).process(EmptyType())

    def flat(self):
        return self

    def resolve(self):
        if self._refs is not None:
            return self._refs
        self._refs = self._registry.get_ref(self._name)
        ref = set(self._refs)
        res = set()
        while True:
            for t in ref:
                res.update(t.resolve())
            if ref == res:
                break
            self._refs = make_or_type(
                set(r for r in res if isinstance(r, RefType)))
            ref = res
            res = set()
        return self._refs

    def unnamed(self):
        return self.force().unnamed()

    def ref(self):
        return self._name

    def append(self, name, other):
        return self.force().append(name, other)

    def extend(self, other):
        return self.force().extend(other)


class TypeOp:
    pass


class TagOp(TypeOp):
    def __init__(self, name):
        self._name = name

    def process(self, t):
        return NamedType(self._name)


class AppendOp(TypeOp):
    def __init__(self, op, name, registry):
        self._op = op
        self._name = name
        self._registry = registry

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return t.append(self._name, self._registry.seen_type(r).flat())


class RappendOp(AppendOp):
    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return r.append(self._name, self._registry.seen_type(t).flat())


class ExtendOp(TypeOp):
    def __init__(self, op):
        self._op = op

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return t.extend(r.force())


class RextendOp(ExtendOp):
    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return r.extend(t.force())


class RepeatOp(TypeOp):
    def __init__(self, op):
        self._op = op

    def process(self, t):
        res = set()
        while t is not None and any(i not in res for i in t):
            res.update(t)
            t = self._op.process(t)
        return make_or_type(res)


class SequenceOp(TypeOp):
    def __init__(self, ops):
        self._ops = ops

    def process(self, t):
        for op in self._ops:
            t = op.process(t)
            if t is None:
                return None
        return t


class ChoiceOp(TypeOp):
    def __init__(self, ops):
        self._ops = ops

    def process(self, t):
        res = set()
        for op in self._ops:
            r = op.process(t)
            if r is not None:
                res.update(r)
        return make_or_type(res)


class NoOp(TypeOp):
    def process(self, t):
        return t


class StringOp(TypeOp):
    def process(self, t):
        return t.extend(StringType())


class LazyOp(TypeOp):
    def __init__(self, name, registry):
        self._name = name
        self._registry = registry

    def process(self, t):
        if type(t.force()) is EmptyType:
            return RuleRefType(self._name, self._registry)
        return self._registry.get(self._name).process(t)


class MemoOp(TypeOp):
    def __init__(self, op):
        self._op = op
        self._input = {}

    def process(self, t):
        if t in self._input:
            return self._input[t]
        self._input[t] = None
        r = self._input[t] = self._op.process(t)
        if r is None:
            return None
        n = self._op.process(t)
        while r != n:
            r = self._input[t] = n
            n = self._op.process(t)
        return r


class Registry:
    def __init__(self, start):
        self._start = start
        self._exprs = {}
        self._rets = {}
        self._types = {}
        self._seen_refs = set([self._start])
        self._queue = deque([self._start])

    def infer(self):
        while self._queue:
            name = self._queue.popleft()
            self._rets[name] = self.seen_type(
                self._exprs[name].process(EmptyType())
            ).flat()
        res = {}
        for k, v in list(self._types.items()):
            if isinstance(k, RuleRefType):
                continue
            res[k.name()] = v.resolve().common()
        return res

    def get_ref(self, name):
        return self._rets.get(name, ())

    def set_ref(self, name, value):
        if value is None:
            value = ()
        self._rets[name] = value

    def seen_type(self, t):
        for i in t:
            if i.ref() is not None and i.ref() not in self._seen_refs:
                self._seen_refs.add(i.ref())
                self._queue.append(i.ref())
            self._types[i.flat()] = self._types.get(i.flat(), i).merge(i)
        return t

    def expr(self, name, expr):
        self._exprs[name] = expr

    def lazy(self, name):
        return LazyOp(name, self)

    def get(self, name):
        return self._exprs[name]

    def append(self, name, op):
        return AppendOp(op, name, self)

    def rappend(self, name, op):
        return RappendOp(op, name, self)


class TypingVisitor(Visitor):
    def __init__(self):
        self._registry = None
    
    def visit_Grammar(self, node):
        rules = node.values("rule")
        self._registry = Registry(rules[0]["name"].value)
        for rule in rules:
            expr = self.visit(rule["body"])
            self._registry.expr(rule["name"].value, MemoOp(expr))
        return self._registry

    def visit_Sequence(self, node):
        ops = []
        for item in node.values("item"):
            ops.append(self.visit(item))
        return SequenceOp(ops)

    def visit_Choice(self, node):
        alts = []
        for alt in node.values("alt"):
            alts.append(self.visit(alt))
        return ChoiceOp(alts)

    def visit_Identifier(self, node):
        return self._registry.lazy(node.value)

    def visit_Repeat(self, node):
        return RepeatOp(self.visit(node["expr"]))

    def visit_Repeat1(self, node):
        op = self.visit(node["expr"])
        return SequenceOp([op, RepeatOp(op)])

    def visit_Optional(self, node):
        return ChoiceOp([self.visit(node["expr"]), NoOp()])

    def visit_Append(self, node):
        return self._registry.append(node["name"].value,
                                     self.visit(node["expr"]))

    def visit_Rappend(self, node):
        return self._registry.rappend(node["name"].value,
                                      self.visit(node["expr"]))

    def visit_Extend(self, node):
        return ExtendOp(self.visit(node["expr"]))

    def visit_Rextend(self, node):
        return RextendOp(self.visit(node["expr"]))

    def visit_Tag(self, node):
        return TagOp(node.value)

    def visit_Range(self, node):
        return StringOp()

    def visit_Class(self, node):
        return StringOp()

    def visit_Char(self, node):
        return StringOp()

    def visit_Literal(self, node):
        return StringOp()

    def visit_Any(self, node):
        return StringOp()

    def visit_Ignore(self, node):
        return NoOp()

    def visit_Not(self, node):
        return NoOp()


def infer_types(grammar):
    visitor = TypingVisitor()
    registry = visitor.visit(grammar)
    return registry.infer()


def gen_converter(types):
    visitor = ["class ConverterVisitor(Visitor):"]
    for t, d in types.items():
        visitor.append(d.gen_converter())
    return "\n".join(visitor)
