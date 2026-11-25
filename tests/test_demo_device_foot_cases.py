"""SYNTHETIC hard cases of the device PPG foot (scripts/demo_device_foot_cases.py).

The draft rules of docs/protocol/device_ppg_foot_definition_v1.md section 3 keep
the foot on the first rise after R in every case; the current ``tangent`` code
moves it on a deep notch and takes the wrong wave when the later wave is taller.
A raised-cosine rise has zero slope at its onset, so the tangent foot sits 18 ms
after the set onset: a property of the tangent, the same in every case.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import demo_device_foot_cases as demo  # noqa: E402


def test_draft_rules_keep_the_foot_on_the_first_rise():
    feet = {title: demo.draft_foot(t, y)[2] for title, t, y in demo.cases()}
    for title, foot in feet.items():
        assert foot == pytest.approx(demo.ONSET_S + 0.018, abs=0.006), title


def test_current_code_differs_where_the_figure_says():
    old = {title: demo.code_foot(t, y)[1] for title, t, y in demo.cases()}
    assert old["Bình thường"] == pytest.approx(0.218, abs=0.002)
    assert old["Đáy phẳng"] == pytest.approx(0.218, abs=0.002)
    assert old["Gờ trước sườn lên"] < 0.21  # B on the deeper notch: earlier foot
    assert old["Sóng sau cao hơn sóng tâm thu"] > 0.3  # the wrong wave


def test_script_refuses_to_overwrite(tmp_path):
    target = tmp_path / "cases.svg"
    assert demo.main(["--output", str(target)]) == 0
    assert target.read_text(encoding="utf-8").startswith("<?xml")
    with pytest.raises(SystemExit, match="refusing"):
        demo.main(["--output", str(target)])
