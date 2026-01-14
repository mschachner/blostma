from scipy.optimize import linear_sum_assignment

import time
import threading
import sys

from .format import _tprint

# Engine for Blossom.

# At each round, we have two choices:
# 1. Play an `advancing` word, which contains the special letter and moves us to the next petal.
# 2. Play a `non-advancing` word, maintaining the petal, OR play an advancing word and use the refresh exploit to maintain the petal.

# Since there are 12 rounds, and we have to start on the first petal, this means that a game path is
# determined by a binary string of length 11.

# Our strategy is to look at all 2^11 = 2048 possible game paths and play each one in the best possible way.
# Then we select the path that maximizes our expected score, and play according to that path.

# Now: at some point we might try to play an invalid word. At that point we have to recalculate the best path and play according to that.


def binaryStrings(N):
    if N == 0:
        return [""]
    return [b + "0" for b in binaryStrings(N-1)] + [b + "1" for b in binaryStrings(N-1)]
 

class Game:
    def __init__(self,blossom,session,bank=None):
        self.settings = blossom.settings
        self.legalWords = list(blossom.wordlist.keys())
        self.session = session
        self.bank = bank
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

    def scoreWord(self, word):
        baseScore = 2 * len(word) - 6 if len(word) < 7 else 3 * len(word) - 9
        specialLetterScore = 5 * word.count(self.specialLetter)
        pangramScore = 7 if all(c in word for c in self.bank) else 0
        return baseScore + specialLetterScore + pangramScore

    def playWord(self):
        self.refreshed = False
        enginePlay = self.strategy["words"].pop(0)
        self.prevPlayed.append(enginePlay["word"])
        return enginePlay

    
    def chooseStrategy(self):

        def _gamePath(binaryString):
            petals = self.bank[1:]
            path = []
            pos = petals.index(self.specialLetter)
            for bit in binaryString:
                if bit == "0":
                    path.append((petals[pos], "any" if self.settings["allowRefresh"] else "non-advancing"))
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
                        matrix[i][j] = self.scoreWord(w)
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

        
        tprint = _tprint if self.settings["fast"] else print
        # Print the base message without a newline, then animate dots each second.
        tprint("🤔 Thinking...", end="", flush=True)
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
        tprint("")
        tprint(f"Thought for {end_time - start_time:.2f} seconds.")
        self.strategy = bestPath
        return

    def expectedScore(self):
        return self.score + self.strategy["score"]
