from collections import deque


__all__ = ("And", "Or", "Not", "Var", "true", "false", "solve")


class Expression:
    pass


class _Term(Expression):
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return repr(self._value)

    def evaluate(self, env):
        return self

    def unwrap(self):
        return self._value


true = _Term(True)
false = _Term(False)


class And(Expression):
    def __init__(self, items):
        self._items = items

    def evaluate(self, env):
        items = []
        for item in self._items:
            item = item.evaluate(env)
            if item is true:
                continue
            if item is false:
                return false
            items.append(item)
        if not items:
            return true
        if len(items) == 1:
            return items[0]
        return And(items)

    def unwrap(self):
        return None

    def ns(self, ns):
        return And([item.ns(ns) for item in self._items])


class Or(Expression):
    def __init__(self, items):
        self._items = items

    def evaluate(self, env):
        items = []
        for item in self._items:
            item = item.evaluate(env)
            if item is true:
                return true
            if item is false:
                continue
            items.append(item)
        if not items:
            return false
        if len(items) == 1:
            return items[0]
        return Or(items)

    def unwrap(self):
        return None

    def ns(self, ns):
        return Or([item.ns(ns) for item in self._items])


class Not(Expression):
    def __init__(self, item):
        self._item = item

    def evaluate(self, env):
        item = self._item.evaluate(env)
        if item is true:
            return false
        if item is false:
            return true
        return Not(item)

    def unwrap(self):
        return None

    def ns(self, ns):
        return Not(self._item.ns(ns))


class Var(Expression):
    def __init__(self, name, ns):
        self.name = name
        self.ns = ns

    def __repr__(self):
        return "Var({!r}, {!r})".format(self.name, self.ns)

    def __hash__(self):
        return hash((self.ns, self.name))

    def __eq__(self, other):
        return type(self) is type(other) and \
            self.name == other.name and self.ns == other.ns

    def evaluate(self, env):
        return env.get(self, self)

    def unwrap(self):
        return None

    def ns(self, ns):
        return Var(self.name, ns)


def solve(equations):
    env = {}
    pending = deque(equations.items())
    loop = True
    while pending and loop:
        loop = False
        unfinished = deque()
        while pending:
            var, expr = pending.popleft()
            expr = expr.evaluate(env)
            if expr in (true, false):
                env[var] = expr
                loop = True
            else:
                unfinished.append((var, expr))
        pending = unfinished
    env.update(pending)
    return env
