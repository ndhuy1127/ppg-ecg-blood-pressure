# Week 8 — Device Session Ingest Verification

## Environment
- Branch: dev/ngoclinh
- Source: SYNTHETIC ECG/PPG
- Input: runs/linh_device_demo_01/rec
- Output: runs/linh_device_ingest_01

## Automated tests
- test_device_ingest.py
- test_device_features.py
- Result: 33 passed in 11.60s

## Pipeline results
- Cuff events: 1
- Window samples: 66719
- PAT ground truth: 200 ms
- Estimated PAT: 201.186605 ms
- Absolute PAT error: 1.186605 ms
- Valid PAT count: 34
- Flags: none
- Session summary: generated
- Provenance: generated

## Conclusion
The SYNTHETIC session was ingested successfully.
The pipeline generated timebase, window samples,
session summary, provenance and cuff features.

PAT acceptance against the locked quantization
tolerance remains to be reviewed by Huy.

These results do not establish validity on real
hardware or human participants.
