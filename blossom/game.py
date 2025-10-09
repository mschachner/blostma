import os
from datetime import datetime

from .utils import _tprint, condMsg, getResponseBy, getResponseMenu, sevenUniques
from .updater import wordHighScore, loadDict, submit, showStats, searchWords, dispWord

def scoreWord(bank, sL, word):
    baseScore = 2 * len(word) - 6 if len(word) < 7 else 3 * len(word) - 9
    specialLetterScore = 5 * word.count(sL)
    pangramScore = 7 if all(c in word for c in bank) else 0
    return baseScore + specialLetterScore + pangramScore

def advanceSL(bank, sL, lastWord=None):
    if not lastWord or sL in lastWord:
        return bank[(bank.index(sL) % 6) + 1]
    return sL

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


def playBlossom(bank=None, fast=False):
    newData = {
        "wordScoreRecord": {},
        "gameScores": [],
        "wordsToRemove": [],
        "wordsToValidate": []
    }
    timestamp = datetime.now().strftime("%Y-%m-%d")
    playAgain = True
    tprint = print if fast else _tprint
    while playAgain:
        os.system("clear")
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
        prevPlayed = []
        score = 0
        if bank:
            tprint(f"Bank: {bank.upper()}.")
            bank = bank[0] + "".join(sorted(list(bank[1:])))
        else:
            match getResponseMenu("", ["Play", "Search", "Stats", "Quit"]):
                case "Search":
                    searchWords()
                case "Stats":
                    showStats()
                case "Quit":
                    return
                case "Play":
                    match getResponseBy(
                        "What's the bank? (Center letter first)",
                        lambda b: sevenUniques(b) or b == "quit",
                        "Please enter seven unique letters, or \"quit\".",
                    ).lower():
                        case "quit":
                            return
                        case bk:
                            bank = bk[0] + "".join(sorted(list(bk)[1:]))
                    tprint("Okay, let's play!")
                    dictionary = loadDict(bank)
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
                            match getResponseMenu("Is that valid?", ["yes", "no", "quit"]):
                                case "yes":
                                    newData["wordsToValidate"].append(word)
                                    break
                                case "no":
                                    newData["wordsToRemove"].append(word)
                                    prefix = "Okay, then instead "
                                case "quit":
                                    return
                        wordScore = scoreWord(bank, sL, word)
                        if wordScore > wordHighScore["score"]:
                            tprint("That's a new word high score!")
                            newData["wordScoreRecord"] = {"word": word, "specialLetter": sL, "score": wordScore}
                        score += wordScore
                        tprint(f"{condMsg(not dictionary[word], 'Great! ')}We scored {wordScore} {condMsg(round != 0, 'additional ')}points{condMsg(round > 0, f', for a total of {score} points')}.")
                    newData["gameScores"].append({"bank": bank, "score": score, "date": timestamp})
                    bank = None
        tprint(
            f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {score} points."
        )
        while True:
            match getResponseMenu(
                "What do you want to do next?",
                ["play again", "search", "stats", "submit and quit", "quit without submitting"]
            ):
                case "play again":
                    playAgain = True
                    break
                case "search":
                    searchWords(fast=fast)
                case "stats":
                    showStats(fast=fast)
                case "submit and quit":
                    submit(newData)
                    return
                case "quit without submitting":
                    return
    return
