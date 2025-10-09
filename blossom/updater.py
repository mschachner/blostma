import json
import subprocess
from datetime import datetime

from .utils import selectMultiple, getResponseMenu, _tprint, STYLES, formatScore, formatWordScore, formatScores

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
        json.dump({"wordHighScore": wordHighScore, "allScores": allScores}, f)
    return

def setWordHighScore(wordHighScore):
    with open(metadata["gameScores"]["location"], "w") as f:
        json.dump({"wordHighScore": wordHighScore, "allScores": allScores}, f)

def validateWords(words):
    fD = fullDictionary()
    for word in words:
        fD[word] = True
    fD = dict(sorted(fD.items(), key=lambda item: item[0]))
    with open(metadata["wordsToValidate"]["location"], "w", encoding="utf-8") as outfile:
        json.dump(fD, outfile)
    return

def removeWords(words):
    fD = fullDictionary()
    for word in words:
        del fD[word]
    with open(metadata["wordsToRemove"]["location"], "w", encoding="utf-8") as outfile:
        json.dump(fD, outfile)
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
# ========================== Functions accessing the data files ==========================

def searchWords(queries=None, fast=False):
    fD = fullDictionary()
    tprint = print if fast else _tprint
    if not queries:
        response = input("Enter words to search (comma or space separated):\n > ")
        queries = [w.strip() for w in response.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    padding = 5 + max(len(dispWord(word)) for word in queries)

    tprint("Search results:")
    for word in queries:
        dword = dispWord(word)
        msg = (
            ": Not found"
            if word not in fD
            else ": Validated"
            if fD[word]
            else ": Present, not validated"
        )
        tprint(dword + (padding - len(dword)) * " " + msg)

    if any(word not in fD or not fD[word] for word in queries) and getResponseMenu(
        "Add/validate all words? (yes/no)", ["yes", "no"]
    ) == "yes":
        return True
    return False

def dispWord(word):
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
    return icon + f"{STYLES['bold' + color]}{word.upper()}{STYLES['reset']}"

def dispWords(words):
    return "\n ".join(dispWord(word) for word in words)

def showStats(fast=False):
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
    tprint("Top scores:")
    pad = max(len(formatScore(sc)) for sc in allScores)
    for i in range(min(10, len(allScores))):
        sc = allScores[i]   
        tprint(
            f"{i+1}.{'  ' if i < 9 else ' '}{formatScore(sc).rjust(pad)}"
        )
    tprint(f"Median score: {formatScore(allScores[len(allScores)//2]).rjust(pad)}")
    tprint(f"Lowest score: {formatScore(allScores[-1]).rjust(pad)}")

# ========================== Git functions ==========================

def pushFiles(files, body):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = f"auto: submitted at {timestamp}"
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
    return

def submit(newData):
    filesToSubmit = []
    approved = {data: None for data in metadata}
    body = ""
    print("To be submitted:")
    for d, md in metadata.items():
        if newData[d]:
            print(f"{md["name"]}:\n {md["format"](newData[d])}")
    match getResponseMenu("What do you want to submit?", ["Submit all", "Submit none", "Submit some"]):
        case "Submit all":
            approved = newData
        case "Submit none":
            return
        case "Submit some":
            for choice in selectMultiple("Submit which?", metadata):
                approved[choice] = newData[choice]
    for d, md in metadata.items():
        if approved[d]:
            md["update"](approved[d])
            filesToSubmit.append(md["location"])
            body += f"{md["name"]}:\n {md["format"](approved[d])}\n"
    if filesToSubmit:
        pushFiles(filesToSubmit, body)
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
allScores = scores["allScores"]

def fullDictionary():
    with open(metadata["wordsToValidate"]["location"], "r") as infile:
        dictionary = json.load(infile)
    return dictionary


