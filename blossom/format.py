import sys
import time

# ========================== Constants ==========================

STYLES = {
    "reset": "\033[0m",
    "boldred": "\033[1;31m",
    "boldgreen": "\033[1;32m",
    "boldyellow": "\033[1;33m",
    "boldpink": "\033[1;35m",
}

def colorBold(color, text):
    return f"{STYLES['bold' + color]}{text}{STYLES['reset']}"

# ========================== Pure formatting functions ==========================

def formatGameScore(gameScore, style="terminal"):
    match style:
        case "terminal":
            specialLetter = colorBold("yellow", gameScore["bank"][0].upper())
            restOfBank = colorBold("pink", gameScore["bank"][1:].upper())
            return f"{specialLetter + restOfBank} | {gameScore["score"]} points, {gameScore["date"]}"
        case "git":
            return f"{gameScore["bank"].upper()} | {gameScore["score"]} points, {gameScore["date"]}"
        case _:
            raise ValueError(f"Invalid style: {style}")

def formatWordPure(word, status, style="terminal", padding=0):
    match status:
        case "not found":
            color = "red"
            icon = "❌ "
            status = f": {padding * ' '}Not found"
        case "present, not validated":
            color = "yellow"
            icon = "🟡 "
            status = f": {padding * ' '}Present, not validated"
        case "validated":
            color = "green"
            icon = "🌸 " if len(set(word)) == 7 else "✅ "
            status = f": {padding * ' '}Validated"
    match style:
        case "git":
            return icon + word.upper()
        case "terminal":
            return icon + colorBold(color, word.upper())
        case "search":
            return icon + colorBold(color, word.upper()) + status

def formatWordScorePure(wordScore, style="terminal", status="validated", padding=0):
    pad = " " * (max(len(wordScore["word"]), padding) - len(wordScore["word"]))
    return formatWordPure(wordScore["word"], status, style=style) + f", {pad}{wordScore["specialLetter"].upper()}, {wordScore["score"]} points"

def formatWordScores(wordScores, style="terminal"):
    scores = ""
    padding = max(len(wordScore["word"]) for wordScore in wordScores) if style == "terminal" else 0
    for wordScore in wordScores:
        scores += f"{formatWordScorePure(wordScore, style=style, padding=padding)}\n"
    return scores.rstrip()

def formatSettings():
    # TODO
    return

def formatStatsGameScore(gameScores, topCount=10, bottomCount=1, showMedian=True):
    stats = ""
    numScores = len(gameScores)
    medianIndex = 1 + numScores//2
    for index in range(1, numScores + 1):
        pad = " " * (4 - len(str(index)))
        paddedIndex = f"{index}.{pad}"
        formattedScore = formatGameScore(gameScores[index-1])
        if index == medianIndex and showMedian:
            note = " (median)"
        elif index == numScores:
            note = " (lowest)"
        else:
            note = ""
        if any([index <= topCount, index > numScores - bottomCount, (showMedian and index == medianIndex)]):
            stats += f"{paddedIndex}{formattedScore}{note}\n"
        elif index == topCount + 1 or (showMedian and index == medianIndex + 1):
            stats += "⋮\n"
    return stats.rstrip()

# ========================== Printing functions ==========================

def _tprint(*objects, sep=" ", end="\n", file=sys.stdout, flush=False):
    text = sep.join(map(str, objects)) + end

    # If not an interactive terminal, print fast.
    if not getattr(file, "isatty", lambda: False)():
        file.write(text)
        if flush:
            file.flush()
        return

    # Tuned speeds
    cps = 150  # characters per second
    punct_pause = 0.10  # pause after . ! ?
    mid_pause = 0.10  # pause after , ; : – —
    base = 1.0 / cps

    for ch in text:
        file.write(ch)
        file.flush()
        if ch in ".!?":
            time.sleep(punct_pause)
        elif ch in ",;:–—":
            time.sleep(mid_pause)
        else:
            time.sleep(base)