"""MAX30101 timing constants shared by the device ingest and the SYNTHETIC generator.

Taken from the datasheet, not from any recording, so the ingest does not depend on
the SYNTHETIC module (moved here 2026-11-15). The slot spacing is checked on the
bench by acceptance criterion A4 (hardware/test_reports/sync_10min_test_plan.md);
until then it is a datasheet value.
"""

# LED_PW code -> spacing between rising edges of consecutive slots, us
# (Packet Schema V0.1 section 7: MAX30101 p. 22, Table 11).
SLOT_SPACING_US = {0: 427, 1: 525, 2: 720, 3: 1107}
