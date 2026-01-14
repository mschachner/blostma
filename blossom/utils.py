import simple_term_menu

from .format import _tprint

def getResponseBy(msg, cond, invalidMsg, firstChoice = None, fast = False):
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

def getResponse(msg, valids, fast = False):
    return getResponseBy(msg, lambda r: r in valids, f"Valid responses: {', '.join(valids)}.", fast=fast)

def getResponseMenu(msg, options, fast = False):
    menu = simple_term_menu.TerminalMenu(
        options,
        title=msg, 
        menu_cursor_style=(("fg_purple", "bold")), 
        menu_cursor="🌸 > ",
        quit_keys=[]
    )
    return options[menu.show()]

def selectMultiple(msg, options, fast = False):
    menu = simple_term_menu.TerminalMenu(
        options,
        title=msg,
        menu_cursor_style=(("fg_purple", "bold")),
        menu_cursor="🌸 > ",
        multi_select=True,
        multi_select_cursor_brackets_style=(("fg_gray", "bold")),
        multi_select_cursor="[🌸] ",
        quit_keys=[]
    )
    return [list(options)[i] for i in menu.show()]

def selectMultipleMD(msg, options):
    choices = selectMultiple(msg, [option["name"] for option in options.values()])
    return {k: v for k, v in options.items() if k in choices}

def sevenUniques(s):
    return len(s) == 7 and len(set(s)) == 7 and s.isalpha()

def condMsg(cond, msg, elseMsg=""):
    return msg if cond else elseMsg

def plural(l):
    return condMsg(len(l) != 1, "s")

def blankData():
    return {
        "wordScores": [],
        "gameScores": [],
        "wordsToRemove": set(),
        "wordsToValidate": set()
    }

def pending(data):
    return any(v for v in data.values())

def mergeData(data1, data2, prefer = "remove"):
    if data2["wordScores"]:
        data1["wordScores"].extend(data2["wordScores"])
    data1["gameScores"].extend(data2["gameScores"])
    data1["wordsToRemove"].update(data2["wordsToRemove"])
    data1["wordsToValidate"].update(data2["wordsToValidate"])
    # Fix data1 to not contain words that are both to validate and to remove.
    if prefer == "remove":
        data1["wordsToValidate"] -= data1["wordsToRemove"]
    elif prefer == "validate":
        data1["wordsToRemove"] -= data1["wordsToValidate"]
    return data1