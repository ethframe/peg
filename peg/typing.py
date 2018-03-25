from .visitor import Visitor


__all__ = ("infer_type",)


class Type:
    def __eq__(self, other):
        raise NotImplementedError()

    def __hash__(self):
        raise NotImplementedError()


class EmptyType(Type):
    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self))

    def top(self):
        return self

    def extend(self, other):
        if isinstance(other, StringType):
            return other
        raise NotImplementedError(other)


class NamedType(Type):
    def __init__(self, name):
        self._name = name

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def __str__(self):
        return "{}".format(self._name)

    def top(self):
        return self

    def _tn(self):
        return self

    def named(self):
        return True

    def append(self, name, other):
        if other.named():
            return NodeType(self._name, [(name, other, False)])
        raise NotImplementedError(other)

    def rappend(self, name, other):
        if other.named():
            return NodeType(self._name, [(name, other, False)])
        raise NotImplementedError(other)

    def extend(self, other):
        if isinstance(other, StringType):
            return TermType(self._name)
        raise NotImplementedError(other)

    def rextend(self, other):
        if isinstance(other, OrType):
            return _mk_or(self.rextend(t) for t in other._ts)
        if isinstance(other, (StringType, TermType)):
            return TermType(self._name)
        raise NotImplementedError(other)


class StringType(Type):
    def __eq__(self, other):
        return type(self) is type(other)

    def __hash__(self):
        return hash(type(self))

    def top(self):
        return self

    def extend(self, other):
        if isinstance(other, StringType):
            return self
        raise NotImplementedType(other)


class ContainerType(Type):
    pass


class TermType(Type):
    def __init__(self, name):
        self._name = name

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash((type(self), self._name))

    def __str__(self):
        return "\"{}\"".format(self._name)

    def top(self):
        return self

    def _tn(self):
        return NamedType(self._name)

    def named(self):
        return True

    def extend(self, other):
        if isinstance(other, StringType):
            return TermType(self._name)
        raise NotImplementedError(other)


class NodeType(Type):
    def __init__(self, name, values):
        self._name = name
        self._values = tuple(values)

    def __eq__(self, other):
        return type(self) is type(other) and self._name == other._name \
            and self._values == other._values

    def __hash__(self):
        return hash((type(self), self._name, self._values))

    def __str__(self):
        if len(self._values) == 0:
            return "{}()".format(self._name)
        return "{}(\n    {}\n)".format(
            self._name,
            ",\n".join("{}=[{}]".format(n, t) if a else "{}={}".format(n, t)
                       for n, t, a in self._values).replace("\n", "\n    "))

    def top(self):
        return NodeType(self._name, ((n, t._tn(), a) for n, t, a in self._values))

    def _tn(self):
        return NamedType(self._name)

    def named(self):
        return True

    def append(self, name, other):
        if other.named():
            nvalues = []
            found = False
            for n, t, a in self._values:
                if name == n:
                    found = True
                    if t.top() == other.top():
                        nvalues.append((n, t, True))
                    else:
                        nvalues.append((n, _mk_or([t, other]), True))
                else:
                    nvalues.append((n, t, a))
            if not found:
                nvalues.append((name, other, False))
            return NodeType(self._name, nvalues)
        raise NotImplementedError(other)


def _flatten(ts):
    f = []
    for t in ts:
        if isinstance(t, OrType):
            for i in _flatten(t._ts):
                if i not in f:
                    f.append(i)
        elif t not in f:
            f.append(t)
    return f


def _mk_or(ts):
    ts = _flatten(ts)
    if len(ts) == 0:
        return None
    if len(ts) == 1:
        return ts[0]
    return OrType(ts)


