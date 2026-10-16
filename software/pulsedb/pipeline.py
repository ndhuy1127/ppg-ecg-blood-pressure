
import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from software.pulsedb.reader import PulseDBReader
from software.pulsedb.features import extract_features
from software.pulsedb.train import train_models, save_models
from software.pulsedb.evaluate import build_metrics_table


def run_pipeline(data_path, manifest_path, output_dir):
    """Run feature extraction, training and evaluation."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read manifest and validate its structure
    manifest = pd.read_csv(manifest_path)

    required_columns = {"sample_id", "subject_id", "split"}
    missing_columns = required_columns - set(manifest.columns)

    if missing_columns:
        raise ValueError(
            f"Manifest thiếu các cột: {sorted(missing_columns)}"
        )

    if manifest.empty:
        raise ValueError("Manifest không có mẫu")

    if manifest["sample_id"].duplicated().any():
        raise ValueError("Manifest có sample_id bị trùng")

    manifest = manifest.sort_values("sample_id").reset_index(drop=True)

    if not manifest["split"].isin(["train", "val", "test"]).all():
        raise ValueError("Manifest chứa split không hợp lệ")

    n_samples = len(manifest)

    expected_ids = list(range(n_samples))
    if manifest["sample_id"].tolist() != expected_ids:
        raise ValueError("sample_id phải liên tục từ 0 đến N-1")

    if manifest["subject_id"].isna().any():
        raise ValueError("Manifest có subject_id bị thiếu")

    # 2. Read source data
    all_segments = PulseDBReader(data_path).read()

    if len(all_segments) == 0:
        raise ValueError("Reader không đọc được segment nào")

    # Select up to 10 segments per subject, matching the notebook.
    by_subject = defaultdict(list)

    for segment in all_segments:
        if len(by_subject[segment.subject_id]) < 10:
            by_subject[segment.subject_id].append(segment)

    selected_segments = []

    for subject_id, subject_segments in by_subject.items():
        if len(subject_segments) == 10:
            selected_segments.extend(subject_segments)

        if len(selected_segments) >= n_samples:
            break

    segments = selected_segments[:n_samples]

    if len(segments) != n_samples:
        raise ValueError(
            f"Chỉ chọn được {len(segments)} segment, "
            f"nhưng manifest có {n_samples} dòng"
        )

    # Ensure source segments align with manifest rows
    reader_subjects = [
        str(segment.subject_id) for segment in segments
    ]
    manifest_subjects = (
        manifest["subject_id"].astype(str).tolist()
    )

    if reader_subjects != manifest_subjects:
        raise ValueError(
            "subject_id trong manifest không khớp với các segment "
            "được chọn từ reader. Không train để tránh ghép sai mẫu."
        )

    # 3. Validate subject-level split leakage
    subject_splits = manifest.groupby("subject_id")["split"].nunique()

    if (subject_splits > 1).any():
        raise ValueError(
            "Phát hiện subject_id xuất hiện ở nhiều split"
        )

    for split_name in ("train", "val", "test"):
        if not manifest["split"].eq(split_name).any():
            raise ValueError(f"Tập {split_name} không có mẫu")

    # 4. Extract ECG/PPG features and labels
    X = pd.DataFrame(
        [extract_features(segment) for segment in segments]
    )

    y_sbp = np.array(
        [segment.sbp for segment in segments], dtype=float
    )
    y_dbp = np.array(
        [segment.dbp for segment in segments], dtype=float
    )

    if X.empty or X.shape[1] == 0:
        raise ValueError("Không trích xuất được đặc trưng")

    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise ValueError("Features chứa NaN hoặc infinity")

    if not np.isfinite(y_sbp).all() or not np.isfinite(y_dbp).all():
        raise ValueError("SBP/DBP chứa NaN hoặc infinity")

    # 5. Train using training split only
    train_mask = manifest["split"].eq("train").to_numpy()

    model_sbp, model_dbp = train_models(
        X,
        y_sbp,
        y_dbp,
        train_mask,
        random_state=42,
    )

    # 6. Evaluate validation and test splits
    metric_tables = []

    for split_name in ("val", "test"):
        mask = manifest["split"].eq(split_name).to_numpy()

        pred_sbp = model_sbp.predict(X.loc[mask])
        pred_dbp = model_dbp.predict(X.loc[mask])

        metrics = build_metrics_table(
            y_sbp[mask],
            pred_sbp,
            y_dbp[mask],
            pred_dbp,
            split_name,
        )
        metric_tables.append(metrics)

    # 7. Save models and results
    save_models(model_sbp, model_dbp, output_dir)

    metrics_table = pd.concat(metric_tables, ignore_index=True)
    metrics_table.to_csv(output_dir / "metrics.csv", index=False)
    X.to_csv(output_dir / "features.csv", index=False)

    print("\nPipeline hoàn thành!")
    print(f"Số mẫu: {len(segments)}")
    print(f"Số đặc trưng: {X.shape[1]}")
    print(f"Kết quả đã lưu tại: {output_dir}")
    print(metrics_table.to_string(index=False))

    return model_sbp, model_dbp, metrics_table


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data",
        required=True,
        help="Đường dẫn file .mat",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Đường dẫn manifest CSV",
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Thư mục lưu model và kết quả",
    )

    args = parser.parse_args()

    run_pipeline(args.data, args.manifest, args.output)
