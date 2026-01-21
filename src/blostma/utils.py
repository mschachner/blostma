import simple_term_menu

def menu(msg, options):
    m = simple_term_menu.TerminalMenu(
        options,
        title=msg, 
        menu_cursor_style=(("fg_purple", "bold")), 
        menu_cursor="🌸 > ",
        quit_keys=[]
    )
    return options[m.show()]

def selectMultiple(msg, options):
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

def binaryStrings(N):
    if N == 0:
        return [""]
    return [b + "0" for b in binaryStrings(N-1)] + [b + "1" for b in binaryStrings(N-1)]
 

def blankData():
    return {
        "wordScores": [],
        "gameScores": [],
        "wordsToRemove": set(),
        "wordsToValidate": set()
    }

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