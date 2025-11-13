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

def formatWordScorePure(wordScore, style="terminal"):
    return formatWordPure(wordScore["word"], status="validated", style=style) + f", {wordScore["specialLetter"].upper()}, {wordScore["score"]} points"

def formatSettings():
    # TODO
    return

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