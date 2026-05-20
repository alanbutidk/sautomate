Automate

A cross-platform automation DSL that lets you write simple, readable `.sauto` files and run them with a single command. No complex configuration, no learning curve, just automation that does what you tell it to.

---

## Installation

Download the latest binary from the releases page and add it to your PATH.

```
sa myfile.sauto
```

---

## Usage

```
sa <file.sauto>               Run a .sauto file
sa <file.sauto> -c "<cmd>"    Run a file then an inline command
sa -c "<cmd>"                 Run an inline command without a file
sa <file.sauto> --hash <values...>   Hash sensitive values in logs
```

---

## .sauto Syntax

### Keywords

**DETAILED 1/0** -- Toggle verbose output per line.

```
DETAILED 1
```

**NEWSESSION \<shell\>** -- Run everything after this line in a new shell session.

```
NEWSESSION powershell
NEWSESSION zsh
```

**ignore \<command\> \<errorcode\>** -- Run a command and suppress a specific exit code.

```
ignore npm install 1
ignore make build 2
```

### Built-in Commands

**get-latest** -- Install or update a package.

```
get-latest ffmpeg
get-latest ffmpeg --pkg-mng choco
get-latest ffmpeg --link https://example.com/ffmpeg-installer
```

**get-usage** -- Get help output for any command, including ones without man pages.

```
get-usage pip
get-usage winget
```

**github-release** -- Create a GitHub release with assets.

```
github-release User Repo v1.0 "My Release" --executables app.exe --README README.md
```

Requires the [gh CLI](https://cli.github.com) to be installed and authenticated.

---

## Example .sauto File

```
DETAILED 1

get-latest ffmpeg --pkg-mng choco

py build.py

github-release myuser myrepo v1.0 "My App v1.0" --executables myapp.exe --README README.md
```

---

## Error Reporting

SAutomate reports errors in a consistent format:

```
myfile.sauto:4 -> command exited with code 1
myfile.sauto:1 error(s). 3/4 steps completed.
```

Runner-level errors produce a full log file at `~/.sautomate/logs/LogAtRunN.log` containing the failed call, exit code, version info, and diagnosis. Sensitive values like tokens and keys are automatically hashed using SHA3-256 before being written to any log.

---

## Security

SAutomate automatically detects and hashes common secret variable names in logs including tokens, keys, passwords, and API keys. You can extend this with the `--hash` flag:

```
sa myfile.sauto --hash MY_SECRET ANOTHER_KEY "My Token"
```

Values of 2 characters or less are never shown in logs even in masked form.

---

## License

GPLv3 in source, Free, Open-Source. Modify it YOUR WAY!
