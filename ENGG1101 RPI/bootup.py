#!/usr/bin/env python3
"""
bootup.py  – “fire-and-forget” dependency helper
================================================

• Creates (or re-uses) a virtual-environment called *iaq-env* that lives
  next to this file.  
• Re-execs itself *inside* that venv (no manual activation needed).  
• Ensures the **required** packages are importable.  
    – each package is installed individually,  
    – failures are reported but do **not** stop the rest of the work.  
• Prints friendly hints for *optional* Debian packages.  

Designed for Raspberry-Pi / Debian but portable to any POSIX system.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent

VENV_DIR   = SCRIPT_DIR / "iaq-env"
VENV_PY    = VENV_DIR / "bin" / "python3"          # Linux / Pi

# Required  {import-name: PyPI package}
REQUIRED: Dict[str, str] = {
    "adafruit_blinka": "adafruit-blinka",
    "adafruit_ahtx0":  "adafruit-circuitpython-ahtx0",
    "adafruit_ens160":"adafruit-circuitpython-ens160",
    "RPi.GPIO":        "RPi.GPIO",
    "smbus2":          "smbus2",
    "numpy":           "numpy",
    "serial":          "pyserial",
}

# Optional  {import-name: apt package   (only a hint)}
OPTIONAL_APT: Dict[str, str] = {
    "lgpio":  "python3-lgpio",
    "pigpio": "python3-pigpio",
}

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _run(cmd: List[str]) -> tuple[int, str]:
    """Run *cmd*; return (exit code, combined stdout+stderr)."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out  = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def _ensure_venv() -> None:
    """Create the venv once and re-exec inside it."""
    if sys.executable == str(VENV_PY):
        return  # already inside

    try:
        if not VENV_DIR.exists():
            print(f"🔧  Creating venv at {VENV_DIR} …")
            subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

        # Upgrade the core packaging tools (idempotent)
        subprocess.check_call(
            [str(VENV_PY), "-m", "pip", "install", "--upgrade",
             "pip", "setuptools", "wheel"],
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"❌  Failed to prepare the venv ({exc}). Aborting.")

    # Re-exec ourselves using the venv’s interpreter
    print("🔄  Re-executing inside the venv …\n")
    os.execv(str(VENV_PY), [str(VENV_PY)] + sys.argv)


def _install_package(pkg: str) -> bool:
    """Return True on success, False if installation failed."""
    print(f"    → pip install {pkg}")
    rc, out = _run([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
    if rc == 0:
        return True
    # pip failed – show last few lines
    print("      ⚠️  pip error:")
    for line in out.strip().splitlines()[-8:]:
        print("      " + line)
    return False


def _advise_optional() -> None:
    for mod, apt_pkg in OPTIONAL_APT.items():
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            print(f"ℹ️  Optional:  sudo apt install {apt_pkg}   "
                  f"(needed for  import {mod})")


# ----------------------------------------------------------------------
# Main sequence
# ----------------------------------------------------------------------
def bootup_sequence() -> None:
    missing: List[str] = []

    # first detection pass
    for mod, pkg in REQUIRED.items():
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            missing.append(pkg)

    if not missing:
        print("✅  Environment already complete – nothing to install.")
        _advise_optional()
        return

    print("⏳  Installing missing packages …")
    failed: List[str] = []

    for pkg in missing:
        if not _install_package(pkg):
            failed.append(pkg)

    # second detection pass (verify)
    still_missing: List[str] = []
    for mod, pkg in REQUIRED.items():
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError:
            still_missing.append(pkg)

    # ------------------------------------------------------------------
    #  Results
    # ------------------------------------------------------------------
    if not still_missing:
        print("✅  All mandatory dependencies satisfied.")
    else:
        print("\n❌  Some packages could not be installed/imported:")
        for pkg in still_missing:
            print(f"   • {pkg}")
        print("   Application may not run correctly.\n")

    if failed:
        print("📝  See pip output above for error details.")

    _advise_optional()


# ----------------------------------------------------------------------
if __name__ == "__main__":
    _ensure_venv()          # may replace the current process
    bootup_sequence()       # runs only inside the venv