"""Pin and Python-version comparison of scripts/check_environment.py."""

from importlib.metadata import version

from scripts.check_environment import pin_problems, python_problems


def test_python_spec_accepts_only_the_pinned_minor():
    assert python_problems(">=3.11,<3.12", (3, 11, 9)) == []
    assert python_problems(">=3.11,<3.12", (3, 13, 12)) == ["Python 3.13.12 violates <3.12"]
    assert python_problems(">=3.11,<3.12", (3, 10, 4)) == ["Python 3.10.4 violates >=3.11"]


def test_pin_comparison_reports_missing_unpinned_and_different_versions():
    installed = version("pytest")
    text = (f"pytest=={installed}  # comment\n\npytest==0.0.1\n"
            "not-a-real-package-xyz==1.0\nnumpy\n")
    problems = pin_problems(text)
    assert problems == [
        f"pytest=={installed} differs from pin 0.0.1",
        "not-a-real-package-xyz is not installed (pin 1.0)",
        "Unpinned requirement: numpy",
    ]
