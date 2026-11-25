"""Build settings of the firmware: PlatformIO envs and the board header guards.

Answers come from firmware/README.md (section "Bản build", decided 2026-10-29):
esp32s3_devkitc_all_real builds the three real chips with the SAMP capture, bit 8
off (BOARD_SAMP_VERIFIED=0), no sync stimulus and no fault injection; sync10 adds
BOARD_SAMP_VERIFIED=1 and BOARD_STIM=1. Values measured at bring-up are passed at
build time (PLATFORMIO_BUILD_FLAGS), so the board header refuses a SAMP polarity
other than 0/1 and an LED pulse width other than 411/215 us instead of the driver
silently taking 411. The header check compiles with a host C compiler and is
skipped without one; the PlatformIO build itself is not run here.
"""

import configparser
import os
import subprocess
from pathlib import Path

import pytest

from tests.test_firmware_c_encoder import _compiler

ROOT = Path(__file__).resolve().parents[1]
FAULT_FLAGS = ("FAKE_IMU_STALLS", "FAKE_SAMP_FAULTS", "FAKE_PPG_DELAY", "BOARD_STIM")


def env_flags(name):
    ini = configparser.ConfigParser()
    ini.read(ROOT / "firmware/platformio.ini", encoding="utf-8")
    flags = {}
    for flag in ini[f"env:{name}"].get("build_flags", "").split():
        key, _, value = flag.removeprefix("-D").partition("=")
        flags[key] = value
    return ini, flags


def test_all_real_env():
    ini, flags = env_flags("esp32s3_devkitc_all_real")
    assert ini["env:esp32s3_devkitc_all_real"]["extends"] == "env:esp32s3_devkitc"
    assert flags == {"BOARD_ECG_REAL": "1", "BOARD_SAMP_CAPTURE": "1",
                     "BOARD_SAMP_VERIFIED": "0", "BOARD_PPG_REAL": "1",
                     "BOARD_IMU_REAL": "1"}
    assert not set(FAULT_FLAGS) & set(flags)
    # The bring-up values are never fixed in an env: they come at build time.
    for section in ini.sections():
        if section.startswith("env:"):
            fixed = set(env_flags(section.removeprefix("env:"))[1])
            assert not {"BOARD_SAMP_RISING_EDGE", "BOARD_PPG_LED_PW_US"} & fixed, section


def test_pll_diag_env_is_ecg_real_plus_diag_and_only_there():
    _, ecg_real = env_flags("esp32s3_devkitc_ecg_real")
    _, diag = env_flags("esp32s3_devkitc_ecg_pll_diag")
    assert diag == {**ecg_real, "BOARD_ECG_PLL_DIAG": "1"}
    assert diag.get("BOARD_SAMP_VERIFIED", "0") == "0"
    ini, _ = env_flags("esp32s3_devkitc")
    for section in ini.sections():
        if section.startswith("env:") and section != "env:esp32s3_devkitc_ecg_pll_diag":
            assert "BOARD_ECG_PLL_DIAG" not in env_flags(section.removeprefix("env:"))[1]


def test_fifo_envs_differ_from_samp_builds_only_by_the_fifo_mode():
    _, ecg_fifo = env_flags("esp32s3_devkitc_ecg_fifo")
    _, all_fifo = env_flags("esp32s3_devkitc_all_real_fifo")
    _, sync_fifo = env_flags("esp32s3_devkitc_sync_fifo")
    _, all_real = env_flags("esp32s3_devkitc_all_real")
    assert ecg_fifo == {"BOARD_ECG_REAL": "1", "BOARD_ECG_FIFO_MODE": "1"}
    # all_real without the SAMP capture, with the FIFO mode.
    expected = {k: v for k, v in all_real.items() if k != "BOARD_SAMP_CAPTURE"}
    assert all_fifo == {**expected, "BOARD_ECG_FIFO_MODE": "1"}
    assert all_fifo["BOARD_SAMP_VERIFIED"] == "0"
    assert sync_fifo == {**all_fifo, "BOARD_STIM": "1"}
    assert not set(FAULT_FLAGS) & set(all_fifo)


