from args import *
from filehandle import *
import os
import sys
import subprocess as s
from pathlib import Path

class BadOperationError(Exception):
    def __init__(self, message="SoulAutomate is having problems with working with file!"):
        super().__init__(f"BadOperationError: {message}")

class Operations:
    args = sys.argv[1:]
    filename = args[0] if args else None
    fileexists = CheckForFilenameExists(filename) if filename else False

    SpecialKeywords = [
        "DETAILED",
        "NEWSESSION",
        "ignore",
        "github-release",
        "get-latest",
        "get-usage"
    ]

    @staticmethod
    def CheckForSpecialKeywords():
        found = []
        try:
            with open(Operations.filename, 'r') as f:
                DataList = f.read().splitlines()
                for i, line in enumerate(DataList):
                    for keyword in Operations.SpecialKeywords:
                        if line.strip().startswith(keyword):
                            found.append((i + 1, keyword, line.strip()))
            return found
        except FileNotFoundError:
            raise BadOperationError(f"{Operations.filename} was not found")
        except PermissionError:
            raise BadOperationError(f"{Operations.filename} could not be read, permission denied")

