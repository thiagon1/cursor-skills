"""Shared VTEX CLI auth for the scripts in this folder.

VTEX_AUTH_TOKEN wins when it is set. Otherwise the token comes from `vtex local token`,
which is read defensively: the CLI can print an update notice or a warning alongside the
token, and picking the wrong line yields a 401 that looks like an expired login.

The CLI is resolved with shutil.which because on Windows an npm-installed `vtex` is a
.cmd shim, and subprocess only ever resolves a bare name to .exe.
"""

import os
import re
import shutil
import subprocess
import sys

TOKEN = re.compile(r"[A-Za-z0-9._-]{40,}")
LOGIN_HINT = "run `vtex login <account>`, or set VTEX_AUTH_TOKEN"


def vtex_cli() -> str:
    path = shutil.which("vtex")
    if not path:
        sys.exit(f"`vtex` CLI not found on PATH — {LOGIN_HINT}")
    return path


def auth_token() -> str:
    env = os.environ.get("VTEX_AUTH_TOKEN")
    if env:
        return env.strip()

    try:
        out = subprocess.run(
            [vtex_cli(), "local", "token"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as exc:
        sys.exit(f"could not run `vtex local token`: {exc}")

    if out.returncode != 0:
        detail = (out.stderr or out.stdout).strip().splitlines()
        tail = f": {detail[-1]}" if detail else ""
        sys.exit(f"`vtex local token` failed{tail} — {LOGIN_HINT}")

    lines = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    matches = [line for line in lines if TOKEN.fullmatch(line)]
    if matches:
        return matches[-1]
    if len(lines) == 1:
        return lines[0]
    sys.exit(f"no token found in `vtex local token` output ({len(lines)} lines) — {LOGIN_HINT}")


def infer_account() -> str:
    """Read the account out of `vtex whoami`, whose phrasing varies by CLI version."""
    try:
        who = subprocess.run(
            [vtex_cli(), "whoami"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError) as exc:
        sys.exit(f"could not run `vtex whoami` ({exc}) — pass --account")
    match = re.search(r"Logged into (\S+) as", who.stdout + who.stderr)
    if not match:
        sys.exit("could not infer the account from `vtex whoami` — pass --account")
    return match.group(1)
