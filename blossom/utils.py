import sys
import time
import simple_term_menu

STYLES = {
    "reset": "\033[0m",
    "boldred": "\033[1;31m",
    "boldgreen": "\033[1;32m",
    "boldyellow": "\033[1;33m",
    "boldpink": "\033[1;35m",
}

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

def getResponseBy(msg, cond, invalidMsg, firstChoice = None, fast=False):
    tprint = print if fast else _tprint
    if firstChoice:
        if cond(firstChoice):
            return firstChoice
        else:
            tprint(invalidMsg)
    while True:
        attempt = input(msg + "\n > ")
        if cond(attempt):
            return attempt
        tprint(invalidMsg)

def getResponse(msg, valids):
    return getResponseBy(msg, lambda r: r in valids, f"Valid responses: {', '.join(valids)}.")

def getResponseMenu(msg, options):
    menu = simple_term_menu.TerminalMenu(options, title=msg, menu_cursor_style=(("fg_purple", "bold")), menu_cursor="🌸 > ")
    return options[menu.show()]

def selectMultiple(msg, options):
    menu = simple_term_menu.TerminalMenu(
        options,
        title=msg,
        menu_cursor_style=(("fg_purple", "bold")),
        menu_cursor="🌸 > ",
        multi_select=True,
        multi_select_cursor_brackets_style=(("fg_gray", "bold")),
        multi_select_cursor="[🌸] ",
    )
    return [list(options)[i] for i in menu.show()]

def selectMultipleMD(msg, options):
    choices = selectMultiple(msg, [option["name"] for option in options.values()])
    return {k: v for k, v in options.items() if k in choices}

def sevenUniques(s):
    return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

def scoreWord(bank, sL, word):
    baseScore = 2 * len(word) - 6 if len(word) < 7 else 3 * len(word) - 9
    specialLetterScore = 5 * word.count(sL)
    pangramScore = 7 if all(c in word for c in bank) else 0
    return baseScore + specialLetterScore + pangramScore

def advanceSL(bank, sL, lastWord=None):
    if not lastWord or sL in lastWord:
        return bank[(bank.index(sL) % 6) + 1]
    return sL

def condMsg(cond, msg, elseMsg=""):
    return msg if cond else elseMsg

def plural(l):
    return condMsg(len(l) != 1, "s")

def colorBold(color, text):
    return f"{STYLES['bold' + color]}{text}{STYLES['reset']}"

def formatSettings():
    # TODO
    return

def blankData():
    return {
        "wordScores": [],
        "gameScores": [],
        "wordsToRemove": set(),
        "wordsToValidate": set()
    }

def fixData(data, prefer = "remove"):
    if prefer == "remove":
        data["wordsToValidate"] -= data["wordsToRemove"]
    elif prefer == "validate":
        data["wordsToRemove"] -= data["wordsToValidate"]
    return data

def pending(data):
    return any(v for v in data.values())

def mergeData(data1, data2):
    if data2["wordScores"]:
        data1["wordScores"].extend(data2["wordScores"])
    data1["gameScores"].extend(data2["gameScores"])
    data1["wordsToRemove"].update(data2["wordsToRemove"])
    data1["wordsToValidate"].update(data2["wordsToValidate"])
    fixData(data1)
    return