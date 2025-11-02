Blossom AI
==========

Blossom AI is a command-line companion for Merriam-Webster's [Blossom word game](https://www.merriam-webster.com/games/blossom-word-game). It automates play with a look-ahead strategy, keeps long-term records, and helps curate the underlying word list.

Features
--------

- **Interactive control loop** – Choose to play, search the dictionary, review statistics, adjust settings, or submit data from a single terminal menu.
- **Automated gameplay** – Given a seven-letter bank (center letter first), Blossom AI selects the best-scoring words for each round, announces scores with a typewriter effect, and tracks personal bests.
- **Word list management** – Search for one or more words, validate new discoveries, or flag mistakes. Changes accumulate locally until you submit them.
- **Persistent records** – Stores validated words, removal requests, high scores, and per-bank results in JSON files so you can track progress over time.
- **Git-backed submissions** – When you choose to submit data, the tool stages the updated JSON files, creates a descriptive commit, and pushes to the `main` branch.
- **Fast mode** – Skip the typewriter animation when you want instant feedback.

Installation
------------

Blossom AI requires Python 3.10+ and the [`simple-term-menu`](https://pypi.org/project/simple-term-menu/) package.

```bash
pip install simple-term-menu
```

Usage
-----

Run the entry point script to open the interactive menu:

```bash
python blossom.py
```

You can also bypass the menu and run subcommands directly:

```bash
python blossom.py play                  # prompt for a bank
python blossom.py play resanto          # play using a provided bank (center letter first)
python blossom.py play -f resanto       # play fast
python blossom.py search                # interactive dictionary lookup/add
python blossom.py search foo bar        # search specific words
python blossom.py stats                 # show stats
python blossom.py stats -f              # show stats without the typewriter effect
python blossom.py --help                # show all options
```

Data files
----------

All persistent data lives in the `data/` directory:

- `data/wordlist.json` – Known words and their validation status.
- `data/scores.json` – Overall scores, high-score metadata, and ranked history.
- `data/settings.json` – User-configurable options (edited through the in-app settings menu).

Changes you make while playing or editing accumulate in memory until you select **Submit data**. At that point Blossom AI will preview the pending updates, apply them to the JSON files, and (if approved) commit and push the results.

Project layout
--------------

- `blossom/cli.py` – Argument parsing and menu routing.
- `blossom/game.py` – Core gameplay loop and scoring logic.
- `blossom/updater.py` – Word list editing, statistics reporting, and Git integration.
- `blossom/utils.py` – Shared helpers for prompts, scoring, and formatting.
- `blossom.py` – Minimal entry point that launches the CLI.

Happy blossoming!