def test_samp_bench_env_is_ecg_real_with_bit8_off_and_only_there():
    # Sync test plan 11.8 (2026-11-23): a bench tool, ECG alone, bit 8 off.
    _, ecg_real = env_flags("esp32s3_devkitc_ecg_real")
    _, bench = env_flags("esp32s3_devkitc_ecg_samp_bench")
    assert bench == {**ecg_real, "BOARD_SAMP_VERIFIED": "0", "BOARD_ECG_SAMP_BENCH": "1"}
    assert not set(FAULT_FLAGS) & set(bench)
    ini, _ = env_flags("esp32s3_devkitc")
    for section in ini.sections():
        if section.startswith("env:") and section != "env:esp32s3_devkitc_ecg_samp_bench":
            assert "BOARD_ECG_SAMP_BENCH" not in env_flags(section.removeprefix("env:"))[1]


def test_sync10_env_is_all_real_plus_verified_samp_and_stimulus():
    _, all_real = env_flags("esp32s3_devkitc_all_real")
    _, sync10 = env_flags("esp32s3_devkitc_sync10")
    assert sync10 == {**all_real, "BOARD_SAMP_VERIFIED": "1", "BOARD_STIM": "1"}


@pytest.fixture(scope="module")
def compiler():
    cc = _compiler()
    if cc is None:
        pytest.skip("no host C compiler ($CC, cc, gcc or clang)")
    return cc


@pytest.mark.parametrize("flags,builds", [
    ((), True),
    (("-DBOARD_PPG_LED_PW_US=411",), True),
    (("-DBOARD_PPG_LED_PW_US=215",), True),
    (("-DBOARD_PPG_LED_PW_US=118",), False),
    (("-DBOARD_PPG_LED_PW_US=251",), False),
    (("-DBOARD_SAMP_RISING_EDGE=0",), True),
    (("-DBOARD_SAMP_RISING_EDGE=1",), True),
    (("-DBOARD_SAMP_RISING_EDGE=2",), False),
    (("-DBOARD_SAMP_RISING_EDGE=1", "-DBOARD_PPG_LED_PW_US=215"), True),
])
def test_board_header_refuses_unknown_bring_up_values(compiler, tmp_path, flags, builds):
    source = tmp_path / "board.c"
    source.write_text('#include "board_v1_module.h"\n'
                      "int pw = BOARD_PPG_LED_PW_US, edge = BOARD_SAMP_RISING_EDGE;\n",
                      encoding="utf-8")
    out = tmp_path / ("board.obj" if os.name == "nt" else "board.o")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-c",
         "-I", str(ROOT / "firmware/boards"), *flags, str(source), "-o", str(out)],
        capture_output=True, text=True,
    )
    assert (build.returncode == 0) == builds, build.stderr
    if not builds:
        assert "must be" in build.stderr


@pytest.mark.parametrize("flags,builds", [
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1"), True),
    (("-DBOARD_ECG_FIFO_MODE=1",), False),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1", "-DBOARD_SAMP_CAPTURE=1"), False),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1", "-DBOARD_SAMP_VERIFIED=1"), False),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1", "-DBOARD_SAMP_VERIFIED=0"), True),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1", "-DBOARD_ECG_PLL_DIAG=1"), False),
])
def test_board_header_guards_the_fifo_mode(compiler, tmp_path, flags, builds):
    source = tmp_path / "board.c"
    source.write_text('#include "board_v1_module.h"\nint fifo = BOARD_ECG_FIFO_MODE;\n',
                      encoding="utf-8")
    out = tmp_path / ("board.obj" if os.name == "nt" else "board.o")
    build = subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-c",
         "-I", str(ROOT / "firmware/boards"), *flags, str(source), "-o", str(out)],
        capture_output=True, text=True,
    )
    assert (build.returncode == 0) == builds, build.stderr
    if not builds:
        assert "BOARD_ECG_FIFO_MODE" in build.stderr


BENCH = ("-DBOARD_ECG_REAL=1", "-DBOARD_SAMP_CAPTURE=1", "-DBOARD_ECG_SAMP_BENCH=1")


