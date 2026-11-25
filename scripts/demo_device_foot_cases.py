"""SYNTHETIC figure of the hard cases of the device PPG foot (device-foot-v1 draft).

Four beats built by hand: a plain pulse, a ridge before the upstroke, a flat floor
and a later wave taller than the systolic one. On each, the draft rules of
docs/protocol/device_ppg_foot_definition_v1.md section 3 are drawn: A, the
steepest point of the first rise after R; B, the level of the last local minimum
before A; the foot, where the tangent at A meets B. The point the current
``tangent``/``valley_min`` code takes as the valley (lowest value in the 0.5 s
before the detected peak) is drawn too. Figure only: nothing here is used by the
pipeline, and SYNTHETIC results never say anything about real data.

    python scripts/demo_device_foot_cases.py --output runs/demo_device_foot/cases.svg

Refuses to overwrite.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FS = 200.0
R_S = 0.0
ONSET_S = 0.20  # set foot of every case: R + 200 ms


def _rise(t, onset, width=0.10, height=1.0):
    x = np.clip((t - onset) / width, 0, 1)
    return height * 0.5 * (1 - np.cos(np.pi * x))


def _decay(t, start, length, height):
    x = np.clip((t - start) / length, 0, 1)
    return height * 0.5 * (1 + np.cos(np.pi * x)) * (t >= start)


def _bump(t, centre, width, height):
    return height * np.exp(-0.5 * ((t - centre) / width) ** 2)


def cases():
    """(title, t, signal) of the four beats; t in s from R, set foot at ONSET_S."""
    t = np.arange(-0.6, 0.8, 1 / FS)
    pulse = _rise(t, ONSET_S) * (t < ONSET_S + 0.1) + _decay(t, ONSET_S + 0.1, 0.45, 1.0)
    plain = pulse + _decay(t, -0.6, 0.8, 0.35)  # previous beat decays to the onset
    ridge = pulse + _decay(t, -0.6, 0.5, 0.35) - _bump(t, -0.12, 0.05, 0.25)         + _bump(t, 0.06, 0.05, 0.10)  # deep notch, then a small wave, then the rise
    flat = pulse + _decay(t, -0.6, 0.3, 0.35)  # floor flat for 0.5 s before the onset
    first = _rise(t, ONSET_S, 0.08, 0.55) * (t < ONSET_S + 0.08)         + _decay(t, ONSET_S + 0.08, 0.12, 0.55) * (t < ONSET_S + 0.14)
    dip = ONSET_S + 0.14
    level = float(first[np.searchsorted(t, dip) - 1])
    second = (t >= dip) * (level + _rise(t, dip, 0.08, 1.0 - level) * (t < dip + 0.08)
                           + (1.0 - level) * (t >= dip + 0.08))         * np.where(t >= dip + 0.08, _decay(t, dip + 0.08, 0.4, 1.0), 1.0)
    taller = first + second + _decay(t, -0.6, 0.8, 0.35)
    return [("Bình thường", t, plain), ("Gờ trước sườn lên", t, ridge),
            ("Đáy phẳng", t, flat), ("Sóng sau cao hơn sóng tâm thu", t, taller)]


def draft_foot(t, y, r_s=R_S, rise_min_fraction=0.3):
    """Draft rules, as ``fiducials.feet_after_r`` (rise-after-r-v1): A = steepest
    forward step of the first rising run after R that climbs at least
    ``rise_min_fraction`` of the P1-P99 range; B = value at the start of that run;
    foot = tangent at A meets B. Returns (a_index, b_index, foot)."""
    from software.signal_processing.fiducials import _rising_runs
    runs, slopes = _rising_runs(y, t)
    scale = np.percentile(y, 99) - np.percentile(y, 1)
    for start, stop, steep in runs:
        if t[start] >= r_s and y[stop] - y[start] >= rise_min_fraction * scale:
            return steep, start, float(t[steep] - (y[steep] - y[start]) / slopes[steep])
    return None, None, None


def code_foot(t, y):
    """(valley index, foot time) of the current code (fiducials.ppg_fiducials,
    ``tangent``) for the tallest peak after R."""
    from software.signal_processing.fiducials import SignalConfig, ppg_fiducials
    after = np.flatnonzero(t >= R_S)
    peak = int(after[int(np.argmax(y[after]))])
    beats = ppg_fiducials(y, t, np.array([peak]), SignalConfig(edge_s=0.0))
    return (beats[0][2], beats[0][0]) if beats else (None, None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path,
                        default=ROOT / "runs/demo_device_foot/device_foot_v1_cases.svg")
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit(f"refusing to overwrite {args.output}")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 4, figsize=(14, 3.4), sharey=False)
    for ax, (title, t, y) in zip(axes, cases()):
        a, b, foot = draft_foot(t, y)
        v, old_foot = code_foot(t, y)
        ax.plot(t * 1000, y, color="0.2", lw=1.2)
        ax.axvline(R_S * 1000, color="0.6", lw=0.8, ls=":")
        ax.text(R_S * 1000, ax.get_ylim()[1], " R", va="top", fontsize=8, color="0.4")
        if a is not None:
            line = np.array([foot - 0.02, t[a] + 0.03])
            slope = (y[a + 1] - y[a]) / (t[a + 1] - t[a])
            ax.plot(line * 1000, y[a] + (line - t[a]) * slope,
                    color="tab:green", lw=0.9)
            ax.axhline(y[b], color="tab:green", lw=0.8, ls="--")
            ax.plot(t[a] * 1000, y[a], "o", color="tab:green", ms=4, label="A")
            ax.plot(t[b] * 1000, y[b], "s", color="tab:green", ms=4, label="B")
            ax.axvline(foot * 1000, color="tab:green", lw=1.2,
                       label=f"chân sóng {foot * 1000:.0f} ms")
        ax.plot(t[v] * 1000, y[v], "x", color="tab:red", ms=7, label="đáy của code hiện tại")
        ax.axvline(old_foot * 1000, color="tab:red", lw=1.0, ls="--",
                   label=f"chân của code hiện tại {old_foot * 1000:.0f} ms")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("ms từ R (chân đặt ở 200 ms)", fontsize=8)
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("SYNTHETIC: device-foot-v1 (bản nháp), không phải dữ liệu thật", fontsize=10)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "xb") as handle:
        fig.savefig(handle, format="svg")
    for title, t, y in cases():
        a, b, foot = draft_foot(t, y)
        print(f"{title}: draft foot {foot * 1000:.1f} ms, current code foot "
              f"{code_foot(t, y)[1] * 1000:.1f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
