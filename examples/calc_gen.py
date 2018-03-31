from peg import metagrammar, infer_types, gen_converter, generate_py_parser


def main():
    grammar = """
        Start  <- _ Expr !.

        Expr   <- Mult ((ADD / SUB)<:left Mult:right)*
        Mult   <- Term ((MUL / DIV)<:left Term:right)*
        Term   <- LP Expr RP / Number / NEG Term:expr

        Number <- ([0] / [1-9] [0-9]*) @Number<< _

        ADD    <- "+"~ _ @Add
        SUB    <- "-"~ _ @Sub
        MUL    <- "*"~ _ @Mul
        DIV    <- "/"~ _ @Div
        NEG    <- "-"~ _ @Neg
        LP     <- "("~ _
        RP     <- ")"~ _
        _      <- ([ \t\r\n]*)~
    """

    tree, _ = metagrammar.parse(grammar)
    types = infer_types(tree)
    with open("calc_generated.py", "w") as fp:
        fp.write("from peg import *\n\n\n")
        fp.write(generate_py_parser(tree))
        fp.write("\n\n\n")
        for t, d in types.items():
            fp.write(d.gen())
            fp.write("\n\n")
        fp.write(gen_converter(types))
        fp.write("\n")
        fp.write("""
class ExpressionVisitor(ClassVisitor):
    __call__ = ClassVisitor.visit
    
    def visit_Add(self, node):
        return self(node.left) + self(node.right)

    def visit_Sub(self, node):
        return self(node.left) - self(node.right)

    def visit_Mul(self, node):
        return self(node.left) * self(node.right)

    def visit_Div(self, node):
        return self(node.left) / self(node.right)

    def visit_Neg(self, node):
        return -self(node.expr)

    def visit_Number(self, node):
        return int(node.value)


def main():
    parser = make_parser()
    tree, rest = parser.parse("2 + 2 * (3 + -1) / 3 * 2")
    assert not rest
    tree = ConverterVisitor().visit(tree)
    print(ExpressionVisitor().visit(tree))


if __name__ == '__main__':
    main()
""")


if __name__ == '__main__':
    main()
