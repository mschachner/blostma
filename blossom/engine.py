from .utils import scoreWord, _tprint
from .updater import getSettings
from scipy.optimize import linear_sum_assignment

import time
import threading
import sys

# Engine for Blossom.

# At each round, we have two choices:
# 1. Play an `advancing` word, which contains the special letter and moves us to the next petal.
# 2. Play a `non-advancing` word, maintaining the petal, OR play an advancing word and use the refresh exploit to maintain the petal.

# Since there are 12 rounds, and we have to start on the first petal, this means that a game path is
# determined by a binary string of length 11.

# Our strategy is to look at all 2^11 = 2048 possible game paths and play each one in the best possible way.
# Then we select the path that maximizes our expected score, and play according to that path.

# Now: at some point we might try to play an invalid word. At that point we have to recalculate the best path and play according to that.

# As a warmup, let's write a function that outputs all binary strings of length N.

def binaryStrings(N):
    if N == 0:
        return [""]
    return [b + "0" for b in binaryStrings(N-1)] + [b + "1" for b in binaryStrings(N-1)]
 
# Next we need to convert a binary string and letter bank to a game path.
# To account for the case that we might be recalculating midgame, we need an argument for the current petal

def gamePath(binaryString, bank, specialLetter, settings):
    petals = bank[1:]
    path = []
    pos = petals.index(specialLetter)
    for bit in binaryString:
        if bit == "0":
            path.append((petals[pos], "any" if settings["allowRefresh"] else "non-advancing"))
        else:
            path.append((petals[pos], "advancing"))
            pos = (pos+1) % 6
    path.append((petals[pos], "any"))
    return path
        

# Now, given a game path of length N and a dictionary of size D, we need to build a matrix of size NxD that contains the score for each word in the dictionary at each position in the game path.
# Here, to account for the midgame case, we need an argument for the words played so far.

def scoreMatrix(bank, path, dictionary, prevPlayed):
    matrix = [[0 for _ in range(len(dictionary))] for _ in range(len(path))]
    for i in range(len(path)):
        for j in range(len(dictionary)):
            if (any([
                path[i][1] == "advancing" and path[i][0] not in dictionary[j],
                path[i][1] == "non-advancing" and path[i][0] in dictionary[j],
                dictionary[j] in prevPlayed,
            ])):
                matrix[i][j] = 0
            else:
                matrix[i][j] = scoreWord(bank, path[i][0], dictionary[j])
    return matrix

# Choosing a strategy now means solving the assignment problem with the score matrix.

def chooseStrategy(bank, specialLetter, binaryString, dictionary, round, prevPlayed=[]):
    settings = getSettings()
    path = gamePath(binaryString, bank, specialLetter, settings)
    matrix = scoreMatrix(bank, path, dictionary, prevPlayed)
    row_indices, col_indices = linear_sum_assignment(matrix, maximize=True)
    words = []
    for i in range(len(path)):
        if path[i][1] == "any" and path[i][0] in dictionary[col_indices[i]] and i < len(path) - 1:
            words.append({
                "word": dictionary[col_indices[i]],
                "score": matrix[i][col_indices[i]],
                "refresh": True
            })
        else:
            words.append({
                "word": dictionary[col_indices[i]],
                "score": matrix[i][col_indices[i]],
                "refresh": False
            })
    return {
        "words": words,
        "score": sum(matrix[i][j] for i, j in zip(row_indices, col_indices)),
    }

def chooseBestStrategy(bank, specialLetter, dictionary, round, prevPlayed=[]):
    settings = getSettings()
    tprint = print if settings["fast"] else _tprint
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
    bestStrategy = {
        "words": [],
        "score": 0
    }

    for binaryString in binaryStrings(11-round):
        strategy = chooseStrategy(bank, specialLetter, binaryString, dictionary, round, prevPlayed=prevPlayed)
        if strategy["score"] > bestStrategy["score"]:
            bestStrategy = strategy
    end_time = time.time()
    # Stop animation and move to the next line before printing the summary.
    stop_event.set()
    dot_thread.join(timeout=0.1)
    print()
    tprint(f"Thought for {end_time - start_time:.2f} seconds.")
    return bestStrategy
