from args import *;import subprocess as s;from pathlib import Path;import os;import sys
if sys.platform == "win32": s.run([], shell=True)
else: pass
WhatToDoOnNoArgs("\x1b[31mNo args were given!\033[0m\nUsage: sa/sautomate <file> --Optionals")

def CheckForFilenameExists(filename: str) -> bool:
    file = Path(filename)
    if file.exists():
        return True
    else:
        print(f"{filename} was not found! Please check the correct filename")
        return False

def IsSAExec(filename: str):
    extens = ".sauto"
    file = Path(filename)
    if file.suffix.lower() == extens:
        return True
    else:
        return False

