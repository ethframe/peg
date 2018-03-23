from .analysis import validate
from .generate import generate_parser
from .peg import *


__all__ = ("META_GRAMMAR", "metagrammar", "parse_grammar")


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
         g('Prefix').app('item').rep()).opt() | Tag('Epsilon'))
    g('Prefix',
        (g('AND') * Tag('And') | g('NOT') * Tag('Not')) *
        g('Suffix').app('expr') | g('Suffix'))
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
        g('IdentStart') * g('IdentCont').rep() *
        Tag('Identifier').rext() * g('Spacing'))
    g('TreeIdent',
        g('IdentStart') * g('IdentCont').rep() *
        Tag('TreeIdent').rext() * g('Spacing'))
    g('Tag',
        Literal('@').ign() * g('IdentStart') * g('IdentCont').rep() *
        Tag('Tag').rext() * g('Spacing'))
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
        Tag('Range').rapp('start') * g('Char').app('end') |
        g('Char') * Tag('Char').rapp('char'))
    g('Char',
        Literal('\\').ign() *
        (Literal('n') | Literal('r') | Literal('t') | Literal("'") |
         Literal('"') | Literal('[') | Literal(']') | Literal('\\')) *
        Tag('escape').rext() |
        Literal('\\').ign() * CharRange('0', '2') *
        CharRange('0', '7') * CharRange('0', '7') * Tag('octal').rext() |
        Literal('\\').ign() * CharRange('0', '7') *
        CharRange('0', '7').opt() * Tag('octal').rext() |
        ~Literal('\\') * Any() * Tag('char').rext())
    g('Any', g('DOT') * Tag('Any'))
    g('LEFTARROW', Literal('<-').ign() * g('Spacing'))
    g('SLASH', Literal('/').ign() * g('Spacing'))
    g('AND', Literal('&').ign() * g('Spacing'))
    g('NOT', Literal('!').ign() * g('Spacing'))
    g('QUESTION', Literal('?').ign() * g('Spacing'))
    g('STAR', Literal('*').ign() * g('Spacing'))
    g('PLUS', Literal('+').ign() * g('Spacing'))
    g('OPEN', Literal('(').ign() * g('Spacing'))
    g('CLOSE', Literal(')').ign() * g('Spacing'))
    g('DOT', Literal('.').ign() * g('Spacing'))
    g('LEXTEND', Literal('>>').ign() * g('Spacing'))
    g('REXTEND', Literal('<<').ign() * g('Spacing'))
    g('LAPPEND', Literal(':').ign() * g('Spacing'))
    g('RAPPEND', Literal('<:').ign() * g('Spacing'))
    g('IGNORE', Literal('~').ign() * g('Spacing'))
    g('Spacing', (g('Space') | g('Comment')).rep())
    g('Comment',
        Literal('#').ign() *
        (~g('EndOfLine') * Any().ign()).rep() * g('EndOfLine'))
    g('Space',
        Literal(' ').ign() | Literal('\t').ign() | g('EndOfLine'))
    g('EndOfLine',
        Literal('\r\n').ign() | Literal('\n').ign() | Literal('\r').ign())
    g('EndOfFile', ~Any())
    return g('Grammar')


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


def _make_metagrammar():
    bootstrap = _make_bootstrap_grammar()
    tree, rest = bootstrap.parse(META_GRAMMAR)
    assert tree and not rest
    validate(tree)
    return generate_parser(tree)


metagrammar = _make_metagrammar()


def parse_grammar(source):
    tree, rest = metagrammar.parse(source)
    if tree is None or rest:
        raise ValueError()
    validate(tree)
    return generate_parser(tree)
