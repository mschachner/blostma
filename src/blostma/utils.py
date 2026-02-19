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