"""Smoke tests for the initial repository scaffold."""

from pathlib import Path

import numpy as np

import software


def test_software_package_can_be_imported() -> None:
    """The top-level software package is importable."""
    assert software.__doc__


def test_main_module_directories_exist() -> None:
    """All planned software modules exist and are Python packages."""
    package_root = Path(software.__file__).parent
    modules = (
        "data_io",
        "preprocessing",
        "signal_processing",
        "feature_extraction",
        "models",
        "evaluation",
        "deployment",
    )

    for module_name in modules:
        module_path = package_root / module_name
        assert module_path.is_dir()
        assert (module_path / "__init__.py").is_file()


def test_numpy_processing_is_correct() -> None:
    """A small deterministic NumPy operation returns the expected result."""
    signal = np.array([1.0, 2.0, 3.0, 4.0])
    centered = signal - signal.mean()
    expected = np.array([-1.5, -0.5, 0.5, 1.5])

    np.testing.assert_allclose(centered, expected)
