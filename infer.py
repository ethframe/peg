from pprint import pprint

from peg import metagrammar, infer_type


def test(grammar):
    tree, rest = metagrammar.parse(grammar)
    assert tree and not rest
    print(infer_type(tree))


def main():
    test("""
        Expr   <- Number (Op<:left Number:right)*
        Number <- [0-9]>>+ @Number<< _
        Op     <- ("+"~ @Add/"-"~ @Sub) _
        _      <- [ \t]~*
    """)
    test("""
        List   <- @List (@Item "a"):item*
    """)
    test("""
        List   <- @List (@Item "a"):fst List:snd / @Empty
    """)


if __name__ == '__main__':
    main()