class OrType(Type):
    def __init__(self, ts):
        self._ts = tuple(ts)

    def __eq__(self, other):
        return type(self) is type(other) and self._ts == other._ts

    def __hash__(self):
        return hash(self._ts)

    def __str__(self):
        return "(\n    {}\n)".format(
            " |\n".join(str(t) for t in self._ts).replace("\n", "\n    "))

    def top(self):
        return _mk_or(t.top() for t in self._ts)

    def _tn(self):
        return _mk_or(t._tn() for t in self._ts)

    def named(self):
        return all(t.named() for t in self._ts)

    def append(self, name, other):
        return _mk_or(t.append(name, other) for t in self._ts)

    def rappend(self, name, other):
        return _mk_or(t.rappend(name, other) for t in self._ts)

    def extend(self, other):
        return _mk_or(t.extend(other) for t in self._ts)


class TypeOp:
    def __init__(self):
        self._input = {}


class TagOp(TypeOp):
    def __init__(self, name):
        super().__init__()
        self._name = name

    def process(self, t):
        return NamedType(self._name)


class AppendOp(TypeOp):
    def __init__(self, op, name):
        super().__init__()
        self._op = op
        self._name = name

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return t.append(self._name, r)


class RappendOp(TypeOp):
    def __init__(self, op, name):
        super().__init__()
        self._op = op
        self._name = name

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return r.rappend(self._name, t)


class ExtendOp(TypeOp):
    def __init__(self, op):
        super().__init__()
        self._op = op

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return t.extend(r)


class RextendOp(TypeOp):
    def __init__(self, op):
        super().__init__()
        self._op = op

    def process(self, t):
        r = self._op.process(EmptyType())
        if r is None:
            return None
        return r.rextend(t)


class RepeatOp(TypeOp):
    def __init__(self, op):
        super().__init__()
        self._op = op

    def process(self, t):
        res = [t]
        tops = set([t.top()])
        t = self._op.process(t)
        while t is not None and t.top() not in tops:
            res.append(t)
            tops.add(t.top())
            t = self._op.process(t)
        return _mk_or(res)


class SequenceOp(TypeOp):
    def __init__(self, ops):
        super().__init__()
        self._ops = ops

    def process(self, t):
        for op in self._ops:
            t = op.process(t)
            if t is None:
                return None
        return t


class ChoiceOp(TypeOp):
    def __init__(self, ops):
        super().__init__()
        self._ops = ops

    def process(self, t):
        res = []
        for op in self._ops:
            r = op.process(t)
            if r is not None:
                res.append(r)
        if res:
            return _mk_or(res)
        return None


class NoOp(TypeOp):
    def process(self, t):
        return t


class StringOp(TypeOp):
    def process(self, t):
        return t.extend(StringType())


class LazyOp(TypeOp):
    def __init__(self, lazy):
        super().__init__()
        self._lazy = lazy

    def process(self, t):
        top = t.top()
        if top in self._input:
            return self._input[top]
        self._input[top] = None
        r = self._input[top] = self._lazy().process(t)
        return r


class TypingVisitor(Visitor):
    def __init__(self):
        self._types = {}
    
    def visit_Grammar(self, node):
        rules = node.values("rule")
        for rule in rules:
            expr = self.visit(rule["body"])
            self._types[rule["name"].value] = expr
        return self._types[rules[0]["name"].value].process(EmptyType())

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
        return LazyOp(lambda: self._types[node.value])

    def visit_Repeat(self, node):
        return RepeatOp(self.visit(node["expr"]))

    def visit_Repeat1(self, node):
        op = self.visit(node["expr"])
        return SequenceOp([op, RepeatOp(op)])

    def visit_Optional(self, node):
        return ChoiceOp([self.visit(node["expr"]), NoOp()])

    def visit_Append(self, node):
        return AppendOp(self.visit(node["expr"]), node["name"].value)

    def visit_Rappend(self, node):
        return RappendOp(self.visit(node["expr"]), node["name"].value)

    def visit_Extend(self, node):
        return ExtendOp(self.visit(node["expr"]))

    def visit_Rextend(self, node):
        return RextendOp(self.visit(node["expr"]))

    def visit_Tag(self, node):
        return TagOp(node.value)

    def visit_Range(self, node):
        return StringOp()

    def visit_Literal(self, node):
        return StringOp()

    def visit_Ignore(self, node):
        return NoOp()


def infer_type(grammar):
    visitor = TypingVisitor()
    return visitor.visit(grammar)
