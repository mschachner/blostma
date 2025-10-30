import json
import subprocess
from datetime import datetime

from .utils import selectMultiple, selectMultipleMD, getResponseMenu, _tprint, formatScore, formatWordScore, formatScores, pending, colorBold, blankData

# All effectful functions go in this file, as well as everything that accesses the data files.

# ========================== Updater functions for the data files ==========================

def addGameScores(gameScores):
    for gameScore in gameScores:
        if any(gameScore["bank"] == score["bank"] for score in allScores):
            for i, score in enumerate(allScores):
                if gameScore["bank"] == score["bank"]:
                    allScores[i] = gameScore
                    break
        else:
            allScores.append(gameScore)
    allScores.sort(key=lambda x: x["score"], reverse=True)
    with open(metadata["gameScores"]["location"], "w") as f:
        json.dump({"wordHighScore": wordHighScore, "allScores": allScores}, f, indent=2)
    return

def setWordHighScore(wordHighScore):
    if not wordHighScore:
        return
    with open(metadata["gameScores"]["location"], "w") as f:
        json.dump({"wordHighScore": wordHighScore, "allScores": allScores}, f, indent=2)

def validateWords(words):
    fD = fullDictionary()
    for word in words:
        fD[word] = True
    fD = dict(sorted(fD.items(), key=lambda item: item[0]))
    with open(metadata["wordsToValidate"]["location"], "w", encoding="utf-8") as outfile:
        json.dump(fD, outfile, indent=2)
    return

def removeWords(words):
    fD = fullDictionary()
    for word in [w for w in words if w in fD]:
        del fD[word]
    with open(metadata["wordsToRemove"]["location"], "w", encoding="utf-8") as outfile:
        json.dump(fD, outfile, indent=2)
    return

# ========================== Load the data files ==========================

def loadDict(bank=None):
    with open(metadata["wordsToValidate"]["location"], "r") as infile:
        dictionary = json.load(infile)
    if not bank:
        return dictionary
    output = {}
    for word in dictionary:
        if any(c == bank[0] for c in word) and all(c in bank for c in word):
            output[word] = dictionary[word]
    return output

def loadSettings():
    with open("data/settings.json", "r") as infile:
        settings = json.load(infile)
    return settings

# ========================== Functions accessing the data files ==========================

