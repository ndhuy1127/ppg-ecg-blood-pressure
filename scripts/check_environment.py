"""Verify that the minimum development environment is available."""

import sys

import matplotlib
import numpy as np
import pandas as pd
import scipy
import sklearn
import yaml


def main() -> int:
    """Run lightweight imports and a deterministic NumPy calculation."""
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
        f"pyyaml={yaml.__version__}",
    )
    print(f"NumPy result: {doubled.tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
