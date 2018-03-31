from peg import metagrammar, infer_types


def main():
    with open("grammar/grammar.txt", "r") as fp:
        text = fp.read()
    tree, rest = metagrammar.parse(text)
    assert tree and not rest
    types = infer_types(tree)
    for t, d in types.items():
        print(d.gen())


if __name__ == '__main__':
    main()
