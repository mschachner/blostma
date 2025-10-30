import os
from datetime import datetime

from .utils import _tprint, condMsg, getResponseBy, getResponseMenu, sevenUniques, pending, scoreWord, advanceSL, blankData, mergeInto
from .updater import wordHighScore, settings, loadDict, updateData, showStats, searchWords, dispWord, showRank, setSettings, pushData

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
                choice = None
                menued = True
                newWordsToValidate, newWordsToRemove = searchWords(queries=queries)
                if newWordsToValidate or newWordsToRemove:
                    d = {
                        "wordsToValidate": newWordsToValidate,
                        "wordsToRemove": newWordsToRemove,
                        "gameScores": None,
                        "wordScoreRecord": None,
                    }
                    updateData(d, fast=fast)
                    mergeInto(dataToSubmit, d)
                continue
            case "stats":
                choice = None
                menued = True
                showStats(fast=fast, topCount=settings["numScores"])
                continue
            case "settings":
                choice = None
                menued = True
                setSettings(fast=fast)
                continue
            case "submit data":
                choice = None
                menued = True
                pushData(dataToSubmit)
                dataToSubmit = blankData()
                continue
            case "quit":
                if pending(dataToSubmit) and getResponseMenu(
                    "Submit data first?", ["[s] submit data", "[q] quit without submitting"]
                    ) == "[s] submit data":
                    pushData(dataToSubmit)
                    dataToSubmit = blankData()
                tprint("Quitting.")
                return
        # Otherwise, it's game on
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
        dictionary = loadDict(bank)
        newData = blankData()
        for round in range(12):
            prefix = ""
            sL = advanceSL(bank, sL, prevPlayed[-1]) if round > 0 else bank[1]
            tprint(f"---\nRound {round+1}. Special letter: {sL.upper()}.\n")
            while True:
                word = blossomBetter(bank, dictionary, prevPlayed, round, sL, score)
                prevPlayed.append(word)
                tprint(f"{prefix}I play: {dispWord(word)}{condMsg(dictionary[word], ', a validated word!')}")
                if dictionary[word]:
                    break
                match getResponseMenu("Is that valid?", ["[y] yes", "[n] no", "[q] quit"]):
                    case "[y] yes":
                        newData["wordsToValidate"].append(word)
                        break
                    case "[n] no":
                        newData["wordsToRemove"].append(word)
                        prefix = "Okay, then instead "
                    case "[q] quit":
                        return
            wordScore = scoreWord(bank, sL, word)
            if wordScore > wordHighScore["score"]:
                tprint("That's a new word high score!")
                newData["wordScoreRecord"] = {"word": word, "specialLetter": sL, "score": wordScore}
            score += wordScore
            tprint(
                f"{condMsg(not dictionary[word], 'Great! ')}We scored {wordScore} {condMsg(round != 0, 'additional ')}points{condMsg(round > 0, f', for a total of {score} points')}."
                )
        newData["gameScores"].append({"bank": bank, "score": score, "date": timestamp})
        bank = None
        tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
        showRank(score)
        updateData(newData, fast=fast)
        mergeInto(dataToSubmit, newData)
        newData = blankData()