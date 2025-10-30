import argparse

from .game import playBlossom
from .updater import showStats, searchWords, updateData
from .utils import sevenUniques


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="choice", required=True)

    playParser = subparsers.add_parser(
        "play", help="Play Blossom with optionally specified bank"
    )
    playParser.add_argument("bank", nargs="?", default=None, help="Bank of letters (optional)")
    playParser.add_argument("-f", "--fast", action="store_true", help="Play fast")

    statsParser = subparsers.add_parser("stats", help="Show stats")
    statsParser.add_argument("-f", "--fast", action="store_true", help="Show stats fast")
    searchParser = subparsers.add_parser("search", help="Search for words")
    searchParser.add_argument("queries", nargs="*", help="Words to be searched")
    searchParser.add_argument("-f", "--fast", action="store_true", help="Search fast")

    args = parser.parse_args()
    match args.choice:
        case "play":
            playBlossom(
                bank=args.bank,
                choice=args.choice,
                fast=args.fast if args.fast else False,
                queries=args.queries if args.choice == "search" else None
            )
        case "stats":
            showStats(fast=args.fast if args.fast else False)
        case "search":
            playBlossom(
                choice=args.choice,
                fast=args.fast if args.fast else False,
                queries=args.queries
            )
