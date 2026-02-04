import subprocess
from datetime import datetime
import os

from .utils import menu, sevenUniques
from .game import Game
from .format import formatGameScore, formatWordScores, colorBold


BLOSSOM_LOGO = f"""
                                              
 ▄▄▄▄    ▄▄                                  
█🌸▀▀█▄  ██                ██                  
██▄▄██▀ 🌸█  ▄███▄ ▄█🌸▀▀ ▀██▀  █🌸█▄███▄   ▀▀█▄ 
██  🌸█▄ ██  ██🌸█ ▀███▄   ██    ██ ██ 🌸█ ▄█▀██ 
▀█████▀  ██  ▀███▀ ▄▄▄🌸   ██🌸  ██ ██  ██ ▀█🌸█
🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃🍃
{colorBold("pink", "A command-line companion for Merriam-Webster's Blossom")}"""

# The Session class holds all information that persists between games but not between sessions.

class Session:
    def __init__(self,blossom):
        self.blossom = blossom
        self.timestamp = datetime.now().strftime("%Y-%m-%d")
        self.data = {
            "wordScores": [],
            "gameScores": [],
            "removed": set(),
            "validated": set()
        }
        self.mode = "menu"
        self.queries = None
        self.menued = False # Whether the user has been to the main menu before this session.
        self.played = False # Whether the user has played a game this session.
        self.refreshed = False # Whether the user has just used the refresh exploit.
        self.lastBank = None # The bank of the last game played.

    def clearData(self):
        self.data = {
            "wordScores": [],
            "gameScores": [],
            "removed": set(),
            "validated": set()
        }
        return

    def formatData(self):
        body = ""
        if self.data["gameScores"]:
            body += "Game scores:\n" + "\n".join(formatGameScore(sc).rstrip() for sc in self.data["gameScores"]) + "\n"
        if self.data["wordScores"]:
            body += "Word scores:\n" + formatWordScores(self.data["wordScores"]) + "\n"
        if self.data["validated"]:
            body += "Validated words:\n"
            body += "\n".join(self.blossom.formatWord(word, status="validated").rstrip() for word in self.data["validated"]) + "\n"
        if self.data["removed"]:
            body += "Removed words:\n"
            body += "\n".join(self.blossom.formatWord(word).rstrip() for word in self.data["removed"])
        return body

    def mainMenu(self): 
        msg = "" if not self.menued else "What do you want to do next?"
        self.menued = True
        choices = ["Search for words", "Stats", "Settings", "Quit"]
        if not self.played:
            choices = ["Play", *choices]
        else:
            choices = ["Play again", "Play with new bank", *choices]
        match menu(msg, choices):
            case "Search for words":
                self.mode = "search"
                return
            case "Stats":
                self.mode = "stats"
                return
            case "Settings":
                self.mode = "settings"
                return
            case "Play" | "play" | "Play with new bank":
                self.played = True
                self.mode = "play"
                self.lastBank = None
                return
            case "Play again":
                self.played = True
                self.mode = "play"
                return
            case "Quit":
                self.mode = "quit"
                self.blossom.write()
                return

    
    def promptForBank(self):
        return self.blossom.getResponseBy(
            "What's the bank? (Center letter first)",
            lambda bk: sevenUniques(bk),
            "Please enter seven unique letters.",
            default = self.lastBank
        )

    def promptForQueries(self):
        response = self.blossom.getResponseBy(
            "Enter words to search (comma or space separated):",
            lambda w: True, # Always pass...
            None,           # ... so no need for a retry message.
        ).strip()
        self.queries = response.split(",") if "," in response else response.split(" ")
        self.queries = [q for q in self.queries if q]


    def run(self):
        os.system("clear")
        b = self.blossom
        print(BLOSSOM_LOGO)
        while True:
            match self.mode:
                case "quit":
                    return
                case "menu":
                    self.mainMenu()
                    continue
                case "search":
                    self.mode = "menu"
                    if not self.queries:
                        self.promptForQueries()
                    b.search(self)
                    continue
                case "stats":
                    self.mode = "menu"
                    b.showStats()
                    continue
                case "settings":
                    self.mode = "menu"
                    b.updateSettings()
                    continue
                case "save":
                    self.mode = "menu"
                    self.save()
                    self.clearData()
                    continue
                case "play":
                    self.mode = "menu"
                    Game(self).play()
                    continue
