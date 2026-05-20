from args import *
from parser import SAParser, ParsedLine
import subprocess
import sys
import os

class SAExecutor:
    def __init__(self, parser: SAParser):
        self.parser = parser
        self.filename = parser.filename if parser else None
        self.detailed = parser.detailed if parser else False
        self.current_session = "default"
        self.session_index = 0
        self.completed = 0
        self.failed = 0

    def run(self):
        session_lines = self._split_by_session()
        for session, lines in session_lines:
            self._run_session(session, lines)
        self._print_summary()

    def run_inline(self, command: str):
        fake_line = ParsedLine(0, None, command, command.split())
        first = fake_line.tokens[0]
        if first in ["github-release", "get-latest", "get-usage", "ignore"]:
            fake_line.keyword = first
        if fake_line.keyword == "ignore":
            self._run_ignore(fake_line)
        elif fake_line.keyword == "github-release":
            self._run_github_release(fake_line)
        elif fake_line.keyword == "get-latest":
            self._run_get_latest(fake_line)
        elif fake_line.keyword == "get-usage":
            self._run_get_usage(fake_line)
        else:
            self._run_shell(fake_line, self.current_session)
        self._print_summary()

    def _split_by_session(self):
        sessions = []
        current_session = "default"
        current_lines = []
        session_boundaries = {ln: shell for ln, shell in self.parser.sessions}
        for parsed in self.parser.lines:
            if parsed.line_number in session_boundaries:
                sessions.append((current_session, current_lines))
                current_session = session_boundaries[parsed.line_number]
                current_lines = []
            current_lines.append(parsed)
        sessions.append((current_session, current_lines))
        return sessions

    def _run_session(self, session: str, lines: list):
        for parsed in lines:
            if parsed.keyword == "ignore":
                self._run_ignore(parsed)
            elif parsed.keyword == "github-release":
                self._run_github_release(parsed)
            elif parsed.keyword == "get-latest":
                self._run_get_latest(parsed)
            elif parsed.keyword == "get-usage":
                self._run_get_usage(parsed)
            elif parsed.keyword is None:
                self._run_shell(parsed, session)

    def _run_shell(self, parsed: ParsedLine, session: str):
        if session == "default":
            result = subprocess.run(parsed.raw, shell=True)
        else:
            if sys.platform == "win32":
                result = subprocess.run([session, "/c", parsed.raw], shell=False)
            else:
                result = subprocess.run([session, "-c", parsed.raw], shell=False)
        if result.returncode != 0:
            self._fail(parsed, f"command exited with code {result.returncode}")
        else:
            self.completed += 1
            if self.detailed:
                print(f"\x1b[32m{self.filename}:{parsed.line_number} -> OK\033[0m")

    def _run_ignore(self, parsed: ParsedLine):
        if len(parsed.tokens) < 3:
            self._fail(parsed, "ignore requires a command and at least one error code")
            return
        ignored_codes = []
        cmd_tokens = []
        for token in parsed.tokens[1:]:
            try:
                ignored_codes.append(int(token))
            except ValueError:
                cmd_tokens.append(token)
        cmd = " ".join(cmd_tokens)
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0 and result.returncode not in ignored_codes:
            self._fail(parsed, f"command exited with code {result.returncode}")
        else:
            self.completed += 1
            if self.detailed:
                print(f"\x1b[32m{self.filename}:{parsed.line_number} -> OK (ignored codes: {ignored_codes})\033[0m")

    def _run_get_usage(self, parsed: ParsedLine):
        if len(parsed.tokens) < 2:
            self._fail(parsed, "get-usage requires a command name")
            return
        cmd = parsed.tokens[1]
        result = subprocess.run(f"{cmd} --help", shell=True, capture_output=True, text=True)
        if not result.stdout and not result.stderr:
            self._fail(parsed, f"{cmd} does not support --help or returned no output")
            return
        output = result.stdout or result.stderr
        print(output)
        self.completed += 1

    def _run_get_latest(self, parsed: ParsedLine):
        if len(parsed.tokens) < 2:
            self._fail(parsed, "get-latest requires a package name")
            return
        package = parsed.tokens[1]
        pkg_mng = None
        link = None
        if "--pkg-mng" in parsed.tokens:
            idx = parsed.tokens.index("--pkg-mng")
            if idx + 1 < len(parsed.tokens):
                pkg_mng = parsed.tokens[idx + 1]
        if "--link" in parsed.tokens:
            idx = parsed.tokens.index("--link")
            if idx + 1 < len(parsed.tokens):
                link = parsed.tokens[idx + 1]
        if link:
            self._install_from_link(parsed, package, link)
        elif pkg_mng:
            self._install_from_pkg_mng(parsed, package, pkg_mng)
        else:
            detected = self._detect_pkg_mng()
            if not detected:
                self._fail(parsed, "no package manager detected on this system")
                return
            self._install_from_pkg_mng(parsed, package, detected)

    def _detect_pkg_mng(self):
        managers = ["winget", "choco", "brew", "apt", "apt-get", "pacman", "dnf", "zypper"]
        for mgr in managers:
            result = subprocess.run(f"{mgr} --version", shell=True, capture_output=True)
            if result.returncode == 0:
                return mgr
        return None

    def _install_from_pkg_mng(self, parsed: ParsedLine, package: str, pkg_mng: str):
        result = subprocess.run(f"{pkg_mng} install {package}", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self._fail(parsed, f"{package} was not found on PKG manager {pkg_mng}")
        else:
            self.completed += 1
            if self.detailed:
                print(f"\x1b[32m{self.filename}:{parsed.line_number} -> {package} installed via {pkg_mng}\033[0m")

    def _install_from_link(self, parsed: ParsedLine, package: str, link: str):
        print(f"\x1b[33mWarning:\033[0m Installing {package} from direct link. Verify the source is trusted.")
        if sys.platform == "win32":
            result = subprocess.run(f"curl -L {link} -o {package}_installer && {package}_installer", shell=True)
        else:
            result = subprocess.run(f"curl -L {link} | sh", shell=True)
        if result.returncode != 0:
            self._fail(parsed, f"{package} failed to install from link")
        else:
            self.completed += 1
            if self.detailed:
                print(f"\x1b[32m{self.filename}:{parsed.line_number} -> {package} installed from link\033[0m")

    def _run_github_release(self, parsed: ParsedLine):
        if len(parsed.tokens) < 5:
            self._fail(parsed, "github-release requires: User Repo TagName Title")
            return
        user = parsed.tokens[1]
        repo = parsed.tokens[2]
        tag = parsed.tokens[3]
        title = parsed.tokens[4]
        executables = []
        readme = None
        if "--executables" in parsed.tokens:
            idx = parsed.tokens.index("--executables")
            for token in parsed.tokens[idx + 1:]:
                if token.startswith("--"):
                    break
                executables.append(token)
        if "--README" in parsed.tokens:
            idx = parsed.tokens.index("--README")
            if idx + 1 < len(parsed.tokens):
                readme = parsed.tokens[idx + 1]
        gh_check = subprocess.run("gh --version", shell=True, capture_output=True)
        if gh_check.returncode != 0:
            self._fail(parsed, "gh CLI is not installed, use get-latest gh to install it")
            return
        cmd = f'gh release create {tag} --title "{title}" --repo {user}/{repo}'
        if readme:
            cmd += f" --notes-file {readme}"
        for exe in executables:
            cmd += f" {exe}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            if "rate limit" in result.stderr.lower():
                reset_time = self._parse_rate_limit_reset(result.stderr)
                if reset_time:
                    print(f"\x1b[31mgithub-release is rate-limited. Resets in {reset_time}\033[0m")
                else:
                    print(f"\x1b[31mgithub-release is detecting rate-limitation, try again later\033[0m")
                self._fail(parsed, "github-release rate limited")
            else:
                self._fail(parsed, f"github-release failed: {result.stderr.strip()}")
        else:
            self.completed += 1
            if self.detailed:
                print(f"\x1b[32m{self.filename}:{parsed.line_number} -> release {tag} created for {user}/{repo}\033[0m")

    def _parse_rate_limit_reset(self, stderr: str):
        import re
        match = re.search(r"(\d+)\s*minutes?", stderr)
        if match:
            return f"{match.group(1)} minutes"
        match = re.search(r"(\d+:\d+\s*UTC)", stderr)
        if match:
            return f"{match.group(1)}"
        return None

    def _fail(self, parsed: ParsedLine, reason: str):
        self.failed += 1
        print(f"\x1b[31m{self.filename}:{parsed.line_number} -> {reason}\033[0m")

    def _print_summary(self):
        total = self.completed + self.failed
        if self.failed > 0:
            print(f"\n\x1b[31m{self.filename}: {self.failed} error(s). {self.completed}/{total} steps completed.\033[0m")
        else:
            print(f"\n\x1b[32m{self.filename}: all {total} steps completed.\033[0m")