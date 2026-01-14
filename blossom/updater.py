import json
import subprocess
from datetime import datetime
import sys

from .format import formatWordPure, formatWordScorePure, formatGameScore, formatStatsGameScore, formatWordScores, _tprint

from .utils import getResponseBy, getResponseMenu

# ========================== Classes and functions for the data files ==========================

# The Blossom class holds all information that should persist between sessions.
# The Session class holds all information that persists between games but not between sessions.

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
        return
    
    # Add game scores to the current state of the BlossomInfo object.
    def addGameScores(self, gameScoresToAdd):
        for gameScoreToAdd in gameScoresToAdd:
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
    def addWordScores(self, wordScoresToAdd):
        for wordScoreToAdd in wordScoresToAdd:
            if any(wordScoreToAdd == wordScore for wordScore in self.wordScores):
                continue
            self.wordScores.append(wordScoreToAdd)
        return
    
    # Validate words in the current state of the BlossomInfo object.
    def validateWords(self, words):
        for word in words:
            self.wordlist[word] = True
        return
    
    # Remove words from the current state of the BlossomInfo object.
    def removeWords(self, words):
        for word in [w for w in words if w in self.wordlist]:
            del self.wordlist[word]
        return

    def updateSettings(self):
        while True:
            options = [
                f"Fast mode: {"Enabled" if self.settings["fast"] else "Disabled"}",
                f"Allow refresh exploit: {"Enabled" if self.settings["allowRefresh"] else "Disabled"}",
                f"Number of top/bottom scores to show: {self.settings["numScores"]}",
                "Back"]
            match options.index(getResponseMenu("Settings",options)):
                case 0:
                    self.settings["fast"] = getResponseMenu("Fast mode?", ["[y] yes", "[n] no"]) == "[y] yes"
                    continue
                case 1:
                    self.settings["allowRefresh"] = getResponseMenu("Allow refresh exploit?", ["[y] yes", "[n] no"]) == "[y] yes"
                case 2:
                    self.settings["numScores"] = int(getResponseBy(
                        "How many top and bottom scores should be shown?",
                        lambda x: 1 <= int(x) and int(x) <= 10,
                        "Please enter an integer between 1 and 10, inclusive."))
                case 3:
                    break
        return

    # Update the data in the current state of the BlossomInfo object.
    def updateDataFromSession(self, session):
        self.addGameScores(session.data["gameScores"])
        self.addWordScores(session.data["wordScores"])
        self.validateWords(session.data["wordsToValidate"])
        self.removeWords(session.data["wordsToRemove"])
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
    def searchWords(self, queries=None):
        if not queries:
            return
        self.tprint("Search results:")
        statuses = self.wordStatuses(queries)
        for word in queries:
            self.tprint(self.formatWord(word, style="search", status=statuses[word]))
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

    def formatData(self, session, style="terminal"):
        body = ""
        data = session.dataToSubmit
        if data["gameScores"]:
            body += "Game scores:\n" + "\n".join(formatGameScore(sc, style).rstrip() for sc in data["gameScores"]) + "\n"
        if data["wordScores"]:
            body += "Word scores:\n" + formatWordScores(data["wordScores"], style) + "\n"
        if data["wordsToValidate"]:
            body += "Validated words:\n" if style == "git" else "Words to validate:\n"
            body += "\n".join(self.formatWord(word, style, status="validated").rstrip() for word in data["wordsToValidate"]) + "\n"
        if data["wordsToRemove"]:
            body += "Removed words:\n" if style == "git" else "Words to remove:\n"
            body += "\n".join(self.formatWord(word, style).rstrip() for word in data["wordsToRemove"])
        return body

    def tprint(self, *objects, sep=" ", end="\n", file=sys.stdout, flush=False):
        if not self.settings["fast"]:
            return print(*objects, sep=sep, end=end, file=file, flush=flush)
        return _tprint(*objects, sep=sep, end=end, file=file, flush=flush)

    def wordScoreRecord(self):
        return max(self.wordScores, key=lambda x: x["score"])["score"]

    
# The Session class holds all information that persists between games but not between sessions.

class Session:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.data = {
            "wordScores": [],
            "gameScores": [],
            "wordsToRemove": set(),
            "wordsToValidate": set()
        }
        self.menued = False # Whether the user has been to the main menu before this session.
        self.played = False # Whether the user has played a game this session.
        self.refreshed = False # Whether the user has just used the refresh exploit.
        self.lastBank = None # The bank of the last game played.

    def pending(self):
        return any(self.data[key] for key in self.data)
    
    def clearData(self):
        self.data = {
            "wordScores": [],
            "gameScores": [],
            "wordsToRemove": set(),
            "wordsToValidate": set()
        }
        return


# ========================== Git ==========================

def pushDataFiles(blossom, session, style="git", verifyFirst=False):
    summary = f"auto: submitted at {session.timestamp}"
    body = session.formatData(style="git")
    blossom.write()

    commit = subprocess.run(
        ["git", "commit", "-m", summary, "-m", body],
        check=False,
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        print((commit.stderr or "git commit failed.").strip())
        raise subprocess.CalledProcessError(commit.returncode, commit.args, output=commit.stdout, stderr=commit.stderr)

    push = subprocess.run(
        ["git", "push", "origin", "main"],
        check=False,
        capture_output=True,
        text=True,
    )
    if push.returncode != 0:
        print((push.stderr or "git push failed.").strip())
        raise subprocess.CalledProcessError(push.returncode, push.args, output=push.stdout, stderr=push.stderr)
    print("Data submitted.")
    return