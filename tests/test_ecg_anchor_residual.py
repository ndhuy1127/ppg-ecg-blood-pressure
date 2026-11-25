"""Criterion A10 (sync_10min_test_plan.md section 11.2) on SYNTHETIC packet rows.

The answers come from the written rule, not from the code: a line fitted on the
previous 10 s of valid ECG packets of the same chain predicts each anchor; more
than 0.5 ms off (either side) flags the packet and cuts the chain, and scoring
restarts only after 10 s of valid packets. The plan requires that steps of
+-1.953 ms (one ECG sample) and +-0.75 ms injected into a clean chain are caught,
and that a clean chain is not flagged. SYNTHETIC only: verifies code.
"""

import json
import random

import pytest

from scripts import check_ecg_anchor_residual as script
from software.device import ecg_anchor_residual as a10

PERIOD_US = 1e6 / 512
SAMPLES = 16
SESSION = 1234


def ecg_rows(seconds, step_at_s=None, step_us=0.0, jitter_us=150.0, seed=7,
             session=SESSION, chain=0, channel="0xE1", start_seq=0, start_t=1_000_000):
    """FIFO-read anchors of 16-sample packets at 512 sps, positive jitter like the
    pilot (scheduling only delays a read), optional step from ``step_at_s`` on."""
    rng = random.Random(seed)
    rows = []
    for n in range(int(seconds * 512 / SAMPLES)):
        last = (n + 1) * SAMPLES - 1
        t = start_t + last * PERIOD_US + rng.uniform(0, jitter_us)
        if step_at_s is not None and last * PERIOD_US >= step_at_s * 1e6:
            t += step_us
        rows.append({"session_id": session, "version": 2, "channel_id": channel,
                     "seq_ext": start_seq + n, "sample_index_ext": n * SAMPLES,
                     "chain_id": chain, "t_anchor_us": round(t),
                     "sample_count": SAMPLES, "fs_nominal_mhz": 512_000, "status": 0x10,
                     "disposition": "accepted"})
    return rows


def only(result):
    assert len(result["sessions"]) == 1
    return result["sessions"][0]


def test_clean_chain_is_not_flagged_and_first_10_s_are_not_scored():
    result = a10.check(ecg_rows(60))
    s = only(result)
    assert s["packets_flagged"] == 0 and result["passed"] is True
    # 10 s at 32 packets/s are history only.
    assert 319 <= s["packets_not_yet_scored"] <= 321
    assert s["packets_scored"] + s["packets_not_yet_scored"] == 60 * 32
    assert s["max_abs_residual_us"] < 150


@pytest.mark.parametrize("step_us", [1953.125, -1953.125, 750.0, -750.0])
def test_injected_steps_are_caught_where_they_start(step_us):
    rows = ecg_rows(60, step_at_s=30, step_us=step_us)
    s = only(a10.check(rows))
    assert s["packets_flagged"] >= 1 and s["flagged"][0]["residual_us"] * step_us > 0
    first_stepped = next(r["seq_ext"] for r in rows
                         if (r["sample_index_ext"] + SAMPLES - 1) * PERIOD_US >= 30e6)
    assert s["flagged"][0]["seq_ext"] == first_stepped
    # The chain is cut: the next 10 s rebuild the line, then the new level is clean.
    assert s["packets_flagged"] == 1
    assert 2 * 319 <= s["packets_not_yet_scored"] <= 2 * 321 + 1


def test_step_under_the_limit_passes_as_written():
    # 0.4 ms is below 0.5 ms: A10 lets it through by design (A3 covers small steps).
    s = only(a10.check(ecg_rows(60, step_at_s=30, step_us=400.0)))
    assert s["packets_flagged"] == 0


def test_unreliable_and_quarantined_packets_are_neither_scored_nor_used():
    rows = ecg_rows(30)
    rows[400]["disposition"] = "accepted_anchor_unreliable"
    rows[400]["t_anchor_us"] += 50_000  # bit 0: anchor not that of its last sample
    rows[500]["disposition"] = "timestamp_anomaly"
    rows[500]["sample_index_ext"] = None
    s = only(a10.check(rows))
    assert s["packets_flagged"] == 0 and s["packets_not_scored"] == 2


def test_new_chain_or_anchor_source_restarts_the_history():
    first = ecg_rows(20)
    second = ecg_rows(20, chain=1, start_seq=len(first), start_t=40_000_000, seed=8)
    s = only(a10.check(first + second))
    assert s["packets_flagged"] == 0
    assert 2 * 319 <= s["packets_not_yet_scored"] <= 2 * 321
    # SAMP-anchored packets (bit 8) never share a line with FIFO-read ones.
    mixed = ecg_rows(20)
    for row in mixed[320:]:
        row["status"] |= 1 << 8
        row["t_anchor_us"] -= 30_000  # unknown offset between the two sources
    s = only(a10.check(mixed))
    assert s["packets_flagged"] == 0