def searchWords(queries=None, fast=False):
    fD = fullDictionary()
    wordsToValidate = []
    wordsToRemove = []
    showValidate = False
    showRemove = False
    opts = ["done"]
    tprint = print if fast else _tprint
    if not queries:
        response = input("Enter words to search (comma or space separated):\n > ")
        queries = [w.strip() for w in response.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    if not queries:
        return [], []
    padding = 5 + max(len(dispWord(word)) for word in queries)

    tprint("Search results:")
    for word in queries:
        if not showRemove and word in fD:
            showRemove = True
            opts.insert(0, "remove")
            if not fD[word]:
                opts.insert(0, "validate all")
        if not showValidate and word not in fD:
            showValidate = True
            opts.insert(0, "validate all")
        dword = dispWord(word)
        msg = (
            ": Not found"
            if word not in fD
            else ": Validated"
            if fD[word]
            else ": Present, not validated"
        )
        tprint(dword + (padding - len(dword)) * " " + msg)
    match getResponseMenu("What would you like to do?", opts):
        case "validate all":
            wordsToValidate = [x for x in queries if x not in fD or not fD[x]]
        case "remove":
            wordsToRemove = selectMultiple("Remove which?", queries)
        case "done":
            pass
    return wordsToValidate, wordsToRemove

def dispWord(word, forGit=False):
    fD = fullDictionary()
    color = (
        "red" if word not in fD else "yellow" if not fD[word] else "green"
    )
    icon = (
        "❌ "
        if word not in fD
        else "🟡 "
        if not fD[word]
        else "🌸 "
        if len(set(word)) == 7
        else "✅ "
    )
    if forGit:
        return icon + word.upper()
    return icon + colorBold(color, word.upper())

def dispWords(words, forGit=False):
    return "\n ".join(dispWord(word, forGit) for word in words)

def showRank(score, fast=False):
    tprint = print if fast else _tprint
    rk = 1
    for sc in allScores:
        if score > sc["score"]:
            break
        rk += 1
    tprint(f"Rank: {rk}/{len(allScores)}")
    if rk == 1:
        tprint("That's a new high score!")
    return

def showStats(fast=False, topCount=10):
    fD = fullDictionary()
    tprint = print if fast else _tprint
    longestWord = max((word for word in fD if fD[word]), key=len)
    totalWords = len(fD)
    validatedWords = sum(1 for word in fD if fD[word])
    totalPangrams = sum(1 for word in fD if len(set(word)) == 7)
    validatedPangrams = sum(1 for word in fD if fD[word] and len(set(word)) == 7)
    pad = 25  # Width for the first column
    tprint(f"{'Banks played:':<{pad}} {len(allScores)}")
    tprint(f"{'Total words:':<{pad}} {totalWords}")
    tprint(f"{'Validated words:':<{pad}} {validatedWords} ({validatedWords/totalWords*100:.2f}%)")
    tprint(f"{'Total pangrams:':<{pad}} {totalPangrams}")
    tprint(f"{'Validated pangrams:':<{pad}} {validatedPangrams} ({validatedPangrams/totalPangrams*100:.2f}%)")
    tprint(
        f"{'Longest validated word:':<{pad}} {dispWord(longestWord)} ({len(longestWord)} letters)"
    )
    tprint(
        f"{'Highest word score:':<{pad}} {dispWord(wordHighScore["word"])} ({wordHighScore["specialLetter"].upper()}), {wordHighScore["score"]} points"
    )
    medianIndex = len(allScores)//2
    tprint("Top scores:")
    pad = max(len(formatScore(sc)) for sc in allScores)
    for i in range(min(topCount, len(allScores))):
        note = "" if i != medianIndex else " (median)"
        sc = allScores[i]   
        tprint(
            f"{i+1}.{'  ' if i < 9 else ' '}{formatScore(sc).rjust(pad)}{note}"
        )
    if topCount < medianIndex:
        tprint("⋮")
        tprint(f"{medianIndex+1}.{'  ' if medianIndex < 9 else ' '}{formatScore(allScores[medianIndex]).rjust(pad)} (median)")
        tprint("⋮")
    tprint(f"{len(allScores)}. {formatScore(allScores[-1]).rjust(pad)} (lowest)")

def setSettings(fast=False):
    tprint = print if fast else _tprint
    print("Settings")

# ========================== Git functions ==========================

def pushData(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"auto: submitted at {timestamp}"
    body = formatData(data, forGit=True)
    files = ["data/settings.json", "data/wordlist.json", "data/scores.json"]

    if not pending(data):
        print("Nothing to submit.")
        return
    if data["gameScores"]:
        body += f"Game scores: {formatScores(data['gameScores'])}\n"
    if data["wordScoreRecord"]:
        body += f"Word score record: {formatWordScore(data['wordScoreRecord'])}\n"
    if data["wordsToValidate"]:
        body += f"Words validated: {dispWords(data['wordsToValidate'], forGit=True)}\n"
    if data["wordsToRemove"]:
        body += f"Words removed: {dispWords(data['wordsToRemove'], forGit=True)}\n"

    
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

def formatData(data, forGit=False):
    formatted = ""
    if data["gameScores"]:
        formatted += f"Game scores: {formatScores(data['gameScores'])}\n"
    if data["wordScoreRecord"]:
        formatted += f"Word score record: {formatWordScore(data['wordScoreRecord'])}\n"
    if data["wordsToValidate"]:
        formatted += f"Words validated: {dispWords(data['wordsToValidate'], forGit=forGit)}\n"
    if data["wordsToRemove"]:
        formatted += f"Words removed: {dispWords(data['wordsToRemove'], forGit=forGit)}\n"
    return formatted


def approveData(data, fast=False):
    tprint = print if fast else _tprint
    if not pending(data):
        tprint("Nothing to update.")
        return data
    approved = {}
    tprint("To be updated:")
    tprint(formatData(data, forGit=False))
    match getResponseMenu("What do you want to update?", ["[a] all", "[n] none", "[s] some"]):
        case "[a] all":
            approved = data
        case "[n] none":
            tprint("Nothing updated.")
            return data
        case "[s] some":
            md = {d: metadata[d] for d in metadata if data[d]}
            for choice in selectMultipleMD("Update which?", md):
                approved[choice] = data[choice]
    return approved

def updateData(dataToUpdate, fast=False):
    tprint = print if fast else _tprint
    approved = approveData(dataToUpdate, fast=fast)
    for d in metadata:
        if d in approved:
            metadata[d]["update"](approved[d])
    tprint("Updated.")
    return

# ========================== Package it up ==========================

metadata = {
    "gameScores": {
        "name": "Game scores",
        "location": "data/scores.json",
        "update": addGameScores,
        "format": formatScores
    },
    "wordScoreRecord": {
        "name": "Word score record",
        "location": "data/scores.json",
        "update": setWordHighScore,
        "format": formatWordScore
    },
    "wordsToValidate": {
        "name": "Words to validate",
        "location": "data/wordlist.json",
        "update": validateWords,
        "format": dispWords
    },
    "wordsToRemove": {
        "name": "Words to remove",
        "location": "data/wordlist.json",
        "update": removeWords,
        "format": dispWords
    }
}

with open(metadata["gameScores"]["location"], "r") as f:
    scores = json.load(f)

wordHighScore = scores["wordHighScore"]
print(scores.keys())
allScores = scores["allScores"]
settings = loadSettings()

def fullDictionary():
    with open(metadata["wordsToValidate"]["location"], "r") as infile:
        dictionary = json.load(infile)
    return dictionary


