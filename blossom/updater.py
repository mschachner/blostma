import json
import subprocess
from datetime import datetime

from .utils import getResponseMenu
from .format import formatWordPure, formatWordScorePure, formatGameScore, formatStatsGameScore, formatWordScores, _tprint

# ========================== Updater functions for the data files ==========================

# Getters
def getGameScores():
    with open("data/gameScores.json", "r") as infile:
        return json.load(infile)
def getWordScores():
    with open("data/wordScores.json", "r") as infile:
        return json.load(infile)
def getDictionary(bank=None):
    with open("data/wordlist.json", "r") as infile:
        dictionary = json.load(infile)
    if bank:
        return {word: dictionary[word] for word in dictionary if any(c == bank[0] for c in word) and all(c in bank for c in word)}
    return dictionary

# Setters (includes sorting)
def setGameScores(gameScores):
    gameScores.sort(key=lambda x: x["score"], reverse=True)
    with open("data/gameScores.json", "w") as outfile:
        json.dump(gameScores, outfile, indent=2)
def setWordScores(wordScores):
    wordScores.sort(key=lambda x: x["score"], reverse=True)
    with open("data/wordScores.json", "w") as outfile:
        json.dump(wordScores, outfile, indent=2)
def setDictionary(dictionary):
    dictionary = dict(sorted(dictionary.items(), key=lambda item: item[0]))
    with open("data/wordlist.json", "w", encoding="utf-8") as outfile:
        json.dump(dictionary, outfile, indent=2)

# Add a list of game scores.
def addGameScores(gameScoresToAdd):
    gameScores = getGameScores()
    for gameScoreToAdd in gameScoresToAdd:
        seenBefore = False
        # If we've played this bank before, and the score is higher, update the score.
        # Otherwise, add the score to the list.
        for i, gameScore in enumerate(gameScores):
            if gameScoreToAdd["bank"] == gameScore["bank"]:
                seenBefore = True
                if gameScoreToAdd["score"] > gameScore["score"]:
                    gameScores[i] = gameScoreToAdd
                    continue
                else:
                    continue
        if not seenBefore:
            gameScores.append(gameScoreToAdd)
    setGameScores(gameScores)
    return

# Add a list of word scores.
def addWordScores(wordScoresToAdd):
    wordScores = getWordScores()
    for wordScoreToAdd in wordScoresToAdd:
        # Idempotent
        if any(wordScoreToAdd == wordScore for wordScore in wordScores):
            continue
        wordScores.append(wordScoreToAdd)
    setWordScores(wordScores)
    return

# Validate or remove a list of words.
def validateWords(words):
    dictionary = getDictionary()
    for word in words:
        dictionary[word] = True
    setDictionary(dictionary)
    return

def removeWords(words):
    dictionary = getDictionary()
    for word in [w for w in words if w in dictionary]:
        del dictionary[word]
    setDictionary(dictionary)
    return

# Update the data files with the given data.
def updateData(dataToUpdate):
    if dataToUpdate["gameScores"]:
        addGameScores(dataToUpdate["gameScores"])
    if dataToUpdate["wordScores"]:
        addWordScores(dataToUpdate["wordScores"])
    if dataToUpdate["wordsToValidate"]:
        validateWords(dataToUpdate["wordsToValidate"])
    if dataToUpdate["wordsToRemove"]:
        removeWords(dataToUpdate["wordsToRemove"])
    return

# ========================== Functions accessing the data files ==========================

# Get word validation status(es)
def wordStatuses(words):
    dictionary = getDictionary()
    statuses = {}
    for word in words:
        if word not in dictionary:
            statuses[word] = "not found"
        elif not dictionary[word]:
            statuses[word] = "present, not validated"
        else:
            statuses[word] = "validated"
    return statuses

def wordStatus(word):
    return wordStatuses([word])[word]

# Impure versions of formatWord and formatWordScore (get status if not provided)
def formatWord(word, style="terminal", status=None, padding=0):
    if not status:
        status = wordStatus(word)
    return formatWordPure(word, status, style, padding)

