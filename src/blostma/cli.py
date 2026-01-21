import argparse

from .blossom import Blossom
from .session import Session

def main():
    print("running blostma.cli.main")
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="choice", required=False)

    playParser = subparsers.add_parser(
        "play", help="Play Blossom with optionally specified bank"
    )
    playParser.add_argument("bank", nargs="?", default=None, help="Bank of letters (optional)")
    
    searchParser = subparsers.add_parser("search", help="Search for words")
    searchParser.add_argument("queries", nargs="*", help="Words to be searched")

    statsParser = subparsers.add_parser("stats", help="Show stats")
    settingsParser = subparsers.add_parser("settings", help="Update settings")
    quitParser = subparsers.add_parser("quit", help="Quit")

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

if __name__ == "__main__":
    main()