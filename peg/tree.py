__all__ = ("Empty", "Named", "FinalizedNamed", "String", "Term",
           "FinalizedTerm", "Container", "Node", "FinalizedNode")


class Empty:
    __slots__ = ()

    def append(self, name, other):
        return Container([(name, other.finalize())])

    def extend(self, other):
        if isinstance(other, (String, Term)):
            return String(other._value)
        if isinstance(other, (Container, Node)):
            return Container(other._values)
        return self

    def rappend(self, name, other):
        return Container([(name, other.finalize())])

    def rextend(self, other):
        if isinstance(other, (String, Term)):
            return String(other._value)
        if isinstance(other, (Container, Node)):
            return Container(other._values)
        return self


class Named:
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def finalize(self):
        return FinalizedNamed(self._name)

    def append(self, name, other):
        return Node(self._name, [(name, other.finalize())])

    def extend(self, other):
        if isinstance(other, (String, Term)):
            return Term(self._name, other._value)
        if isinstance(other, (Container, Node)):
            return Node(self._name, other._values)
        return self

    def rappend(self, name, other):
        return Node(self._name, [(name, other.finalize())])

    def rextend(self, other):
        if isinstance(other, (String, Term)):
            return Term(self._name, other._value)
        if isinstance(other, (Container, Node)):
            return Node(self._name, other._values)
        return self


class FinalizedNamed:
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return type(self) == type(other) and self._name == other._name

    def __iter__(self):
        return iter(())

    @property
    def name(self):
        return self._name


class String:
    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def append(self, name, other):
        raise TypeError()

    def extend(self, other):
        return String(self._value + other._value)

    def rappend(self, name, other):
        raise TypeError()

    def rextend(self, other):
        return String(other._value + self._value)


class Term:
    __slots__ = ("_name", "_value")

    def __init__(self, name, value):
        self._name = name
        self._value = value

    def finalize(self):
        return FinalizedTerm(self._name, self._value)

    def append(self, name, other):
        raise TypeError()

    def extend(self, other):
        return Term(self._name, self._value + other._value)

    def rappend(self, name, other):
        raise TypeError()

    def rextend(self, other):
        return Term(self._name, other._value + self._value)


class FinalizedTerm:
    __slots__ = ("_name", "_value")

    def __init__(self, name, value):
        self._name = name
        self._value = value

    def __str__(self):
        return "{}({!r})".format(self._name, self._value)

    def __eq__(self, other):
        return type(self) == type(other) and self._name == other._name and \
            self._value == other._value

    def __iter__(self):
        return iter(())

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._value


class Container:
    __slots__ = ("_values",)

    def __init__(self, values):
        self._values = values

    def append(self, name, other):
        return Container(self._values + [(name, other.finalize())])

    def extend(self, other):
        return Container(self._values + other._values)

    def rappend(self, name, other):
        return Container([(name, other.finalize())] + self._values)

    def rextend(self, other):
        return Container(other._values + self._values)


class Node:
    __slots__ = ("_name", "_values")

    def __init__(self, name, values):
        self._name = name
        self._values = values

    def finalize(self):
        return FinalizedNode(self._name, self._values)

    def append(self, name, other):
        return Node(self._name, self._values + [(name, other.finalize())])

    def extend(self, other):
        return Node(self._name, self._values + other._values)

    def rappend(self, name, other):
        return Node(self._name, [(name, other.finalize())] + self._values)

    def rextend(self, other):
        return Node(self._name, other._values + self._values)


class FinalizedNode:
    __slots__ = ("_name", "_values", "_values_dict", "_single_values")

    def __init__(self, name, values):
        self._name = name
        self._values = values
        self._values_dict = {}
        for n, v in values:
            self._values_dict.setdefault(n, []).append(v)
        self._single_values = {
            n: vs[0] for n, vs in self._values_dict.items() if len(vs) == 1
        }

    def __str__(self):
        if len(self._values) == 0:
            return "{}()".format(self._name)
        return "{}(\n    {})".format(
            self._name,
            ",\n".join("{}={}".format(*v)
                       for v in self._values).replace("\n", "\n    "))

    def __eq__(self, other):
        return type(self) == type(other) and self._name == other._name and \
            self._values == other._values

    def __iter__(self):
        return iter(self._values)

    @property
    def name(self):
        return self._name

    def values(self, item):
        return self._values_dict[item]

    def __getitem__(self, item):
        return self._single_values[item]
