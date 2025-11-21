import os
from datetime import datetime

from .utils import _tprint, condMsg, getResponseBy, getResponseMenu, sevenUniques, pending, scoreWord, advanceSL, blankData, mergeData, selectMultiple
from .updater import updateData, showStats, searchWords, showRank, setSettings, pushData, getDictionary, formatWord, wordStatus, getWordScores

def blossomBetter(bank, dictionary, prevPlayed, round, sL, score):
    allPlays = []
    chosenPlays = {petal: [] for petal in bank[1:]}
    stillNeeded = {petal: 0 for petal in bank[1:]}
    petal = sL
    for i in range(round, 12):
        stillNeeded[petal] += 1
        petal = advanceSL(bank, petal)
    for word in (w for w in dictionary if w not in prevPlayed):
        for petal in bank[1:]:
            allPlays.append((petal, word))
    allPlays.sort(key=lambda x: scoreWord(bank, x[0], x[1]), reverse=True)
    for (petal, word) in allPlays:
        if (
            len(chosenPlays[petal]) < stillNeeded[petal]
            and word not in [w for p in chosenPlays.values() for w in p]
        ):
            chosenPlays[petal].append(word)
        if sum(len(p) for p in chosenPlays.values()) == 12 - round:
            break
    expectedScore = score + sum(
        scoreWord(bank, petal, word) for petal in bank[1:] for word in chosenPlays[petal]
    )
    print(f"Expected score: {expectedScore} points.")
    return chosenPlays[sL][0]


def blossomSearch(queries, dataToSubmit, fast=False):
    tprint = print if fast else _tprint
    dataToUpdate = blankData()
    if not queries:
        queries = getResponseBy(
            "Enter words to search (comma or space separated):",
            lambda w: True,
            None,
            fast=fast
            )
        queries = [w.strip() for w in queries.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    if not queries:
        tprint("Fine, don't search anything then. 🙄")
        return
    searchWords(queries=queries, fast=fast)
    match getResponseMenu(
        "Any changes?",
        ["[v] validate all", "[r] remove all", "[s] select words", "[d] done"]
        ):
        case "[v] validate all":
            dataToUpdate["wordsToValidate"] = queries
        case "[r] remove all":
            dataToUpdate["wordsToRemove"] = queries
        case "[s] select words":
            words = selectMultiple("Which words?", queries)
            match getResponseMenu(
                "What would you like to do?",
                ["[v] validate", "[r] remove", "[d] done"]
                ):
                case "[v] validate":
                    dataToUpdate["wordsToValidate"] = words
                case "[r] remove":
                    dataToUpdate["wordsToRemove"] = queries - words
                case "[d] done":
                    return
    updateData(dataToUpdate)
    mergeData(dataToSubmit, dataToUpdate)
    return

def playBlossom(bank=None, fast=False, choice=None, queries=None):
    os.system("clear")
    dataToSubmit = blankData()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    menued = False
    tprint = print if fast else _tprint
    print(
            r"""
,-----.  ,--.
|  |) /_ |  | ,---.  ,---.  ,---.  ,---. ,--,--,--.
|  .-.  \|  || .-. |(  .-' (  .-' | .-. ||        |
|  '--' /|  |' '-' '.-'  `).-'  `)' '-' '|  |  |  |
`------' `--' `---' `----' `----'  `---' `--`--`--'
🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸
            """
        )
    while True:
        if not choice:
            msg = "What do you want to do?" if not menued else "What do you want to do next?"
            choices = [
                "play", "search", "stats", "settings", "quit"
                ] if not pending(dataToSubmit) else [
                "play", "search", "stats", "settings", "submit data","quit"
                ]
            choice = getResponseMenu(msg, choices)
        match choice:
            case "search":
                choice, menued = None, True
                blossomSearch(queries, dataToSubmit, fast=fast)
                queries = None
            case "stats":
                choice, menued = None, True
                showStats(fast=fast, topCount=10)
                continue
            case "settings":
                choice, menued = None, True
                setSettings(fast=fast)
                continue
            case "submit data":
                choice, menued = None, True
                pushData(dataToSubmit, fast=fast, verifyFirst=True)
                dataToSubmit = blankData()
                continue
            case "quit":
                if pending(dataToSubmit) and getResponseMenu(
                    "Submit all data first?", ["[s] submit data", "[q] quit without submitting"]
                    ) == "[s] submit data":
                    pushData(dataToSubmit, fast=fast, verifyFirst=False)
                tprint("Quitting.")
                return
            case "play":
                choice = None
                menued = True
                prevPlayed = []
                score = 0
                match getResponseBy(
                    "What's the bank? (Center letter first)",
                    lambda b: sevenUniques(b) or b == "quit",
                    "Please enter seven unique letters, or \"quit\".",
                    firstChoice = bank
                ).lower():
                    case "quit":
                        return
                    case bk:
                        bank = bk
                tprint("Okay, let's play!")
                tprint(f"Bank: {bank.upper()}.")
                bank = bank[0] + "".join(sorted(list(bank[1:])))
                dictionary = getDictionary(bank)
                wordScoreRecord = max(getWordScores(), key=lambda x: x["score"])["score"]
                newData = blankData()
                for round in range(12):
                    prefix = ""
                    sL = advanceSL(bank, sL, prevPlayed[-1]) if round > 0 else bank[1]
                    tprint(f"---\nRound {round+1}. Special letter: {sL.upper()}.\n")
                    while True:
                        word = blossomBetter(bank, dictionary, prevPlayed, round, sL, score)
                        prevPlayed.append(word)
                        status = wordStatus(word)
                        tprint(f"{prefix}I play: {formatWord(word, status=status)}{condMsg(status == 'validated', ', a validated word!')}")
                        if status == 'validated':
                            break
                        match getResponseMenu("Is that valid?", ["[y] yes", "[n] no", "[q] quit"]):
                            case "[y] yes":
                                newData["wordsToValidate"].add(word)
                                break
                            case "[n] no":
                                newData["wordsToRemove"].add(word)
                                prefix = "Okay, then instead "
                            case "[q] quit":
                                return
                    wordScore = scoreWord(bank, sL, word)
                    if wordScore > wordScoreRecord:
                        tprint("That's a new word high score!")
                        wordScoreRecord = wordScore
                    score += wordScore
                    tprint(
                        f"{condMsg(not dictionary[word], 'Great! ')}We scored {wordScore} {condMsg(round != 0, 'additional ')}points{condMsg(round > 0, f', for a total of {score} points')}."
                        )
                    newData["wordScores"].append({"word": word, "specialLetter": sL, "score": wordScore})
                tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
                showRank(score, fast=fast)
                newData["gameScores"].append({"bank": bank.upper(), "score": score, "date": timestamp})
                updateData(newData)
                mergeData(dataToSubmit, newData)
                newData = blankData()
                bank = None