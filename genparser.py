from peg import metagrammar, generate_py_parser, generate_visitor


def main():
    with open("grammar/grammar.txt", "r") as fp:
        text = fp.read()
    tree, rest = metagrammar.parse(text)
    print(generate_py_parser(tree))
    print(generate_visitor(tree))


if __name__ == '__main__':
    main()
