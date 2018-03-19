from peg import parse_grammar, Visitor


def main():
    grammar = parse_grammar("""
        Start  <- _ Expr !.

        Expr   <- Mult ((ADD @Add<:left / SUB @Sub<:left) Mult:right)*
        Mult   <- Term ((MUL @Mul<:left / DIV @Div<:left) Term:right)*
        Term   <- LP Expr RP / Number

        Number <- @Number "-"? [0-9]* _

        ADD    <- "+"~ _
        SUB    <- "-"~ _
        MUL    <- "*"~ _
        DIV    <- "/"~ _
        LP     <- "("~ _
        RP     <- ")"~ _
        _      <- ([ \t\r\n]*)~
    """)

    class ExprVisitor(Visitor):
        def visit_Add(self, node):
            return self.visit(node["left"]) + self.visit(node["right"])

        def visit_Sub(self, node):
            return self.visit(node["left"]) - self.visit(node["right"])

        def visit_Mul(self, node):
            return self.visit(node["left"]) * self.visit(node["right"])

        def visit_Div(self, node):
            return self.visit(node["left"]) / self.visit(node["right"])

        def visit_Number(self, node):
            return int(node.value)

    visitor = ExprVisitor()

    tree, _ = grammar.parse("2 + 2 * 2")
    print(tree)
    print(visitor.visit(tree))

    tree, _ = grammar.parse("(2 + 2) * 2")
    print(tree)
    print(visitor.visit(tree))


if __name__ == '__main__':
    main()
