import os
from datetime import datetime

from .utils import _tprint, condMsg, getResponseBy, getResponseMenu, sevenUniques, pending, scoreWord, advanceSL, blankData, mergeData, selectMultiple
from .updater import updateData, showStats, searchWords, showRank, updateSettings, pushData, getDictionary, formatWord, wordStatus, getWordScores, getSettings

from .engine import chooseBestStrategy

def blossomSearch(queries, dataToSubmit):
    settings = getSettings()
    tprint = print if settings["fast"] else _tprint
    dataToUpdate = blankData()
    if not queries:
        queries = getResponseBy(
            "Enter words to search (comma or space separated):",
            lambda w: True,
            None,
            fast=settings["fast"]
            )
        queries = [w.strip() for w in queries.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    if not queries:
        tprint("Fine, don't search anything then. 🙄")
        return
    searchWords(queries=queries)
    match getResponseMenu(
        "Any changes?",
        ["[v] validate all", "[r] remove all", "[s] select words", "[d] done"]
        , fast=settings["fast"]
        ):
        case "[v] validate all":
            dataToUpdate["wordsToValidate"] = queries
        case "[r] remove all":
            dataToUpdate["wordsToRemove"] = queries
        case "[s] select words":
            words = selectMultiple("Which words?", queries, fast=settings["fast"])
            match getResponseMenu(
                "What would you like to do?",
                ["[v] validate", "[r] remove", "[d] done"]
                , fast=settings["fast"]
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

def playBlossom(bank=None, choice=None, queries=None):
    os.system("clear")
    dataToSubmit = blankData()
    settings = getSettings()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    menued = False
    played = False
    tprint = print if settings["fast"] else _tprint
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
        settings = getSettings()
        if not choice:
            msg = "What do you want to do?" if not menued else "What do you want to do next?"
            choices = ["search", "stats", "settings", "quit"]
            if pending(dataToSubmit):
                choices.insert(2, "submit data")
            if not played:
                choices = ["play", *choices]
            else:
                choices = ["play again", "play with new bank", *choices]
            choice = getResponseMenu(msg, choices, fast=settings["fast"])
        match choice:
            case "search":
                choice, menued = None, True
                blossomSearch(queries, dataToSubmit)
                queries = None
            case "stats":
                choice, menued = None, True
                showStats()
                continue
            case "settings":
                choice, menued = None, True
                updateSettings()
                continue
            case "submit data":
                choice, menued = None, True
                pushData(dataToSubmit, verifyFirst=True)
                dataToSubmit = blankData()
                continue
            case "quit":
                if pending(dataToSubmit) and getResponseMenu(
                    "Submit all data first?", ["[s] submit data", "[q] quit without submitting"]
                    , fast=settings["fast"]
                    ) == "[s] submit data":
                    pushData(dataToSubmit, verifyFirst=False)
                tprint("Quitting.")
                return
            case "play" | "play again" | "play with new bank":
                menued, played, refreshed = True, True, False
                if choice == "play again":
                    bank = lastBank
                else:
                    match getResponseBy(
                        "What's the bank? (Center letter first)",
                        lambda b: sevenUniques(b) or b == "quit",
                        "Please enter seven unique letters, or \"quit\".",
                        firstChoice = bank,
                        fast=settings["fast"]
                    ).lower():
                        case "quit":
                            return
                        case bk:
                            bank = bk
                choice = None
                tprint("Okay, let's play!")
                tprint(f"Bank: {bank.upper()}.")
                if settings["allowRefresh"]:
                    tprint("Playing with refresh exploit.")
                else:
                    tprint("Playing without refresh exploit.")
                bank = bank[0] + "".join(sorted(list(bank[1:])))
                dictionary = getDictionary(bank)
                wordScoreRecord = max(getWordScores(), key=lambda x: x["score"])["score"]
                newData = blankData()
                sL = bank[1]
                prevPlayed = []
                score = 0
                engineStrategy = chooseBestStrategy(bank, sL, list(dictionary.keys()), 0, prevPlayed=prevPlayed)
                enginePlays = engineStrategy["words"]
                expectedTailScore = engineStrategy["score"]
                for round in range(12):
                    prefix = ""
                    if (round > 0 and not refreshed):
                        sL = advanceSL(bank, sL, prevPlayed[-1])
                    refreshed = False
                    tprint(f"---\nRound {round+1}. Special letter: {sL.upper()}.\n")
                    while True:
                        print("Expected score: ", score + expectedTailScore, "points.")
                        enginePlay = enginePlays.pop(0)
                        word = enginePlay["word"]
                        expectedTailScore -= enginePlay["score"]
                        prevPlayed.append(word)
                        status = wordStatus(word)
                        tprint(f"{prefix}I play: {formatWord(word, status=status)}{condMsg(status == 'validated', ', a validated word!')}")
                        if enginePlay["refresh"]:
                            refreshed = True
                            tprint("REFRESH!")
                        if status == 'validated':
                            break
                        match getResponseMenu("Is that valid?", ["[y] yes", "[n] no", "[q] quit"], fast=settings["fast"]):
                            case "[y] yes":
                                newData["wordsToValidate"].add(word)
                                break
                            case "[n] no":
                                engineStrategy = chooseBestStrategy(bank, sL, list(dictionary.keys()), round, prevPlayed=prevPlayed)
                                enginePlays = engineStrategy["words"]
                                expectedTailScore = engineStrategy["score"]
                                newData["wordsToRemove"].add(word)
                                prefix = "Okay, then instead "
                            case "[q] quit":
                                return
                    if enginePlay["score"] > wordScoreRecord:
                        tprint("That's a new word high score!")
                        wordScoreRecord = enginePlay["score"]
                    score += enginePlay["score"]
                    tprint(
                        f"{condMsg(not dictionary[word], 'Great! ')}We scored {enginePlay["score"]} {condMsg(round != 0, 'additional ')}points{condMsg(round > 0, f', for a total of {score} points')}."
                        )
                    newData["wordScores"].append({"word": word, "specialLetter": sL, "score": enginePlay["score"]})
                tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points.")
                newData["gameScores"].append({"bank": bank.upper(), "score": score, "date": timestamp})
                updateData(newData)
                mergeData(dataToSubmit, newData)
                showRank(score)
                newData = blankData()
                lastBank = bank
                bank = None