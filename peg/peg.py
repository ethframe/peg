from .analysis import validate
from .visitor import *
from .tree import *


__all__ = ("parse_grammar", "META_GRAMMAR", "MetaGrammarVisitor",
           "metagrammar")


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

    def __str__(self):
        return "Epsilon()"

    def _parse(self, s, tree):
        return tree, s


class Nothing(Expression):
    __slots__ = ()

    def __str__(self):
        return "Nothing()"

    def _parse(self, s, tree):
        return None, s


class Any(Expression):
    __slots__ = ()

    def __str__(self):
        return "Any()"

    def _parse(self, s, tree):
        if s:
            return tree.extend(String(s[0])), s[1:]
        return None, s


class Literal(Expression):
    __slots__ = ("_lit",)

    def __init__(self, lit):
        self._lit = lit

    def __str__(self):
        return "Literal({!r})".format(self._lit)

    def _parse(self, s, tree):
        if s.startswith(self._lit):
            return tree.extend(String(self._lit)), s[len(self._lit):]
        return None, s


class CharRange(Expression):
    __slots__ = ("_start", "_end")

    def __init__(self, start, end):
        self._start = start
        self._end = end

    def __str__(self):
        return "CharRange({!r}, {!r})".format(self._start, self._end)

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

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice,)):
                return "({})".format(p)
            return str(p)
        return "{} * {}".format(maybe_paren(self._first),
                                maybe_paren(self._second))

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

    def __str__(self):
        return "{} | {}".format(self._first, self._second)

    def _parse(self, s, tree):
        res, tail = self._first._parse(s, tree)
        if res is not None:
            return res, tail
        return self._second._parse(s, tree)


class Repeat(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "{}.rep()".format(maybe_paren(self._expr))

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

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "{}.rep1()".format(maybe_paren(self._expr))

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

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence, And, Not)):
                return "({})".format(p)
            return str(p)
        return "{}.opt()".format(maybe_paren(self._expr))

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, tree)
        if res is None:
            return tree, s
        return res, tail


