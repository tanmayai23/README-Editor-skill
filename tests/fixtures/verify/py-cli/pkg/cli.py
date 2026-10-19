import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(prog="tool")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--out", default="out.json")
    args = parser.parse_args(argv)
    if args.verbose:
        print("writing", args.out)
    return 0
