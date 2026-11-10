"""Logger memory fixes of 2026-11-07 (review of the same day), SYNTHETIC only.

DATA is kept as int32 bytes (DataWords), accepted samples as one block per
packet (SampleBlocks), rows with slots, outputs written line by line, and
record keeps no packet while capturing. Answers: the decode outputs must be the
bytes of the plain algorithm they replace (a sample tuple each, one sort, one
joined string), written here independently; CRC-16/CCITT-FALSE has the published
check value 0x29B1.
"""

import hashlib
import json
import random
from pathlib import Path

import pytest

from scripts import packet_logger
from scripts.packet_logger import record, replay
from software.data_io import packet_receiver
from software.data_io.command_desk import CommandDesk
from software.data_io.packet_receiver import (
    PACKET_COLUMNS, SAMPLE_COLUMNS, SampleBlocks, analyze_stream, json_bytes,
    render_outputs, write_outputs,
)
from software.data_io.packet_simulation_v3 import (
    CASES, V02_CASES, generate_stream, session_metadata,
)
from software.data_io.packet_wire import (
    HEADER, SYNC, DataWords, Packet, StreamDecoder, crc16_ccitt_false, decode_bytes,
    encode_packet,
)

ROOT = Path(__file__).resolve().parents[1]
LOGGER_CONFIG = ROOT / "configs/hardware/packet_logger.json"
SIM_V01 = ROOT / "configs/hardware/packet_simulation_v3.json"
SIM_V02 = ROOT / "configs/hardware/packet_simulation_v3_v02.json"


def logger():
    return json.loads(LOGGER_CONFIG.read_bytes())


def bitwise_crc(payload):
    """CRC-16/CCITT-FALSE bit by bit: poly 0x1021, init 0xFFFF, no reflection."""
    crc = 0xFFFF
    for byte in payload:
        crc ^= byte << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def test_crc_check_value_and_a_bitwise_reference():
    assert crc16_ccitt_false(b"123456789") == 0x29B1
    rng = random.Random(7)
    for _ in range(200):
        payload = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 200)))
        assert crc16_ccitt_false(payload) == bitwise_crc(payload)
        assert crc16_ccitt_false(bytearray(payload)) == bitwise_crc(payload)


def test_data_words_behave_like_the_tuple_of_their_values():
    values = (0, -1, 2 ** 31 - 1, -(2 ** 31), 262143)
    words = DataWords(b"".join(v.to_bytes(4, "little", signed=True) for v in values))
    assert len(words) == 5 and tuple(words) == values and list(words) == list(values)
    assert words[0] == 0 and words[-1] == 262143 and words[1:3] == (-1, 2 ** 31 - 1)
    assert words == values and values == words and hash(words) == hash(values)
    assert words != list(values) and words != values[:4]
    with pytest.raises(IndexError):
        words[5]
    with pytest.raises(ValueError):
        DataWords(b"\x00" * 6)


def test_decoded_packets_keep_data_as_bytes_and_equal_the_sent_packet():
    sent = Packet(2, 0xF1, 9, 3, 48, 2_000_000, 1_925_000, 200_000, 0,
                  (1, 262143, 5, 70000))
    item = decode_bytes(encode_packet(sent), supported_versions=(2,))[0][0]
    assert isinstance(item.packet.data, DataWords)
    assert item.packet == sent and hash(item.packet) == hash(sent)
    assert encode_packet(item.packet) == encode_packet(sent)