@pytest.mark.parametrize("flags,builds,count_only", [
    (BENCH, True, 1),
    ((*BENCH, "-DBOARD_SAMP_VERIFIED=0"), True, 1),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_SAMP_BENCH=1"), False, None),
    (("-DBOARD_SAMP_CAPTURE=1", "-DBOARD_ECG_SAMP_BENCH=1"), False, None),
    ((*BENCH, "-DBOARD_SAMP_VERIFIED=1"), False, None),
    ((*BENCH, "-DBOARD_ECG_FIFO_MODE=1"), False, None),
    ((*BENCH, "-DBOARD_ECG_PLL_DIAG=1"), False, None),
    ((*BENCH, "-DBOARD_SAMP_RISING_EDGE=1"), False, None),
    ((*BENCH, "-DBOARD_SAMP_RISING_EDGE=0"), True, 1),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_ECG_FIFO_MODE=1"), True, 1),
    (("-DBOARD_ECG_REAL=1", "-DBOARD_SAMP_CAPTURE=1", "-DBOARD_ECG_INT_SHORTED=0"), True, 0),
])
def test_board_header_guards_the_samp_bench_mode(compiler, tmp_path, flags, builds,
                                                  count_only):
    source = tmp_path / "board.c"
    source.write_text('#include "board_v1_module.h"\n'
                      "_Static_assert(BOARD_ECG_PLLINT_COUNT_ONLY == EXPECTED, \"count\");\n"
                      "int bench = BOARD_ECG_SAMP_BENCH;\n",
                      encoding="utf-8")
    out = tmp_path / ("board.obj" if os.name == "nt" else "board.o")
    expected = f"-DEXPECTED={count_only if count_only is not None else 0}"
    build = subprocess.run(
        [*compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-c",
         "-I", str(ROOT / "firmware/boards"), *flags, expected, str(source), "-o", str(out)],
        capture_output=True, text=True,
    )
    assert (build.returncode == 0) == builds, build.stderr
    if not builds:
        assert "BOARD_ECG_SAMP_BENCH" in build.stderr


# Envs that enable both interrupt outputs (INTB = EINT, INT2B = SAMP): refused by
# default since INTB and INT2B are shorted on the breakout v2 03/24 (bring-up
# report 9.8), built only with -DBOARD_ECG_INT_SHORTED=0.
BOTH_OUTPUTS = {"esp32s3_devkitc_ecg_real", "esp32s3_devkitc_ecg_pll_diag",
                "esp32s3_devkitc_all_real", "esp32s3_devkitc_sync10"}


def _header_build(compiler, tmp_path, flags):
    source = tmp_path / "board.c"
    source.write_text('#include "board_v1_module.h"\nint shorted = BOARD_ECG_INT_SHORTED;\n',
                      encoding="utf-8")
    out = tmp_path / ("board.obj" if os.name == "nt" else "board.o")
    return subprocess.run(
        [*compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-c",
         "-I", str(ROOT / "firmware/boards"), *flags, str(source), "-o", str(out)],
        capture_output=True, text=True,
    )


def _all_envs():
    ini, _ = env_flags("esp32s3_devkitc")
    return [s.removeprefix("env:") for s in ini.sections() if s.startswith("env:")]


def test_both_output_envs_are_the_real_ecg_envs_outside_the_one_output_modes():
    for name in _all_envs():
        flags = env_flags(name)[1]
        both = (flags.get("BOARD_ECG_REAL") == "1"
                and flags.get("BOARD_ECG_FIFO_MODE") != "1"
                and flags.get("BOARD_ECG_SAMP_BENCH") != "1")
        assert both == (name in BOTH_OUTPUTS), name


@pytest.mark.parametrize("name", _all_envs())
def test_board_header_refuses_both_outputs_unless_the_pins_are_separate(
        compiler, tmp_path, name):
    flags = [f"-D{k}={v}" if v else f"-D{k}" for k, v in env_flags(name)[1].items()]
    build = _header_build(compiler, tmp_path, flags)
    assert (build.returncode == 0) == (name not in BOTH_OUTPUTS), build.stderr
    if name in BOTH_OUTPUTS:
        assert "BOARD_ECG_INT_SHORTED" in build.stderr
    separate = _header_build(compiler, tmp_path, [*flags, "-DBOARD_ECG_INT_SHORTED=0"])
    assert separate.returncode == 0, separate.stderr


def test_board_header_refuses_an_unknown_shorted_value(compiler, tmp_path):
    build = _header_build(compiler, tmp_path, ["-DBOARD_ECG_INT_SHORTED=2"])
    assert build.returncode != 0 and "must be 0 or 1" in build.stderr