def test_missing_samples_restart_the_history():
    # Packets lost in the middle of a chain: the line is not fitted across the
    # hole, the next 10 s are history again (as after a cut).
    rows = ecg_rows(40)
    del rows[600:700]
    s = only(a10.check(rows))
    assert s["packets_flagged"] == 0
    assert 2 * 319 <= s["packets_not_yet_scored"] <= 2 * 321
    # An unreliable anchor (bit 0) is not a valid packet either: 10 s of reliable
    # anchors are needed again after it.
    rows = ecg_rows(40)
    rows[600]["disposition"] = "accepted_anchor_unreliable"
    s = only(a10.check(rows))
    assert 2 * 319 <= s["packets_not_yet_scored"] <= 2 * 321 and s["packets_not_scored"] == 1


def test_other_channels_and_sessions_are_separate():
    rows = (ecg_rows(15) + ecg_rows(15, channel="0xF1", step_at_s=12, step_us=5000)
            + ecg_rows(15, session=99, step_at_s=12, step_us=1953.125))
    result = a10.check(rows)
    by_session = {s["session_id"]: s for s in result["sessions"]}
    assert set(by_session) == {SESSION, 99}
    assert by_session[SESSION]["packets_flagged"] == 0
    assert by_session[99]["packets_flagged"] == 1 and result["passed"] is False


def test_no_ecg_means_no_verdict_and_too_short_is_not_a_pass():
    assert a10.check(ecg_rows(5, channel="0xF1"))["passed"] is None
    # Nothing scored in 5 s: no verdict, not a pass and not a failure.
    result = a10.check(ecg_rows(5))
    assert result["passed"] is None and only(result)["passed"] is None
    # One clean scored session does not hide an unscored one.
    assert a10.check(ecg_rows(30) + ecg_rows(5, session=99))["passed"] is None


def test_first_scorable_packet_is_scored_whatever_its_own_anchor():
    # The 10 s are counted on the sample index, so a bad anchor on the first packet
    # that has 10 s of history cannot push itself back into the history.
    for step in (-750.0, 750.0):
        rows = ecg_rows(30, jitter_us=0.0)
        first = 320  # last sample 16 * 320 + 15: exactly 5120 samples after packet 0
        rows[first]["t_anchor_us"] += round(step)
        s = only(a10.check(rows))
        assert s["flagged"][0]["seq_ext"] == first and s["packets_flagged"] == 1
        # 320 packets of history before it, 320 again after the cut.
        assert s["packets_not_yet_scored"] == 2 * first


def test_residuals_match_an_independent_fit_on_a_drifting_rate():
    # Rate drifts by 300 ppm over the record: the line must follow the last 10 s
    # (inclusive), recomputed here with numpy from the written rule.
    import numpy as np

    rows = ecg_rows(40, jitter_us=0.0)
    for r in rows:
        last = r["sample_index_ext"] + SAMPLES - 1
        r["t_anchor_us"] = round(1_000_000 + last * PERIOD_US
                                 * (1 + 300e-6 * last / (40 * 512)) + (last % 7) * 9)
    k = np.array([r["sample_index_ext"] + SAMPLES - 1 for r in rows], float)
    t = np.array([r["t_anchor_us"] for r in rows], float)
    expected = []
    for i in range(len(rows)):
        if k[i] - k[0] < 5120:
            continue
        use = (k[:i] >= k[i] - 5120)
        b, a = np.polyfit(k[:i][use], t[:i][use], 1)
        expected.append(abs(t[i] - (a + b * k[i])))
    s = only(a10.check(rows))
    assert s["packets_scored"] == len(expected) and s["packets_flagged"] == 0
    assert s["max_abs_residual_us"] == pytest.approx(max(expected), abs=1e-3)


def test_bad_parameters_are_refused():
    with pytest.raises(ValueError):
        a10.check([], window_us=0)
    with pytest.raises(ValueError):
        a10.check([], limit_us=-1)


def test_script_refuses_raw_root_and_existing_output(tmp_path):
    raw = tmp_path / "data" / "raw"
    raw.mkdir(parents=True)
    with pytest.raises(ValueError, match="data/raw"):
        script.check_output(raw / "x.json", raw_root=raw)
    existing = tmp_path / "out.json"
    existing.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(ValueError, match="exists"):
        script.check_output(existing, raw_root=raw)


def test_classify_gives_each_row_its_own_state_even_for_duplicates():
    rows = ecg_rows(15, start_seq=0)
    # A duplicate of a warm-up packet (same seq) and one of a later packet.
    dup_warm = {**rows[5], "disposition": "duplicate", "chain_id": None}
    dup_late = {**rows[400], "disposition": "duplicate", "chain_id": None}
    packets = rows + [dup_warm, dup_late] + ecg_rows(1, channel="0xF1")
    states = a10.classify(packets)
    assert len(states) == len(packets)
    assert states[5] == "not_yet_scored" and states[400] == "scored"
    assert states[len(rows)] == "not_scored" and states[len(rows) + 1] == "not_scored"
    assert states[-1] is None  # not ECG