def test_sample_blocks_order_is_the_sample_sort_even_with_overlaps():
    rng = random.Random(11)
    for _ in range(50):
        blocks, plain = SampleBlocks(), []
        for session in rng.sample(range(1, 6), 2):
            for version in (1, 2):
                for key in ("0xE1", "0xF1", "0xA1"):
                    seq, index = 0, rng.randrange(100)
                    for chain in range(rng.randrange(1, 3)):
                        for _ in range(rng.randrange(1, 6)):
                            seq += rng.randrange(1, 3)
                            # Mostly contiguous; sometimes an overlap or a gap.
                            index += rng.choice((0, 0, 0, -3, 5))
                            data = tuple(rng.randrange(-9, 9)
                                         for _ in range(rng.randrange(1, 5)))
                            blocks.add(session, version, key, chain, index, seq, data)
                            plain += [(session, key, chain, seq, index + i, v, version)
                                      for i, v in enumerate(data)]
                            index += len(data)
        assert list(blocks) == plain and len(blocks) == len(plain)
        assert list(blocks.ordered()) == sorted(
            plain, key=lambda s: (s[0], s[6], s[1], s[2], s[4]))


def reference_outputs(result, rows, samples):
    """The bytes the logger wrote before 2026-11-07, computed the plain way."""
    def csv(columns, lines):
        text = [",".join(columns)] + [
            ",".join("" if value is None else str(value) for value in line)
            for line in lines]
        return ("\n".join(text) + "\n").encode("utf-8")

    ordered = sorted(samples, key=lambda s: (s[0], s[6], s[1], s[2], s[4]))
    return {"decode.json": json_bytes(result),
            "packets.csv": csv(PACKET_COLUMNS,
                               [[row[name] for name in PACKET_COLUMNS] for row in rows]),
            "samples.csv": csv(SAMPLE_COLUMNS, ordered)}


OLD = json.loads((ROOT / "tests/fixtures/packet_outputs_a7e0ea1.json").read_bytes())
SIM_TAGS = {"v01": SIM_V01, "v02": SIM_V02,
            "v02temp": ROOT / "configs/hardware/packet_simulation_v3_v02_temp.json"}