class And(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "&{}".format(maybe_paren(self._expr))

    def _parse(self, s, tree):
        res, _ = self._expr._parse(s, Empty())
        if res is not None:
            return tree, s
        return None, s


class Not(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "~{}".format(maybe_paren(self._expr))

    def _parse(self, s, tree):
        res, _ = self._expr._parse(s, Empty())
        if res is None:
            return tree, s
        return None, s


class Ignore(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "{}.ign()".format(maybe_paren(self._expr))

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

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "{}.app({!r})".format(maybe_paren(self._expr), self._name)

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

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence)):
                return "({})".format(p)
            return str(p)
        return "{}.rapp({!r})".format(maybe_paren(self._expr), self._name)

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return res.rappend(self._name, tree), tail


class Rextend(Expression):
    __slots__ = ("_expr",)

    def __init__(self, expr):
        self._expr = expr

    def __str__(self):
        def maybe_paren(p):
            if isinstance(p, (Choice, Sequence, And, Not)):
                return "({})".format(p)
            return str(p)
        return "{}.rext()".format(maybe_paren(self._expr))

    def _parse(self, s, tree):
        res, tail = self._expr._parse(s, Empty())
        if res is None:
            return None, s
        return res.rextend(tree), tail


class Tag(Expression):
    __slots__ = ("_name",)

    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "Tag({!r})".format(self._name)

    def _parse(self, s, tree):
        return Named(self._name), s


class Grammar(object):

    def __init__(self):
        self._rules = {}

    def __str__(self):
        rules = ["g = Grammar()"]
        for rule, body in self._rules.items():
            rules.append("g({!r}, {})".format(rule, body))
        return "\n".join(rules)

    def __call__(self, name, body=None):
        if body is not None:
            self._rules[name] = body
        return Rule(name, lambda: self._rules[name])


class Rule(Expression):
    __slots__ = ("_name", "_lazy")

    def __init__(self, name, lazy):
        self._name = name
        self._lazy = lazy

    def __str__(self):
        return "g({!r})".format(self._name)

    def _parse(self, s, tree):
        return self._lazy()._parse(s, tree)


class _BootstrapGrammarVisitor(Visitor):
    def __init__(self):
        self.grammar = None
        self.start = None

    def visit_Grammar(self, node):
        self.grammar = Grammar()
        self.start = None
        rules = node.values("rule")
        for rule in rules:
            self.visit(rule)
        if rules:
            self.start = self.grammar(rules[0]["name"].value)
        return self.start

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


def _make_bootstrap_grammar():
    g = Grammar()
    g('Grammar',
        Tag('Grammar') * g('Spacing') *
        g('Definition').app('rule').rep1() * g('EndOfFile'))
    g('Definition',
        g('Identifier') * g('LEFTARROW') *
        Tag('Rule').rapp('name') * g('Expression').app('body'))
    g('Expression',
        g('Sequence') *
        (g('SLASH') * Tag('Choice').rapp('alt') * g('Sequence').app('alt') *
         (g('SLASH') * g('Sequence').app('alt')).rep()).opt())
    g('Sequence',
        g('Prefix') *
        (Tag('Sequence').rapp('item') * g('Prefix').app('item') *
         g('Prefix').app('item').rep()).opt() |
        Tag('Epsilon'))
    g('Prefix',
        (g('AND') * Tag('And') |
         g('NOT') * Tag('Not')) *
        g('Suffix').app('expr') |
        g('Suffix'))
    g('Suffix',
        g('AstOp') *
        (g('QUESTION') * Tag('Optional') |
         g('STAR') * Tag('Repeat') |
         g('PLUS') * Tag('Repeat1')).rapp('expr').opt())
    g('AstOp',
        g('Primary') *
        ((g('LAPPEND') * Tag('Append') |
          g('RAPPEND') * Tag('Rappend')).rapp('expr') *
         g('TreeIdent').app('name') |
         (g('LEXTEND') * Tag('Extend') |
          g('REXTEND') * Tag('Rextend') |
          g('IGNORE') * Tag('Ignore')).rapp('expr')).opt())
    g('Primary',
        g('Identifier') * ~g('LEFTARROW') |
        g('OPEN') * g('Expression') * g('CLOSE') |
        g('Literal') | g('Class') | g('Any') | g('Tag'))
    g('Identifier',
        g('IdentStart') * Tag('Identifier').rext() *
        g('IdentCont').rep() * g('Spacing'))
    g('TreeIdent',
        g('IdentStart') * Tag('TreeIdent').rext() *
        g('IdentCont').rep() * g('Spacing'))
    g('Tag',
        Literal('@').ign() * g('IdentStart') *
        Tag('Tag').rext() * g('IdentCont').rep() * g('Spacing'))
    g('IdentStart',
        CharRange('a', 'z') | CharRange('A', 'Z') | Literal('_'))
    g('IdentCont',
        g('IdentStart') | CharRange('0', '9'))
    g('Literal',
        Literal("'").ign() * Tag('Literal') *
        (~Literal("'") * g('Char').app('char')).rep() *
        Literal("'").ign() * g('Spacing') |
        Literal('"').ign() * Tag('Literal') *
        (~Literal('"') * g('Char').app('char')).rep() *
        Literal('"').ign() * g('Spacing'))
    g('Class',
        Literal('[').ign() *
        (~Literal(']') * g('Range') *
         (~Literal(']') * Tag('Class').rapp('item') * g('Range').app('item') *
          (~Literal(']') * g('Range').app('item')).rep()).opt() |
         Tag('Nothing')) *
        Literal(']').ign() * g('Spacing'))
    g('Range',
        g('Char') * Literal('-').ign() *
        Tag('Range').rapp('start') *
        g('Char').app('end') |
        g('Char') * Tag('Char').rapp('char'))
    g('Char',
        Literal('\\').ign() *
        (Literal('n') | Literal('r') | Literal('t') |
         Literal("'") | Literal('"') | Literal('[') |
         Literal(']') | Literal('\\')) *
        Tag('escape').rext() |
        Literal('\\').ign() * CharRange('0', '2') *
        CharRange('0', '7') * CharRange('0', '7') *
        Tag('octal').rext() |
        Literal('\\').ign() * CharRange('0', '7') *
        CharRange('0', '7').opt() * Tag('octal').rext() |
        ~Literal('\\') * Any() * Tag('char').rext())
    g('Any',
        g('DOT') * Tag('Any'))
    g('LEFTARROW',
        Literal('<-').ign() * g('Spacing'))
    g('SLASH',
        Literal('/').ign() * g('Spacing'))
    g('AND',
        Literal('&').ign() * g('Spacing'))
    g('NOT',
        Literal('!').ign() * g('Spacing'))
    g('QUESTION',
        Literal('?').ign() * g('Spacing'))
    g('STAR',
        Literal('*').ign() * g('Spacing'))
    g('PLUS',
        Literal('+').ign() * g('Spacing'))
    g('OPEN',
        Literal('(').ign() * g('Spacing'))
    g('CLOSE',
        Literal(')').ign() * g('Spacing'))
    g('DOT',
        Literal('.').ign() * g('Spacing'))
    g('LEXTEND',
        Literal('>>').ign() * g('Spacing'))
    g('REXTEND',
        Literal('<<').ign() * g('Spacing'))
    g('LAPPEND',
        Literal(':').ign() * g('Spacing'))
    g('RAPPEND',
        Literal('<:').ign() * g('Spacing'))
    g('IGNORE',
        Literal('~').ign() * g('Spacing'))
    g('Spacing',
        (g('Space') | g('Comment')).rep())
    g('Comment',
        Literal('#').ign() *
        (~g('EndOfLine') * Any().ign()).rep() * g('EndOfLine'))
    g('Space',
        Literal(' ').ign() | Literal('\t').ign() | g('EndOfLine'))
    g('EndOfLine',
        Literal('\r\n').ign() | Literal('\n').ign() | Literal('\r').ign())
    g('EndOfFile',
        ~Any())
    return g("Grammar")


META_GRAMMAR = r"""
# Based on Ford`s original grammar for PEGs

# Hierarchical syntax
Grammar    <- @Grammar Spacing Definition:rule+ EndOfFile
Definition <- Identifier LEFTARROW @Rule<:name Expression:body

Expression <- Sequence (SLASH @Choice<:alt Sequence:alt (SLASH Sequence:alt)*)?
Sequence   <- Prefix (@Sequence<:item Prefix:item Prefix:item*)? / @Epsilon
Prefix     <- (AND @And / NOT @Not) Suffix:expr / Suffix
Suffix     <- AstOp (QUESTION @Optional /
                     STAR @Repeat /
                     PLUS @Repeat1)<:expr?
AstOp      <- Primary ((LAPPEND @Append /
                        RAPPEND @Rappend)<:expr TreeIdent:name /
                       (LEXTEND @Extend /
                        REXTEND @Rextend /
                        IGNORE @Ignore)<:expr)?
Primary    <- Identifier !LEFTARROW
            / OPEN Expression CLOSE
            / Literal / Class / Any
            / Tag

# Lexical syntax
Identifier  <- IdentStart IdentCont* @Identifier<< Spacing
TreeIdent   <- IdentStart IdentCont* @TreeIdent<< Spacing
Tag         <- "@"~ IdentStart IdentCont* @Tag<< Spacing
IdentStart  <- [a-zA-Z_]
IdentCont   <- IdentStart / [0-9]

Literal     <- [']~ @Literal (!['] Char:char)* [']~ Spacing
             / ["]~ @Literal (!["] Char:char)* ["]~ Spacing
Class       <- '['~ (!']' Range
                     (!']' @Class<:item Range:item (!']' Range:item)*)? /
                     @Nothing) ']'~ Spacing
Range       <- Char '-'~ @Range<:start Char:end / Char @Char<:char
Char        <- '\\'~ [nrt'"\[\]\\] @escape<<
             / '\\'~ [0-2][0-7][0-7] @octal<<
             / '\\'~ [0-7][0-7]? @octal<<
             / !'\\' . @char<<
Any         <- DOT @Any

LEFTARROW   <- '<-'~ Spacing
SLASH       <- '/'~ Spacing
AND         <- '&'~ Spacing
NOT         <- '!'~ Spacing
QUESTION    <- '?'~ Spacing
STAR        <- '*'~ Spacing
PLUS        <- '+'~ Spacing
OPEN        <- '('~ Spacing
CLOSE       <- ')'~ Spacing
DOT         <- '.'~ Spacing
LEXTEND     <- '>>'~ Spacing
REXTEND     <- '<<'~ Spacing
LAPPEND     <- ':'~ Spacing
RAPPEND     <- '<:'~ Spacing
IGNORE      <- '~'~ Spacing

Spacing     <- (Space / Comment)*
Comment     <- '#'~ (!EndOfLine .~)* EndOfLine
Space       <- ' '~ / '\t'~ / EndOfLine
EndOfLine   <- '\r\n'~ / '\n'~ / '\r'~
EndOfFile   <- !.
"""


MetaGrammarVisitor = _BootstrapGrammarVisitor


def _make_metagrammar():
    bootstrap = _make_bootstrap_grammar()
    tree, rest = bootstrap.parse(META_GRAMMAR)
    assert tree and not rest
    validate(tree)
    visitor = MetaGrammarVisitor()
    visitor.visit(tree)
    return visitor.start


metagrammar = _make_metagrammar()


def parse_grammar(source):
    tree, rest = metagrammar.parse(source)
    if tree is None:
        raise ValueError()
    validate(tree)
    visitor = MetaGrammarVisitor()
    visitor.visit(tree)
    return visitor.start


def test():
    g1 = metagrammar
    p1, rest = g1.parse(META_GRAMMAR)
    assert p1 and not rest
    visitor = MetaGrammarVisitor()
    g2 = visitor.visit(p1)
    p2, rest = g2.parse(META_GRAMMAR)
    assert p1 == p2 and not rest


if __name__ == '__main__':
    test()
