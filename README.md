Blostma
==========

[Blossom](https://www.merriam-webster.com/games/blossom-word-game) is a word game published by Merriam-Webster. [Blostma](https://en.wiktionary.org/wiki/blostma#Old_English) is a command-line companion which automates play with a look-ahead strategy, keeps long-term records, and helps curate the underlying word list. It achieves a median score of 454 points, having played roughly 160 banks.

Features
--------

- **Interactive control loop** – Choose to play, search the dictionary, review statistics, adjust settings, or submit data from a single terminal menu.
- **Automated gameplay** – Given a seven-letter bank, select the best-scoring words for each round, announce scores with a typewriter effect, and track personal bests.
- **Word list management** – Search for one or more words, validate new discoveries, or flag mistakes. Changes accumulate locally until you submit them.
- **Persistent records** – Store validated words, removal requests, high scores, and per-bank results in JSON files so you can track progress over time.
- **Typewriter animation** – configurable.
- **Refresh exploit** - Enable the use of an exploit in which the user refreshes the page before the word finishes scoring. This has the effect of scoring the word without advancing the special letter, giving the engine greater control over the special letter.

Installation
------------

Install via pip:

```bash
pip install -e .
```

Usage
-----

Run the CLI script to open the interactive menu:

```bash
blostma
```

You can also bypass the menu and run subcommands directly:

```bash
blostma play                  # prompt for a bank
blostma play ienstvx          # play using a provided bank (center letter first)
blostma search                # interactive dictionary lookup/add
blostma search foo bar        # search specific words
blostma stats                 # show stats
blostma --help                # show all options
```

Data files
----------

The repo contains a sample data directory `sample_data/` with the persistent data files:

- `wordlist.json` – Known words and their validation status.
- `gameScores.json` - Overall game scores and ranked history.
- `wordScores.json` - Individual word scores.
- `settings.json` – User-configurable options.

Before playing you should rename the sample data directory to `data`.

Changes you make while playing or editing accumulate in memory.

Project layout
--------------

- `src/blostma/cli.py` – Argument parsing and menu routing.
- `src/blostma/blossom.py` - Handles information that persists between sessions.
- `src/blostma/format.py` - Formatting helpers.
- `src/blostma/session.py` - Handles game sessions.
- `src/blostma/utils.py` – Other helpers for prompts and scoring.

Happy blossoming!