@pytest.mark.parametrize("name", sorted(OLD["hashes"]))
def test_outputs_equal_those_of_the_code_before_the_change(name):
    # Hashes written by the code at a7e0ea1 (fixture "derivation"): independent of
    # the analyzer under test, unlike the next test.
    tag, case = name.split("_", 1)
    damaged = case.endswith("_damaged")
    case = case.removesuffix("_damaged")
    sim = json.loads(SIM_TAGS[tag].read_bytes())
    stream, _ = generate_stream(sim, case)
    if damaged:
        rng, flipped = random.Random(len(f"{tag}_{case}")), bytearray(stream)
        for _ in range(max(1, len(flipped) // 3000)):
            flipped[rng.randrange(len(flipped))] ^= 1 << rng.randrange(8)
        stream = bytes(flipped)
    config = logger()
    packets, decoder = decode_bytes(stream, config["read_chunk_bytes"],
                                    config["wire_versions"])
    outputs = render_outputs(*analyze_stream(packets, decoder, config,
                                             session_metadata(sim, case, "0" * 64)))
    assert {k: hashlib.sha256(v).hexdigest() for k, v in outputs.items()} == (
        OLD["hashes"][name])


def test_the_fixture_covers_every_case():
    expected = {f"{tag}_{case}{suffix}"
                for tag, cases in (("v01", CASES), ("v02", (*CASES, *V02_CASES)),
                                   ("v02temp", (*CASES, *V02_CASES[2:])))
                for case in cases for suffix in ("", "_damaged")}
    assert set(OLD["hashes"]) == expected


@pytest.mark.parametrize("sim_path, case", [
    *((SIM_V01, case) for case in CASES),
    *((SIM_V02, case) for case in (*CASES, *V02_CASES)),
])
def test_outputs_equal_the_plain_algorithm(sim_path, case, tmp_path, monkeypatch):
    # Batches of 3 lines, so that every batch boundary of the writer is crossed.
    monkeypatch.setattr(packet_receiver, "_LINES_PER_WRITE", 3)
    sim = json.loads(sim_path.read_bytes())
    stream, _ = generate_stream(sim, case)
    config = logger()
    packets, decoder = decode_bytes(stream, config["read_chunk_bytes"],
                                    config["wire_versions"])
    result, rows, samples = analyze_stream(packets, decoder, config,
                                           session_metadata(sim, case, "0" * 64))
    rendered = render_outputs(result, rows, samples)
    assert rendered == reference_outputs(result, rows, list(samples))
    hashes = write_outputs(result, rows, samples,
                           lambda name: (tmp_path / name).open("xb"))
    for name, payload in rendered.items():
        assert (tmp_path / name).read_bytes() == payload
        assert hashes[name] == hashlib.sha256(payload).hexdigest()


class Trickle:
    """A byte source that returns pieces of 1 to 97 bytes."""

    def __init__(self, payload, seed=3):
        self.payload, self.rng = payload, random.Random(seed)

    def read(self, n):
        size = min(n, self.rng.randrange(1, 98))
        chunk, self.payload = self.payload[:size], self.payload[size:]
        return chunk


def stream_and_metadata(tmp_path, case="crc"):
    sim = json.loads(SIM_V02.read_bytes())
    stream, _ = generate_stream(sim, case)
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps(session_metadata(sim, case, "0" * 64)), encoding="utf-8")
    return stream, meta


def read_csv(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.split(",") for line in lines[1:]]


def test_record_in_small_reads_times_each_packet_by_the_read_of_its_last_byte(
        tmp_path):
    stream, meta = stream_and_metadata(tmp_path)
    out = tmp_path / "rec"
    manifest = record(Trickle(stream), out, LOGGER_CONFIG, meta, ROOT, "trickle")
    chunks = [(int(c[1]), int(c[2]), int(c[3])) for c in read_csv(out / "rx_chunks.csv")]
    assert sum(size for _, size, _ in chunks) == len(stream) == manifest["raw"]["bytes"]
    sizes = {item.offset: item.size for item in decode_bytes(stream,
                                                             supported_versions=(1, 2))[0]}
    rows = read_csv(out / "t_rx_packets.csv")
    assert len(rows) == len(sizes)
    for offset, _, _, _, chunk, t_rx in rows:
        start, size, received = chunks[int(chunk)]
        assert start <= int(offset) + sizes[int(offset)] - 1 < start + size
        assert int(t_rx) == received
    # The stored files hash as the manifest says, and a replay matches it.
    for name, digest in manifest["outputs_sha256"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest
    report = replay(out / "raw.bin", tmp_path / "replay", LOGGER_CONFIG, meta, ROOT,
                    out / "session_manifest.json")
    assert report["expected_manifest"]["mismatches"] == []
    assert report["raw"]["bytes"] == len(stream)


def test_record_stops_when_the_offline_decode_or_the_stored_raw_differs(
        tmp_path, monkeypatch):
    stream, meta = stream_and_metadata(tmp_path, "valid")
    real = packet_logger._decode_file

    def other_digest(path, config):
        packets, decoder, _, sha256, size = real(path, config)
        return packets, decoder, "0" * 64, sha256, size

    def other_bytes(path, config):
        packets, decoder, digest, _, size = real(path, config)
        return packets, decoder, digest, "0" * 64, size

    for fake, message in ((other_digest, "differs from the live decode"),
                          (other_bytes, "on disk differs")):
        monkeypatch.setattr(packet_logger, "_decode_file", fake)
        out = tmp_path / message.split()[0]
        with pytest.raises(ValueError, match=message):
            record(Trickle(stream), out, LOGGER_CONFIG, meta, ROOT, "trickle")
        assert not (out / "session_manifest.json").exists()
        assert (out / "raw.bin").read_bytes() == stream


def test_dc_lines_need_somewhere_to_go(tmp_path):
    stream, meta = stream_and_metadata(tmp_path, "valid")
    with pytest.raises(ValueError, match="needs notify"):
        record(Trickle(stream), tmp_path / "rec", LOGGER_CONFIG, meta, ROOT, "x",
               dc_every_s=2.0)


class WritableTrickle(Trickle):
    """A Trickle that also takes command bytes (record --commands)."""

    def write(self, data):
        return len(data)


def test_record_with_small_csv_batches_and_a_packet_only_finish_recovers(
        tmp_path, monkeypatch):
    monkeypatch.setattr(packet_logger, "CSV_LINES_PER_WRITE", 2)
    stream, meta = stream_and_metadata(tmp_path, "valid")
    # A SYNC whose header claims 32 samples (170 bytes) that never come, then a
    # real event packet: the decoder waits on the first until the end, so only
    # finish() gives the event.
    fake = HEADER.pack(SYNC, 2, 0xF1, 0, 0, 0, 0, 0, 0, 32, 0)
    last = Packet(2, 0xC1, 1, 99, 99, 9_000_000, 9_000_000, 0, 0, (4,))
    stream = stream + fake + encode_packet(last)
    decoder = StreamDecoder((1, 2))
    fed = decoder.feed(stream)
    assert [item.packet for item in decoder.finish()] == [last]
    assert not any(item.packet == last for item in fed)
    out = tmp_path / "rec"
    manifest = record(Trickle(stream), out, LOGGER_CONFIG, meta, ROOT, "trickle")
    rows = read_csv(out / "t_rx_packets.csv")
    chunks = read_csv(out / "rx_chunks.csv")
    assert rows[-1][:4] == [str(len(stream) - len(encode_packet(last))), "1", "0xC1",
                            "99"]
    assert int(rows[-1][4]) == len(chunks) - 1  # the read that held its last byte
    assert manifest["issue_counts"].get("truncated_packet") == 1
    report = replay(out / "raw.bin", tmp_path / "replay", LOGGER_CONFIG, meta, ROOT,
                    out / "session_manifest.json")
    assert report["expected_manifest"]["mismatches"] == []


def test_a_failing_cleanup_still_closes_every_capture_file(tmp_path, monkeypatch):
    # Review of 2026-11-07: if the desk failed while closing, the journal and the
    # receive-time files stayed open and their last buffered lines were lost.
    csv_files, desks = [], []
    csv_init, desk_init = packet_logger._CsvOut.__init__, CommandDesk.__init__

    def keep_csv(self, *args):
        csv_init(self, *args)
        csv_files.append(self)

    def keep_desk(self, *args, **kwargs):
        desk_init(self, *args, **kwargs)
        desks.append(self)

    def broken_close(self):
        raise RuntimeError("desk close failed")

    monkeypatch.setattr(packet_logger._CsvOut, "__init__", keep_csv)
    monkeypatch.setattr(CommandDesk, "__init__", keep_desk)
    monkeypatch.setattr(CommandDesk, "close", broken_close)
    stream, meta = stream_and_metadata(tmp_path, "valid")
    out = tmp_path / "rec"
    with pytest.raises(RuntimeError, match="desk close failed"):
        record(WritableTrickle(stream), out, LOGGER_CONFIG, meta, ROOT, "trickle",
               commands=True)
    assert len(csv_files) == 2 and all(f.handle.closed for f in csv_files)
    assert desks[0].journal.closed
    packets = decode_bytes(stream, supported_versions=(1, 2))[0]
    assert len(read_csv(out / "t_rx_packets.csv")) == len(packets)
    assert (out / "raw.bin").read_bytes() == stream
    assert not (out / "session_manifest.json").exists()


class Unplugged(Trickle):
    """The port goes away after a few reads."""

    def __init__(self, payload, reads=5):
        super().__init__(payload)
        self.reads = reads

    def read(self, n):
        self.reads -= 1
        if self.reads < 0:
            raise OSError("port gone")
        return super().read(n)


def test_a_source_error_keeps_what_was_received(tmp_path):
    stream, meta = stream_and_metadata(tmp_path, "valid")
    out = tmp_path / "rec"
    with pytest.raises(OSError, match="port gone"):
        record(Unplugged(stream), out, LOGGER_CONFIG, meta, ROOT, "unplugged")
    raw = (out / "raw.bin").read_bytes()
    assert raw and stream.startswith(raw)
    chunks = read_csv(out / "rx_chunks.csv")
    assert len(chunks) == 5 and sum(int(c[2]) for c in chunks) == len(raw)
    assert not (out / "session_manifest.json").exists()
