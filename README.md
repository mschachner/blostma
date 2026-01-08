Blossom
==========

[Blossom](https://www.merriam-webster.com/games/blossom-word-game) is a word game published by Merriam-Webster. This is a command-line companion which automates play with a look-ahead strategy, keeps long-term records, and helps curate the underlying word list. It achieves a median score of 454 points, having played roughly 150 banks.

Features
--------

- **Interactive control loop** – Choose to play, search the dictionary, review statistics, adjust settings, or submit data from a single terminal menu.
- **Automated gameplay** – Given a seven-letter bank (center letter first), select the best-scoring words for each round, announce scores with a typewriter effect, and track personal bests.
- **Word list management** – Search for one or more words, validate new discoveries, or flag mistakes. Changes accumulate locally until you submit them.
- **Persistent records** – Store validated words, removal requests, high scores, and per-bank results in JSON files so you can track progress over time.
- **Git-backed submissions** – When you choose to submit data, the tool stages the updated JSON files, creates a descriptive commit, and pushes to the `main` branch.
- **Typewriter animation** – configurable.
- **Refresh exploit** - Enable the use of an exploit in which the user refreshes the page before the word finishes scoring. This has the effect of scoring the word without advancing the special letter, giving the engine greater control over the special letter.

Installation
------------

Requirements are Python 3.10+, [`scipy`](https://scipy.org/), and [`simple-term-menu`](https://pypi.org/project/simple-term-menu/).

```bash
pip install simple-term-menu scipy
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
python blossom.py search                # interactive dictionary lookup/add
python blossom.py search foo bar        # search specific words
python blossom.py stats                 # show stats
python blossom.py --help                # show all options
```

Data files
----------

All persistent data lives in the `data/` directory:

- `data/wordlist.json` – Known words and their validation status.
- `data/gameScores.json` - Overall game scores and ranked history.
- `data/wordScores.json` - Individual word scores.
- `data/settings.json` – User-configurable options (still in development).

Changes you make while playing or editing accumulate in memory until you select **Submit data**. Then you can preview the pending updates, apply them to the JSON files, and (if approved) commit and push the results.

Project layout
--------------

- `blossom/cli.py` – Argument parsing and menu routing.
- `blossom/game.py` – Core gameplay loop and scoring logic.
- `blossom/engine.py` - Engine play.
- `blossom/updater.py` – Word list editing, statistics reporting, and Git integration.
- `blossom/format.py` - Formatting helpers.
- `blossom/utils.py` – Other helpers for prompts and scoring.
- `blossom.py` – Minimal entry point that launches the CLI.

Happy blossoming!
