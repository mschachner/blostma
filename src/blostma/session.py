import subprocess
from datetime import datetime
import os

from .utils import menu, sevenUniques
from .game import Game
from .format import formatGameScore, formatWordScores


BLOSSOM_LOGO = r"""
,-----.  ,--.
|  |) /_ |  | ,---.  ,---.  ,---.  ,---. ,--,--,--.
|  .-.  \|  || .-. |(  .-' (  .-' | .-. ||        |
|  '--' /|  |' '-' '.-'  `).-'  `)' '-' '|  |  |  |
`------' `--' `---' `----' `----'  `---' `--`--`--'
🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸
            """

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

    def pending(self):
        return any(self.data[key] for key in self.data)
    
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
        msg = "What do you want to do?" if not self.menued else "What do you want to do next?"
        self.menued = True
        choices = ["Search for words", "Stats", "Settings", "Quit"]
        if self.pending():
            choices.insert(2, "Save data")
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
            case "Save data":
                self.mode = "save"
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
                if self.pending():
                    match menu("Save data before quitting?", ["[y] yes", "[n] no"]):
                        case "[y] yes":
                            self.save()
                            return
                        case "[n] no":
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
        )
        self.queries = response.split(",") if "," in response else response.split(" ")


    def save(self):
        match menu("Save locally or push to GitHub?", ["[l] local", "[g] GitHub", "[c] cancel"]):
            case "[l] local":
                self.blossom.write()
            case "[g] GitHub":
                self.blossom.write()
                self.pushToGitHub()
            case "[c] cancel":
                print("Data not saved.")
                return
        return

    def pushToGitHub(self):
        summary = f"auto: submitted at {self.timestamp}"
        body = self.formatData("git")
        self.blossom.write()

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
