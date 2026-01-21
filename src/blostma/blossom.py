import json
import sys

from .format import formatWordPure, formatWordScorePure, formatStatsGameScore, _tprint
from .utils import menu

# The Blossom class holds all information that should persist between sessions.

class Blossom:
    def __init__(self):
        with open("data/gameScores.json", "r") as infile:
            self.gameScores = json.load(infile)
        with open("data/wordScores.json", "r") as infile:
            self.wordScores = json.load(infile)
        with open("data/wordlist.json", "r") as infile:
            self.wordlist = json.load(infile)
        with open("data/settings.json", "r") as infile:
            self.settings = json.load(infile)
        return

    def write(self):
        self.gameScores.sort(key=lambda x: x["score"], reverse=True)
        with open("data/gameScores.json", "w") as outfile:
            json.dump(self.gameScores, outfile, indent=2)
        self.wordScores.sort(key=lambda x: x["score"], reverse=True)
        with open("data/wordScores.json", "w") as outfile:
            json.dump(self.wordScores, outfile, indent=2)
        self.wordlist = dict(sorted(self.wordlist.items(), key=lambda item: item[0]))
        with open("data/wordlist.json", "w", encoding="utf-8") as outfile:
            json.dump(self.wordlist, outfile, indent=2)
        with open("data/settings.json", "w") as outfile:
            json.dump(self.settings, outfile, indent=2)
        print("Data saved locally.")
        return
    
    # Add game scores to the current state of the BlossomInfo object.
    def addGameScore(self, gameScoreToAdd):
        seenBefore = False
        for i, gameScore in enumerate(self.gameScores):
            if gameScoreToAdd["bank"] == gameScore["bank"]:
                seenBefore = True
                if gameScoreToAdd["score"] > gameScore["score"]:
                    self.gameScores[i] = gameScoreToAdd
                    continue
                else:
                    continue
        if not seenBefore:
            self.gameScores.append(gameScoreToAdd)
        return
    
    # Add word scores to the current state of the BlossomInfo object.
    def addWordScore(self, wordScoreToAdd):
        if any(wordScoreToAdd == wordScore for wordScore in self.wordScores):
            return
        self.wordScores.append(wordScoreToAdd)
        return
    
    # Validate words in the current state of the BlossomInfo object.
    def validateWord(self, word):
        self.wordlist[word] = True
        return
    
    # Remove words from the current state of the BlossomInfo object.
    def removeWord(self, word):
        del self.wordlist[word]
        return

    def updateSettings(self):
        while True:
            options = [
                f"Fast mode: {"Enabled" if self.settings["fast"] else "Disabled"}",
                f"Autosave locally at game end: {"Enabled" if self.settings["autosave"] else "Disabled"}",
                f"Allow refresh exploit: {"Enabled" if self.settings["allowRefresh"] else "Disabled"}",
                f"Number of top/bottom scores to show: {self.settings["numScores"]}",
                "Back"]
            match options.index(menu("Settings",options)):
                case 0:
                    self.settings["fast"] = menu("Fast mode?", ["[y] yes", "[n] no"]) == "[y] yes"
                    continue
                case 1:
                    self.settings["autosave"] = menu("Autosave locally at game end?", ["[y] yes", "[n] no"]) == "[y] yes"
                    continue
                case 2:
                    self.settings["allowRefresh"] = menu("Allow refresh exploit?", ["[y] yes", "[n] no"]) == "[y] yes"
                    continue
                case 3:
                    self.settings["numScores"] = int(self.getResponseBy(
                        "How many top and bottom scores should be shown?",
                        lambda x: 1 <= int(x) and int(x) <= 10,
                        "Please enter an integer between 1 and 10, inclusive."))
                    continue
                case 4:
                    break
        return
    
    def showStats(self):
        longestWord = max((word for word in self.wordlist if self.wordlist[word]), key=len)
        totalWords = len(self.wordlist)
        validatedWords = sum(1 for word in self.wordlist if self.wordlist[word])
        totalPangrams = sum(1 for word in self.wordlist if len(set(word)) == 7)
        validatedPangrams = sum(1 for word in self.wordlist if self.wordlist[word] and len(set(word)) == 7)
        pad = 25  # Width for the first column
        self.tprint(f"{'Banks played:':<{pad}} {len(self.gameScores)}")
        self.tprint(f"{'Total words:':<{pad}} {totalWords}")
        self.tprint(f"{'Validated words:':<{pad}} {validatedWords} ({validatedWords/totalWords*100:.2f}%)")
        self.tprint(f"{'Total pangrams:':<{pad}} {totalPangrams}")
        self.tprint(f"{'Validated pangrams:':<{pad}} {validatedPangrams} ({validatedPangrams/totalPangrams*100:.2f}%)")
        self.tprint(
            f"{'Longest validated word:':<{pad}} {self.formatWord(longestWord, style="terminal", status="validated")} ({len(longestWord)} letters)"
        )
        self.tprint(
            f"{'Highest word score:':<{pad}} {self.formatWordScore(self.wordScores[0], style="terminal")}"
        )
        self.tprint(f"Top scores:\n{formatStatsGameScore(self.gameScores, topCount=self.settings["numScores"], bottomCount=self.settings["numScores"], showMedian=True)}")
        return
    
    # Show the rank of a given score in the current state of the BlossomInfo object.
    def showRank(self, score):
        rank = len([sc for sc in self.gameScores if score < sc["score"]]) + 1
        self.tprint(f"Rank: {rank}/{len(self.gameScores)}")
        if rank == 1:
            self.tprint("That's a new high score!")
        return

    # Search for words in the current state of the BlossomInfo object.
    def search(self, session):
        if not session.queries:
            self.tprint("Fine, don't search anything then. 🙄")
            return
        self.tprint("Search results:")
        statuses = self.wordStatuses(session.queries)
        for word in session.queries:
            self.tprint(self.formatWord(word, style="search", status=statuses[word]))
        match menu(
            "What would you like to do?",
            ["[v] validate", "[r] remove", "[c] cancel"]
            ):
            case "[v] validate":
                for word in session.queries:
                    self.validateWord(word)
                    session.data["validated"].add(word)
            case "[r] remove":
                for word in session.queries:
                    self.removeWord(word)
                    session.data["removed"].add(word)
            case "[c] cancel":
                pass
        session.queries = set()
        return

    # Get word validation status(es)
    def wordStatuses(self, words):
        statuses = {}
        for word in words:
            if word not in self.wordlist:
                statuses[word] = "not found"
            elif not self.wordlist[word]:
                statuses[word] = "present, not validated"
            else:
                statuses[word] = "validated"
        return statuses

    def wordStatus(self, word):
        return self.wordStatuses([word])[word]
    
    # Impure versions of formatWord and formatWordScore (get status if not provided)
    def formatWord(self, word, style="terminal", status=None, padding=0):
        if not status:
            status = self.wordStatus(word)
        return formatWordPure(word, status, style, padding)
    
    def formatWordScore(self, wordScore, style="terminal", status=None):
        if not status:
            status = self.wordStatus(wordScore["word"])
        return formatWordScorePure(wordScore, style, status)


    def tprint(self, *objects, sep=" ", end="\n", file=sys.stdout, flush=False):
        if self.settings["fast"]:
            return print(*objects, sep=sep, end=end, file=file, flush=flush)
        return _tprint(*objects, sep=sep, end=end, file=file, flush=flush)

    def wordScoreRecord(self):
        return max(self.wordScores, key=lambda x: x["score"])["score"]

    def getResponseBy(self,msg, cond, invalidMsg, default = None):
        if default:
            if cond(default):
                return default
            else:
                self.tprint(invalidMsg)
        while True:
            attempt = input(msg + "\n > ")
            if cond(attempt):
                return attempt
            self.tprint(invalidMsg)
    
    def getResponse(self, msg, options):
        return self.getResponseBy(msg, lambda r: r in options, f"Valid responses: {', '.join(options)}.")

    
