import os
from datetime import datetime

from .utils import condMsg, getResponseBy, getResponseMenu, sevenUniques, selectMultiple
from .updater import Blossom, Session, pushDataFiles
from .format import _tprint
from .engine import Game


def blossomSearch(queries, blossom, session):

    if not queries: # User can provide queries as an argument
        queries = getResponseBy(
            "Enter words to search (comma or space separated):",
            lambda w: True, # Always pass...
            None,           # ... so no need for a retry message.
            fast=blossom.settings["fast"]
            )
        queries = [w.strip() for w in queries.replace(',', ' ').split() if w.strip()]
    queries = set(queries)
    if not queries:
        print("Fine, don't search anything then. 🙄")
        return
    # searchWords does the interacting with data files
    blossom.searchWords(queries=queries)
    match getResponseMenu(
        "Any changes?",
        ["[v] validate all", "[r] remove all", "[s] select words", "[d] done"]
        , fast=blossom.settings["fast"]
        ):
        case "[v] validate all":
            session.data["wordsToValidate"] = queries
        case "[r] remove all":
            session.data["wordsToRemove"] = queries
        case "[s] select words":
            words = selectMultiple("Which words?", queries, fast=blossom.settings["fast"])
            match getResponseMenu(
                "What would you like to do?",
                ["[v] validate", "[r] remove", "[d] done"]
                , fast=blossom.settings["fast"]
                ):
                case "[v] validate":
                    session.data["wordsToValidate"] = set(words)
                case "[r] remove":
                    session.data["wordsToRemove"] = set(queries) - set(words)
                case "[d] done":
                    return
    blossom.updateDataFromSession(session) # Add the new data to the data files
    return

def playBlossom(bk=None, choice=None, queries=None):
    blossom = Blossom()
    session = Session()
    os.system("clear")
    tprint = print if blossom.settings["fast"] else _tprint
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
            msg = "What do you want to do?" if not session.menued else "What do you want to do next?"
            choices = ["Search for words", "Stats", "Settings", "Quit"]
            if session.pending():
                choices.insert(2, "submit data")
            if not session.played:
                choices = ["Play", *choices]
            else:
                choices = ["Play again", "Play with new bank", *choices]
            choice = getResponseMenu(msg, choices, fast=blossom.settings["fast"])
        match choice:
            case "Search":
                choice= None
                session.menued = True
                blossomSearch(queries, blossom, session)
                queries = None
                continue
            case "Stats":
                choice = None
                session.menued = True
                blossom.showStats()
                continue
            case "Settings":
                choice = None
                session.menued = True
                blossom.updateSettings()
                continue
            case "Submit data":
                choice = None
                session.menued = True
                pushDataFiles(blossom, session, verifyFirst=True)
                session.clearData()
                continue
            case "Quit":
                if session.pending() and getResponseMenu(
                    "Submit all data first?", ["[s] Submit data", "[q] Quit without submitting"]
                    , fast=blossom.settings["fast"]
                    ) == "[s] Submit data":
                    pushDataFiles(blossom, session, verifyFirst=False)
                tprint("Quitting.")
                return
            case "Play" | "Play again" | "Play with new bank":
                session.menued = True
                session.played = True
                game = Game(blossom, session, bk)
                if choice == "play again":
                    game.bank = session.lastBank
                else:
                    match getResponseBy(
                        "What's the bank? (Center letter first)",
                        lambda b: sevenUniques(b) or b == "quit",
                        "Please enter seven unique letters, or \"quit\".",
                        firstChoice = bk,
                        fast=blossom.settings["fast"]
                    ).lower():
                        case "quit":
                            return
                        case userEnteredBank:
                            game.bank = userEnteredBank
                choice = None
                session.lastBank = game.bank
                tprint("Okay, let's play!")
                tprint(f"Bank: {game.bank.upper()}.")
                if blossom.settings["allowRefresh"]:
                    tprint("Playing with refresh exploit.")
                else:
                    tprint("Playing without refresh exploit.")
                game.sortBank()
                game.chooseStrategy()
                wordScoreRecord = blossom.wordScoreRecord()
                while (game.round < 12):
                    prefix = ""
                    if (game.round > 0 and not game.refreshed):
                        game.advanceSL()
                    tprint(f"---\nRound {game.round+1}. Special letter: {game.specialLetter.upper()}.\n")
                    while True:
                        tprint("Expected score: ", game.expectedScore(), "points.")
                        enginePlay = game.playWord()
                        word = enginePlay["word"]
                        status = blossom.wordStatus(word)
                        tprint(f"{prefix}I play: {blossom.formatWord(word, status=status)}{condMsg(status == 'validated', ', a validated word!')}")
                        if enginePlay["refresh"]:
                            game.refreshed = True
                            tprint("REFRESH!")
                        if status == 'validated':
                            break
                        match getResponseMenu("Is that valid?", ["[y] Yes", "[n] No", "[q] Quit game"], fast=blossom.settings["fast"]):
                            case "[y] Yes":
                                session.data["wordsToValidate"].add(word)
                                break
                            case "[n] No":
                                game.chooseStrategy()
                                session.data["wordsToRemove"].add(word)
                                prefix = "Okay, then instead "
                            case "[q] Quit game":
                                return
                    if enginePlay["score"] > wordScoreRecord:
                        tprint("That's a new word high score!")
                        wordScoreRecord = enginePlay["score"]
                    game.score += enginePlay["score"]
                    tprint(
                        f"{condMsg(not blossom.wordlist[word], 'Great! ')}We scored {enginePlay["score"]} {condMsg(game.round != 0, 'additional ')}points{condMsg(game.round > 0, f', for a total of {game.score} points')}."
                        )
                    blossom.addWordScores([{"word": word, "specialLetter": game.specialLetter, "score": enginePlay["score"]}])
                    game.round += 1
                tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {game.score} points.")
                blossom.addGameScores(
                    [{"bank": game.bank.upper(), "score": game.score}]
                    )
                blossom.showRank(game.score)
                session.clearData()