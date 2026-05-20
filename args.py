# SAutomate args.py -> Argument helpers
import sys

KnownFlags = ["-c", "--hash"]

def CheckForUnknownFlags(argv: list):
    for arg in argv:
        if arg.startswith("-"):
            found = False
            for flag in KnownFlags:
                if arg.lower() == flag.lower():
                    found = True
                    break
            if not found:
                return arg
    return None

def WhatToDoOnNoArgs(string: str):
    if len(sys.argv) < 2:
        print(string)
        return True
    return False

def CheckArgMeets(string: str, whereat: int):
    try:
        return sys.argv[whereat] == string
    except IndexError:
        return False

def CheckArgMeetsMulti(listofargs: list):
    for arg in listofargs:
        if arg in sys.argv:
            return arg
    return False

def CheckInCaseSens(string: str, whereat: int):
    try:
        return string.lower() == sys.argv[whereat].lower()
    except IndexError:
        return False

def FindFlag(flag: str):
    flag_lower = flag.lower()
    for i, arg in enumerate(sys.argv):
        if arg.lower() == flag_lower:
            return i
    return -1

def GetFlagValue(flag: str):
    idx = FindFlag(flag)
    if idx == -1:
        return None
    try:
        return sys.argv[idx + 1]
    except IndexError:
        return None

def GetFlagValues(flag: str):
    idx = FindFlag(flag)
    if idx == -1:
        return []
    values = []
    for arg in sys.argv[idx + 1:]:
        if arg.startswith("--") or arg.startswith("-"):
            break
        values.append(arg)
    return values