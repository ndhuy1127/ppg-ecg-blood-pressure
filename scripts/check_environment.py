"""Verify the development environment against the repository pins.

Exit 0 only when Python matches ``requires-python`` in pyproject.toml, every
``name==version`` line of requirements.txt is installed at that version and
the core imports work. Any mismatch is listed and the exit code is 1.
"""

import operator
import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import matplotlib
import mat73
import numpy as np
import pandas as pd
import scipy
import sklearn
import xgboost
import yaml

ROOT = Path(__file__).resolve().parents[1]
OPERATORS = {">=": operator.ge, "<=": operator.le, "==": operator.eq,
             "!=": operator.ne, ">": operator.gt, "<": operator.lt}


def _release(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.strip().split("."))


def python_problems(spec: str, current: tuple[int, ...]) -> list[str]:
    """Check simple comma-separated specifiers such as ``>=3.11,<3.12``."""
    problems = []
    for clause in filter(None, (c.strip() for c in spec.split(","))):
        symbol = next(s for s in sorted(OPERATORS, key=len, reverse=True)
                      if clause.startswith(s))
        wanted = _release(clause[len(symbol):])
        if not OPERATORS[symbol](current[:len(wanted)], wanted):
            problems.append(f"Python {'.'.join(map(str, current))} violates {clause}")
    return problems


def pin_problems(requirements: str) -> list[str]:
    problems = []
    for line in requirements.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        name, separator, pinned = line.partition("==")
        if not separator:
            problems.append(f"Unpinned requirement: {line}")
            continue
        try:
            installed = version(name.strip())
        except PackageNotFoundError:
            problems.append(f"{name.strip()} is not installed (pin {pinned.strip()})")
            continue
        if installed != pinned.strip():
            problems.append(f"{name.strip()}=={installed} differs from pin {pinned.strip()}")
    return problems


def main() -> int:
    """Run lightweight imports, a NumPy calculation and the pin comparison."""
    values = np.array([1.0, 2.0, 3.0])
    doubled = values * 2
    if not np.array_equal(doubled, np.array([2.0, 4.0, 6.0])):
        raise RuntimeError("NumPy environment check failed")

    print(f"Python: {sys.version.split()[0]}")
    print(
        "Libraries imported:",
        f"numpy={np.__version__},",
        f"scipy={scipy.__version__},",
        f"pandas={pd.__version__},",
        f"matplotlib={matplotlib.__version__},",
        f"scikit-learn={sklearn.__version__},",
        f"xgboost={xgboost.__version__},",
        f"mat73={version(mat73.__name__)},",
        f"pyyaml={yaml.__version__}",
    )
    print(f"NumPy result: {doubled.tolist()}")

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    problems = python_problems(project["project"]["requires-python"],
                               tuple(sys.version_info[:3]))
    problems += pin_problems((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    for problem in problems:
        print(f"MISMATCH: {problem}")
    if problems:
        print("Environment does not match the repository pins.")
        return 1
    print("Environment matches requirements.txt and requires-python.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
