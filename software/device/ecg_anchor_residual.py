"""Per-packet ECG anchor residual check, criterion A10 (ecg-anchor-residual-v1).

Defined in hardware/test_reports/sync_10min_test_plan.md section 11.2 (decided
2026-11-21, before any validation run): for every ECG packet, predict the anchor
of its last sample from a straight line ``T_ANCHOR_US = a + b k`` fitted on the
valid packets of the previous 10 s only (past data, same chain); a packet whose
|measured - predicted| anchor exceeds 0.5 ms is flagged, the chain is cut, and
scoring starts again only once 10 s of valid packets have built up after it.

Choices that the plan leaves open, fixed here before any validation data:

- "Valid packets" are a continuous run of samples with a reliable anchor
  (disposition ``accepted``). A new chain, a change of anchor source (SAMP edge
  or FIFO read), any sample missing before a packet (lost or quarantined
  packets), and a packet whose anchor is unreliable (STATUS bit 0 or V0.2 bit 7)
  all start a new 10 s history, so a line is never fitted across a hole.
- "10 s" is measured on the sample index at the nominal rate of the packet, not
  on the anchor being tested, so a bad anchor cannot decide whether it is tested:
  a packet is scored when its last sample is at least 10 s of samples after the
  last sample of the first packet of its history, and the line uses the packets
  whose last sample is at most 10 s of samples before it.

Inputs are the ``packets.csv`` rows of a logger recording, as read by
``session_ingest.load_recording`` (integers already parsed). Pure function: no
file access, no printing. Sums are kept in exact integers and the residual is an
exact fraction, so long recordings do not lose precision.
"""

import math
from collections import deque
from fractions import Fraction

VERSION = "ecg-anchor-residual-v1"
ECG_KEY = "0xE1"
WINDOW_US = 10_000_000
LIMIT_US = 500
SAMP_ANCHOR_BIT = 1 << 8
KEPT_DISPOSITIONS = ("accepted", "accepted_anchor_unreliable")


class _Window:
    """Sliding least-squares line over (k, t) points, in exact integers."""

    def __init__(self):
        self.points = deque()
        self.n = self.sk = self.st = self.skk = self.skt = 0

    def add(self, k, t):
        self.points.append((k, t))
        self.n += 1
        self.sk += k
        self.st += t
        self.skk += k * k
        self.skt += k * t

    def drop_older(self, k_now, span_samples):
        """Keep the points whose index is at most ``span_samples`` before k_now."""
        while self.points and k_now - self.points[0][0] > span_samples:
            k, t = self.points.popleft()
            self.n -= 1
            self.sk -= k
            self.st -= t
            self.skk -= k * k
            self.skt -= k * t

    def predict(self, k):
        """Fitted anchor at index ``k``; None when the line is not defined."""
        den = self.n * self.skk - self.sk * self.sk
        if self.n < 2 or den == 0:
            return None
        slope = Fraction(self.n * self.skt - self.sk * self.st, den)
        return (self.st + slope * (self.n * k - self.sk)) / self.n


def _segment_key(row):
    """Rows that may share one line: same session, wire version, chain and anchor
    source (SAMP edges and FIFO reads have an unknown offset between them)."""
    return (row["session_id"], row["version"], row["chain_id"],
            bool(row["status"] & SAMP_ANCHOR_BIT))


def _verdict(flagged, scored):
    if flagged:
        return False
    return True if scored else None


def check(packets, window_us=WINDOW_US, limit_us=LIMIT_US):
    """Run A10 on the ECG packets of one recording.

    Returns a dict: ``method``, ``window_us``, ``limit_us``, ``sessions`` (one
    entry per (session_id, version) with ECG packets: counts of packets scored,
    not yet scored (under 10 s of history), not scored (unreliable anchor or not
    kept by the logger), flagged; the largest |residual| and its nearest-rank
    99th percentile over scored packets, in us; the flagged packets; and
    ``passed``: False with any flagged packet, None when nothing was scored, else
    True) and ``passed`` over all sessions (False if any session is False, else
    None if any is None or there is no ECG packet, else True).
    """
    if window_us <= 0 or limit_us <= 0:
        raise ValueError("window_us and limit_us must be positive")
    ecg = [p for p in packets if p["channel_id"] == ECG_KEY]
    sessions = {}
    for row in sorted(ecg, key=lambda p: (p["session_id"], p["version"], p["seq_ext"])):
        key = (row["session_id"], row["version"])
        state = sessions.setdefault(key, {
            "segment": None, "window": _Window(), "start_k": None, "next_index": None,
            "scored": 0, "warmup": 0, "not_scored": 0, "flags": [], "abs": [],
        })

        def restart():
            state["window"], state["start_k"] = _Window(), None

        if row["disposition"] not in KEPT_DISPOSITIONS or row["sample_index_ext"] is None:
            state["not_scored"] += 1
            continue
        segment = _segment_key(row)
        if segment != state["segment"] or row["sample_index_ext"] != state["next_index"]:
            state["segment"] = segment
            restart()
        state["next_index"] = row["sample_index_ext"] + row["sample_count"]
        if row["disposition"] != "accepted":
            state["not_scored"] += 1
            restart()
            continue
        k = row["sample_index_ext"] + row["sample_count"] - 1
        t = row["t_anchor_us"]
        # 10 s in samples at the nominal rate (FS_NOMINAL_MHZ in millihertz).
        span = Fraction(window_us * row["fs_nominal_mhz"], 10 ** 9)
        window = state["window"]
        window.drop_older(k, span)
        ready = state["start_k"] is not None and k - state["start_k"] >= span
        predicted = window.predict(k) if ready else None
        if predicted is None:
            state["warmup"] += 1
        else:
            residual = t - predicted
            state["scored"] += 1
            state["abs"].append(abs(residual))
            if abs(residual) > limit_us:
                state["flags"].append({"seq_ext": row["seq_ext"],
                                       "chain_id": row["chain_id"],
                                       "last_sample_index": k,
                                       "residual_us": round(float(residual), 3)})
                # Cut: the next valid packet starts a new line.
                restart()
                continue
        if state["start_k"] is None:
            state["start_k"] = k
        window.add(k, t)
    out = []
    for (session_id, version), state in sorted(sessions.items()):
        values = sorted(state["abs"])
        out.append({
            "session_id": session_id, "version": version,
            "packets_scored": state["scored"],
            "packets_not_yet_scored": state["warmup"],
            "packets_not_scored": state["not_scored"],
            "packets_flagged": len(state["flags"]),
            "max_abs_residual_us": round(float(values[-1]), 3) if values else None,
            # Nearest-rank 99th percentile.
            "p99_abs_residual_us": (round(float(values[math.ceil(0.99 * len(values)) - 1]),
                                          3) if values else None),
            "flagged": state["flags"],
            "passed": _verdict(state["flags"], state["scored"]),
        })
    verdicts = [s["passed"] for s in out]
    passed = (False if False in verdicts else None if (None in verdicts or not out)
              else True)
    return {"method": VERSION, "window_us": window_us, "limit_us": limit_us,
            "sessions": out, "passed": passed}
