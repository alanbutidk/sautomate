import re

files = [
    "executor.py",
    "parser.py",
    "sa.py",
    "args.py",
    "filehandle.py",
    "logger.py",
    "operations.py"
]

for filename in files:
    try:
        with open(filename, "r") as f:
            content = f.read()
        fixed = content.expandtabs(4)
        with open(filename, "w") as f:
            f.write(fixed)
        print(f"Fixed: {filename}")
    except FileNotFoundError:
        print(f"Skipped: {filename} not found")