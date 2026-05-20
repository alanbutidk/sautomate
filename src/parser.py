from args import *
import sys

SpecialKeywords = [
    "DETAILED",
    "NEWSESSION",
    "ignore",
    "github-release",
    "get-latest",
    "get-usage"
]

class ParsedLine:
    def __init__(self, line_number: int, keyword: str, raw: str, tokens: list, session: str = "default"):
        self.line_number = line_number
        self.keyword = keyword
        self.raw = raw
        self.tokens = tokens
        self.session = session

class SAParser:
    def __init__(self, filename: str):
        self.filename = filename
        self.lines = []
        self.detailed = False
        self.sessions = []
        self.errors = []

    def parse(self):
        try:
            with open(self.filename, 'r') as f:
                raw_lines = f.read().splitlines()
        except FileNotFoundError:
            print(f"\x1b[31mError:\033[0m {self.filename} was not found")
            sys.exit(1)
        except PermissionError:
            print(f"\x1b[31mError:\033[0m {self.filename} could not be read, permission denied")
            sys.exit(1)

        current_session = "default"

        for i, line in enumerate(raw_lines):
            line_num = i + 1
            stripped = line.strip()

            if not stripped:
                continue

            tokens = stripped.split()
            first = tokens[0]

            if first == "DETAILED":
                if len(tokens) < 2:
                    self.errors.append((line_num, "DETAILED requires 1 or 0"))
                    continue
                if tokens[1] == "1":
                    self.detailed = True
                elif tokens[1] == "0":
                    self.detailed = False
                else:
                    self.errors.append((line_num, f"DETAILED expects 1 or 0, got {tokens[1]}"))
                continue

            if first == "NEWSESSION":
                if len(tokens) < 2:
                    self.errors.append((line_num, "NEWSESSION requires a shell name"))
                    continue
                current_session = tokens[1]
                self.sessions.append((line_num, current_session))
                continue

            keyword = first if first in SpecialKeywords else None
            self.lines.append(ParsedLine(line_num, keyword, stripped, tokens, current_session))

        if self.errors:
            for line_num, error in self.errors:
                print(f"\x1b[31m{self.filename}:{line_num} -> {error}\033[0m")
            sys.exit(1)

        return self