from scipy.optimize import linear_sum_assignment

import time
import threading
import sys

from .utils import binaryStrings
from .utils import menu, condMsg


class Game:
    def __init__(self,session):
        self.session = session
        self.legalWords = list(session.blossom.wordlist.keys())
        self.bank = session.lastBank if session.lastBank else None
        self.specialLetter = None
        self.prevPlayed = []
        self.score = 0
        self.round = 0
        self.refreshed = False
        self.strategy = None

    def sortBank(self):
        self.bank = self.bank[0] + "".join(sorted(list(self.bank[1:])))
        self.specialLetter = self.bank[1]
        self.legalWords = [w for w in self.legalWords if self.bank[0] in w and all(c in self.bank for c in w)]
        return

    def advanceSL(self):
        self.specialLetter = self.bank[(self.bank.index(self.specialLetter) % 6) + 1]
        return

    def scoreWord(self, word, specialLetter=None):
        if specialLetter is None:
            specialLetter = self.specialLetter
        baseScore = 2 * len(word) - 6 if len(word) < 7 else 3 * len(word) - 9
        specialLetterScore = 5 * word.count(specialLetter)
        pangramScore = 7 if all(c in word for c in self.bank) else 0
        return baseScore + specialLetterScore + pangramScore

    def playWord(self):
        self.refreshed = False
        enginePlay= self.strategy["words"].pop(0)
        self.strategy["score"] -= enginePlay["score"]
        self.prevPlayed.append(enginePlay["word"])
        return enginePlay

    def chooseStrategy(self):
        s = self.session
        b = s.blossom

        def _gamePath(binaryString):
            petals = self.bank[1:]
            path = []
            pos = petals.index(self.specialLetter)
            for bit in binaryString:
                if bit == "0":
                    path.append((petals[pos], "any" if b.settings["allowRefresh"] else "non-advancing"))
                else:
                    path.append((petals[pos], "advancing"))
                    pos = (pos+1) % 6
            path.append((petals[pos], "any"))
            return path
        
        def _scoreMatrix(path):
            matrix = [[0 for _ in range(len(self.legalWords))] for _ in range(len(path))]
            for i in range(len(path)):
                for j in range(len(self.legalWords)):
                    w = self.legalWords[j]
                    if (any([
                        path[i][1] == "advancing" and path[i][0] not in w,
                        path[i][1] == "non-advancing" and path[i][0] in w,
                        w in self.prevPlayed,
                    ])):
                        matrix[i][j] = 0
                    else:
                        matrix[i][j] = self.scoreWord(w, specialLetter=path[i][0])
            return matrix

        def _choosePath(binaryString):
            path = _gamePath(binaryString)
            matrix = _scoreMatrix(path)
            row_indices, col_indices = linear_sum_assignment(matrix, maximize=True)
            words = []
            for i in range(len(path)):
                if path[i][1] == "any" and path[i][0] in self.legalWords[col_indices[i]] and i < len(path) - 1:
                    words.append({
                        "word": self.legalWords[col_indices[i]],
                        "score": matrix[i][col_indices[i]],
                        "refresh": True
                    })
                else:
                    words.append({
                        "word": self.legalWords[col_indices[i]],
                        "score": matrix[i][col_indices[i]],
                        "refresh": False
                    })
            return {
                "words": words,
                "score": sum(matrix[i][j] for i, j in zip(row_indices, col_indices)),
            }

        
        # Print the base message without a newline, then animate dots each second.
        b.tprint("🤔 Thinking...", end="", flush=True)
        stop_event = threading.Event()

        def _animate_dots():
            while not stop_event.is_set():
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()

        dot_thread = threading.Thread(target=_animate_dots, daemon=True)
        dot_thread.start()
        start_time = time.time()
        bestPath = {
            "words": [],
            "score": 0
        }
        for binaryString in binaryStrings(11-self.round):
            strategy = _choosePath(binaryString)
            if strategy["score"] > bestPath["score"]:
                bestPath = strategy
        end_time = time.time()
        # Stop animation and move to the next line before printing the summary.
        stop_event.set()
        dot_thread.join(timeout=0.1)
        b.tprint("")
        b.tprint(f"Thought for {end_time - start_time:.2f} seconds.")
        self.strategy = bestPath
        return

    def expectedScore(self):
        return self.score + self.strategy["score"]

    def play(self):
        s = self.session
        b = s.blossom
        if not self.bank:
            self.bank = s.lastBank if s.lastBank else s.promptForBank()
            s.lastBank = self.bank
        b.tprint("Okay, let's play!")
        b.tprint(f"Bank: {self.bank.upper()}.")
        if b.settings["allowRefresh"]:
            b.tprint("Playing with refresh exploit.")
        else:
            b.tprint("Playing without refresh exploit.")
        self.sortBank()
        self.chooseStrategy()
        wordScoreRecord = b.wordScoreRecord()
        while (self.round < 12):
            prefix = ""
            if (self.round > 0 and not self.refreshed):
                self.advanceSL()
            b.tprint(f"---\nRound {self.round+1}. Special letter: {self.specialLetter.upper()}.\n")
            while True:
                b.tprint("Expected score: ", self.expectedScore(), "points.")
                enginePlay = self.playWord()
                word = enginePlay["word"]
                status = b.wordStatus(word)
                b.tprint(f"{prefix}I play: {b.formatWord(word, status=status)}{condMsg(status == 'validated', ', a validated word!')}")
                if enginePlay["refresh"]:
                    self.refreshed = True
                    b.tprint("REFRESH!")
                if status == 'validated':
                    prefix = ""
                    break
                match menu("Is that valid?", ["[y] Yes", "[n] No", "[q] Quit game"]):
                    case "[y] Yes":
                        b.validateWord(word)
                        prefix = "Great! "
                        s.data["validated"].add(word)
                        break
                    case "[n] No":
                        b.removeWord(word)
                        s.data["removed"].add(word)
                        self.chooseStrategy()
                        prefix = "Okay, then instead "
                    case "[q] Quit game":
                        return
            if enginePlay["score"] > wordScoreRecord:
                b.tprint("That's a new word high score!")
                wordScoreRecord = enginePlay["score"]
            self.score += enginePlay["score"]
            b.tprint(
                f"{prefix}We scored {enginePlay["score"]} {condMsg(self.round != 0, 'additional ')}points{condMsg(self.round > 0, f', for a total of {self.score} points')}."
                )
            s.data["wordScores"].append({"word": word, "specialLetter": self.specialLetter, "score": enginePlay["score"]})
            b.addWordScore({"word": word, "specialLetter": self.specialLetter, "score": enginePlay["score"]})
            self.round += 1
        b.tprint(f"\n🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸\n\nGame over! We scored {self.score} points.")
        s.data["gameScores"].append({"bank": self.bank.upper(), "score": self.score})
        b.addGameScore({"bank": self.bank.upper(), "score": self.score, "date": s.timestamp})
        b.showRank(self.score)
        if b.settings["autosave"]:
            b.write()
        s.clearData()
