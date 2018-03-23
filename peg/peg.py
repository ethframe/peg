from .tree import *


__all__ = (
    "Epsilon", "Nothing", "Any", "Literal", "CharRange", "CharSet", "Sequence",
    "Choice", "Repeat", "Repeat1", "Optional", "And", "Not", "Ignore",
    "Append", "Extend", "Rappend", "Rextend", "Tag", "Grammar", "Rule"
)


class Expression:
    def __mul__(self, other):
        return Sequence(self, other)

    def __or__(self, other):
        return Choice(self, other)

    def __invert__(self):
        return Not(self)

    def rep(self):
        return Repeat(self)

    def rep1(self):
        return Repeat1(self)

    def opt(self):
        return Optional(self)

    def app(self, name):
        return Append(self, name)

    def ext(self):
        return Extend(self)

    def rapp(self, name):
        return Rappend(self, name)

    def rext(self):
        return Rextend(self)

    def ign(self):
        return Ignore(self)

    def parse(self, s):
        res, tail = self._parse(s, Empty())
        if res is None:
            return None, s
        return res.finalize(), tail


class Epsilon(Expression):
    __slots__ = ()

    def _parse(self, s, tree):
        return tree, s


class Nothing(Expression):
    __slots__ = ()

    def _parse(self, s, tree):
        return None, s


class Any(Expression):
    __slots__ = ()

    def _parse(self, s, tree):
        if s:
            return tree.extend(String(s[0])), s[1:]
        return None, s


class Literal(Expression):
    __slots__ = ("_lit",)

    def __init__(self, lit):
        self._lit = lit

    def _parse(self, s, tree):
        if s.startswith(self._lit):
            return tree.extend(String(self._lit)), s[len(self._lit):]
        return None, s


class CharRange(Expression):
    __slots__ = ("_start", "_end")

    def __init__(self, start, end):
        self._start = start
        self._end = end

    def _parse(self, s, tree):
        if s and self._start <= s[0] <= self._end:
            return tree.extend(String(s[0])), s[1:]
        return None, s


class CharSet(Expression):
    __slots__ = ("_chars",)

    def __init__(self, chars):
        self._chars = set(chars)

    def _parse(self, s, tree):
        if s and s[0] in self._chars:
            return tree.extend(String(s[0])), s[1:]
        return None, s


class Sequence(Expression):
    __slots__ = ("_first", "_second")

    def __init__(self, first, second):
        self._first = first
        self._second = second

    def _parse(self, s, tree):
        res, tail = self._first._parse(s, tree)
        if res is None:
            return None, s
        res, tail = self._second._parse(tail, res)
        if res is None:
            return None, s
        return res, tail


class Choice(Expression):
    __slots__ = ("_first", "_second")

    def __init__(self, first, second):
        self._first = first
        self._second = second

    def _parse(self, s, tree):
        res, tail = self._first._parse(s, tree)
        if res is not None:
            return res, tail
        return self._second._parse(s, tree)


class Repeat(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        while True:
            res, tail = self._expr._parse(s, tree)
            if res is None:
                return tree, s
            s = tail
            tree = res


class Repeat1(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, tree)
        if res is None:
            return None, s
        s = tail
        tree = res
        while True:
            res, tail = self._expr._parse(s, tree)
            if res is None:
                return tree, s
            s = tail
            tree = res


class Optional(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, tree)
        if res is None:
            return tree, s
        return res, tail


class And(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, _ = self._expr._parse(s, Empty())
        if res is not None:
            return tree, s
        return None, s


class Not(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, _ = self._expr._parse(s, Empty())
        if res is None:
            return tree, s
        return None, s


class Ignore(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return tree, tail


class Append(Expression):
    __slots__ = ("_expr", "_name")

    def __init__(self, expr, name):
        self._expr = expr
        self._name = name

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return tree.append(self._name, res), tail


class Extend(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return tree.extend(res), tail


class Rappend(Expression):
    __slots__ = ("_expr", "_name")

    def __init__(self, expr, name):
        self._expr = expr
        self._name = name

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return res.rappend(self._name, tree), tail


class Rextend(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return res.rextend(tree), tail


class Tag(Expression):
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def _parse(self, s, tree):
        return Named(self._name), s


class Grammar(object):

    def __init__(self):
        self._rules = {}

    def __call__(self, name, body=None):
        if body is not None:
            self._rules[name] = body
        return Rule(name, lambda: self._rules[name])


class Rule(Expression):
    __slots__ = ("_name", "_lazy")

    def __init__(self, name, lazy):
        self._name = name
        self._lazy = lazy

    def _parse(self, s, tree):
        return self._lazy()._parse(s, tree)
