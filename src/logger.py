from pathlib import Path
import hashlib
import sys
import os
import datetime

KNOWN_SECRET_PATTERNS = [
    "token", "secret", "key", "password", "passwd",
    "private", "aws_access", "azure_", "database_url",
    "openai_api_key", "env", "env_key", "env_token",
    "gh_token", "api_key"
]

HASH_VALUES = []

LOG_DIR = Path.home() / ".sautomate" / "logs"

def SetHashValues(values: list):
    global HASH_VALUES
    HASH_VALUES = [v.lower() for v in values]

def _hash_value(value: str) -> str:
    return hashlib.sha3_256(value.encode()).hexdigest()

def _should_hash(key: str) -> bool:
    key_lower = key.lower()
    if key_lower in HASH_VALUES:
        return True
    for pattern in KNOWN_SECRET_PATTERNS:
        if pattern in key_lower:
            return True
    return False

def _mask_value(value: str) -> str:
    if len(value) <= 2:
        return ""
    return value[:2] + "*" * (len(value) - 2)

def _get_log_index() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(LOG_DIR.glob("LogAtRun*.log"))
    return len(existing) + 1

def _filter_line(line: str) -> str:
    filtered_tokens = []
    tokens = line.split()
    skip_next = False
    for i, token in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        if "=" in token:
            key, _, val = token.partition("=")
            if _should_hash(key):
                filtered_tokens.append(f"{key}={_hash_value(val)}")
            else:
                filtered_tokens.append(token)
        else:
            filtered_tokens.append(token)
    return " ".join(filtered_tokens)

def _is_noise(line: str) -> bool:
    noise_patterns = [
        "malloc", "free(", "memcpy", "mmap",
        "munmap", "brk(", "mprotect", "rt_sigaction",
        "rt_sigprocmask", "getpid", "gettid",
        "clock_gettime", "futex"
    ]
    line_lower = line.lower()
    return any(p in line_lower for p in noise_patterns)

class BadSystemOperation:
    def __init__(self, filename: str, line_number: int, call: str,
                 exit_code: int, error: str, extra_hash: list = []):
        self.filename = filename
        self.line_number = line_number
        self.call = call
        self.exit_code = exit_code
        self.error = error
        self.extra_hash = [v.lower() for v in extra_hash]
        self.timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.log_index = _get_log_index()

    def _check_version(self, cmd: str) -> str:
        import subprocess
        tool = cmd.split()[0]
        result = subprocess.run(
            f"{tool} --version",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip() or result.stderr.strip()
        return "version unknown"

    def _build_report(self) -> str:
        version_info = self._check_version(self.call)
        filtered_call = _filter_line(self.call)

        lines = [
            f"[BadSystemOperation — Run {self.log_index}]",
            f"Timestamp:   {self.timestamp}",
            f"File:        {self.filename}",
            f"Line:        {self.line_number}",
            f"Call:        {filtered_call}",
            f"Exit Code:   {self.exit_code}",
            f"Version:     {version_info}",
            f"Diagnosis:   {self.error}",
        ]

        if self.extra_hash:
            hash_log = self._build_hash_log()
            if hash_log:
                lines.append(f"Hash Log:    {hash_log}")

        return "\n".join(lines)

    def _build_hash_log(self) -> str:
        entries = []
        for val in self.extra_hash:
            masked = _mask_value(val)
            if not masked:
                continue
            entries.append(
                f'[{self.timestamp}] LOG: --hash: "{masked}" was not found'
            )
        return "\n".join(entries) if entries else ""

    def write(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"LogAtRun{self.log_index}.log"
        report = self._build_report()

        with open(log_path, 'w') as f:
            f.write(report)

        print(f"\x1b[31mBadSystemOperation caught. Log written to {log_path}\033[0m")
        return log_path