def formatWordScore(wordScore, style="terminal", status=None):
    if not status:
        status = wordStatus(wordScore["word"])
    return formatWordScorePure(wordScore, style, status)

def searchWords(queries=None, fast=False):
    tprint = print if fast else _tprint
    if not queries:
        return
    tprint("Search results:")
    statuses = wordStatuses(queries)
    for word in queries:
        tprint(formatWord(word, style="search", status=statuses[word]))
    return

def showRank(score, fast=False):
    allScores = getGameScores()
    tprint = print if fast else _tprint
    rank = len([sc for sc in allScores if score < sc["score"]]) + 1
    tprint(f"Rank: {rank}/{len(allScores)}")
    if rank == 1:
        tprint("That's a new high score!")
    return

def showStats(fast=False, topCount=10, bottomCount=4, showMedian=True):
    d, gameScores, wordScores = getDictionary(), getGameScores(), getWordScores()
    tprint = print if fast else _tprint
    longestWord = max((word for word in d if d[word]), key=len)
    totalWords = len(d)
    validatedWords = sum(1 for word in d if d[word])
    totalPangrams = sum(1 for word in d if len(set(word)) == 7)
    validatedPangrams = sum(1 for word in d if d[word] and len(set(word)) == 7)
    pad = 25  # Width for the first column
    tprint(f"{'Banks played:':<{pad}} {len(gameScores)}")
    tprint(f"{'Total words:':<{pad}} {totalWords}")
    tprint(f"{'Validated words:':<{pad}} {validatedWords} ({validatedWords/totalWords*100:.2f}%)")
    tprint(f"{'Total pangrams:':<{pad}} {totalPangrams}")
    tprint(f"{'Validated pangrams:':<{pad}} {validatedPangrams} ({validatedPangrams/totalPangrams*100:.2f}%)")
    tprint(
        f"{'Longest validated word:':<{pad}} {formatWord(longestWord, style="terminal", status="validated")} ({len(longestWord)} letters)"
    )
    tprint(
        f"{'Highest word score:':<{pad}} {formatWordScore(wordScores[0], style="terminal")}"
    )
    tprint(f"Top scores:\n{formatStatsGameScore(gameScores, topCount=topCount, bottomCount=bottomCount, showMedian=showMedian)}")

def setSettings(fast=False):
    tprint = print if fast else _tprint
    tprint("Settings")

# ========================== Git ==========================

# Summary formatting (also used for terminal display)
def formatData(data, style="terminal"):
    body = ""
    if data["gameScores"]:
        body += "Game scores:\n" + "\n".join(formatGameScore(sc, style).rstrip() for sc in data["gameScores"]) + "\n"
    if data["wordScores"]:
        body += "Word scores:\n" + formatWordScores(data["wordScores"], style) + "\n"
    if data["wordsToValidate"]:
        body += "Validated words:\n" if style == "git" else "Words to validate:\n"
        body += "\n".join(formatWord(word, style, status="validated").rstrip() for word in data["wordsToValidate"]) + "\n"
    if data["wordsToRemove"]:
        body += "Removed words:\n" if style == "git" else "Words to remove:\n"
        body += "\n".join(formatWord(word, style).rstrip() for word in data["wordsToRemove"])
    return body

def pushData(data,fast=False, verifyFirst=False):
    tprint = print if fast else _tprint
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"auto: submitted at {timestamp}"
    body = formatData(data, style="git")
    files = ["data/wordlist.json", "data/gameScores.json", "data/wordScores.json"]

    if verifyFirst:
        tprint("Data to submit:")
        tprint(formatData(data, style="terminal").rstrip("\n"))
        if getResponseMenu("Submit the above?", ["[y] yes", "[n] no"]) != "[y] yes":
            tprint("Nothing submitted.")
            return
    
    subprocess.run(
        ["git", "add", *files],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # If nothing is staged, skip committing to avoid a non-zero exit from git.
    staged_check = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    if staged_check.returncode == 0:
        print("Nothing to commit.")
        return

    commit = subprocess.run(
        ["git", "commit", "-m", summary, "-m", body],
        check=False,
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        # Surface the real git error instead of hiding it
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
