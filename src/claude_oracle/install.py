"""Install Oracle skill files into ~/.claude/skills/oracle/."""

import os
import shutil
import sys

SKILL_DIR = os.path.join(os.path.expanduser("~"), ".claude", "skills", "oracle")
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

# Shim written into the skill dir. It re-execs with the interpreter claude_oracle
# was installed into if the `python` that launches it can't import the package
# (venv / --user installs where the default interpreter differs). ASCII-only and
# written as UTF-8 so it always parses regardless of the platform code page.
_SHIM_TEMPLATE = '''\
"""Shim - delegates to the pip-installed claude_oracle package."""
import os
import sys

# Interpreter claude_oracle was installed into (captured at install time).
INSTALL_PYTHON = __INSTALL_PYTHON__

try:
    from claude_oracle.sdk import _async_main
except ModuleNotFoundError:
    # This `python` cannot import claude_oracle; re-exec once with the
    # interpreter it was installed into (preserves argv and piped stdin).
    if (
        INSTALL_PYTHON
        and os.path.exists(INSTALL_PYTHON)
        and os.path.realpath(INSTALL_PYTHON) != os.path.realpath(sys.executable)
    ):
        os.execv(INSTALL_PYTHON, [INSTALL_PYTHON, os.path.abspath(__file__), *sys.argv[1:]])
    raise

import asyncio

if __name__ == "__main__":
    asyncio.run(_async_main())
'''


def install():
    os.makedirs(SKILL_DIR, exist_ok=True)

    # Copy SKILL.md from package data (binary-preserving copy — no re-encoding).
    skill_src = os.path.join(PACKAGE_DIR, "data", "SKILL.md")
    if not os.path.exists(skill_src):
        print(f"ERROR: SKILL.md not found at {skill_src}", file=sys.stderr)
        sys.exit(1)

    skill_dst = os.path.join(SKILL_DIR, "SKILL.md")
    shutil.copy2(skill_src, skill_dst)
    print(f"Installed SKILL.md -> {skill_dst}")

    # Create a thin oracle_sdk.py that delegates to the installed package.
    shim = os.path.join(SKILL_DIR, "oracle_sdk.py")
    shim_body = _SHIM_TEMPLATE.replace("__INSTALL_PYTHON__", repr(sys.executable))
    with open(shim, "w", encoding="utf-8") as f:
        f.write(shim_body)
    print(f"Installed oracle_sdk.py shim -> {shim}")

    print("\nOracle installed. Use /oracle in Claude Code.")


if __name__ == "__main__":
    install()
