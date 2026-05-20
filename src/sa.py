from args import *
from filehandle import *
from parser import SAParser
from executor import SAExecutor
from logger import SetHashValues, BadSystemOperation
import sys

class WrongSAutoArgument(Exception):
    def __init__(self, message):
        super().__init__(f"WrongSAutoArgument: {message}")

if WhatToDoOnNoArgs("\x1b[31mNo args were given!\033[0m\nUsage: sa/sautomate <file> --Optionals"):
    sys.exit(1)

unknown = CheckForUnknownFlags(sys.argv[1:])
if unknown:
    raise WrongSAutoArgument(f'"{unknown}" is not a recognized sa argument')

hash_values = GetFlagValues("--hash")
if hash_values:
    SetHashValues(hash_values)

if FindFlag("-c") != -1:
    inline = GetFlagValue("-c")
    if not inline:
        raise WrongSAutoArgument("-c was given but no command followed")
    file_given = sys.argv[1] if not CheckInCaseSens("-c", 1) else None
    if file_given:
        if not CheckForFilenameExists(file_given):
            sys.exit(1)
        if not IsSAExec(file_given):
            raise WrongSAutoArgument(f"{file_given} is not a .sauto file")
        parser = SAParser(file_given).parse()
        executor = SAExecutor(parser)
        executor.run()
        executor.run_inline(inline)
    else:
        executor = SAExecutor(None)
        executor.run_inline(inline)
else:
    filename = sys.argv[1]
    if not CheckForFilenameExists(filename):
        sys.exit(1)
    if not IsSAExec(filename):
        raise WrongSAutoArgument(f"{filename} is not a .sauto file")
    parser = SAParser(filename).parse()
    executor = SAExecutor(parser)
    executor.run()