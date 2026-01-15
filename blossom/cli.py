import argparse

from .blossom import Blossom
from .session import Session



def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="choice", required=False)

    playParser = subparsers.add_parser(
        "play", help="Play Blossom with optionally specified bank"
    )
    playParser.add_argument("bank", nargs="?", default=None, help="Bank of letters (optional)")
    
    searchParser = subparsers.add_parser("search", help="Search for words")
    searchParser.add_argument("queries", nargs="*", help="Words to be searched")

    args = parser.parse_args()

    blossom = Blossom()
    session = Session(blossom)

    match args.choice:
        case "stats":
            session.mode = "stats"
        case "search":
            session.mode = "search"
            session.queries = args.queries
        case "settings":
            session.mode = "settings"
        case _:
            if "bank" in args:
                session.played = True
                session.lastBank = args.bank
                session.mode = "play"
            else:
                session.mode = "menu"
    session.run()

