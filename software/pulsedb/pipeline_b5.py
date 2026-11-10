"""B5: the 1D ResNet-18 of the PulseDB paper on split v2, beside B0/B3 (val only).

Definition: docs/protocol/b5_pulsedb_definition.md. Pure functions: the caller
opens the raw file and writes outputs. Two modes:

- ``inner``: fit on 90 % of the train subjects and report the inner-validation
  curve on the other 10 %. Val and test rows are never read, so this mode may
  run before the definition is approved (it only checks that training works).
- ``val``: the same fit, then predictions on val and B0/B3 refitted exactly as in
  B3 v1, scored together with paired contrasts on the same bootstrap draws.

Test rows are never read in either mode. Requires PyTorch (requirements-dl.txt).
"""

import copy
import json
import time

import numpy as np
import pandas as pd

from software._bp_validation import subjects
from software.evaluation.subject_bootstrap import (
    BootstrapConfig, evaluate_prediction_table,
)
from software.pulsedb import features, pipeline

VERSION = "b5-pipeline-v0"
PENDING = "PENDING_REVIEW"
APPROVED = "APPROVED_NOT_TEST_EVALUATED"
CONFIG_FIELDS = {
    "schema_version", "status", "unit", "split_sha256", "fit_split", "evaluation_split",
    "b3_feature_set", "label_qc", "train_weighting", "xgboost", "model", "training",
    "bootstrap",
}
MODEL = {"architecture": "resnet18-1d", "input_channels": ["ecg", "ppg"],
         "samples": 1250, "separate_targets": True}
TRAINING_FIELDS = {
    "seed", "inner_val_fraction", "optimizer", "learning_rate", "batch_size",
    "max_epochs", "patience", "loss", "input_scaling", "target_scaling",
    "selection_metric", "eval_batch_size",
}
TRAINING_RULES = {"optimizer": "adam", "loss": "subject_weighted_mse",
                  "input_scaling": "train_fit_channel_standardization",
                  "target_scaling": "train_fit_standardization",
                  "selection_metric": "inner_val_subject_balanced_mae"}
TARGETS = ("SBP", "DBP")
MODELS = ("B0", "B3", "B5")
CONTRASTS = [("B5", "B0"), ("B5", "B3")]


def load_config(payload: bytes) -> dict:
    """Parse and check the run config; unknown or missing fields are rejected."""
    config = json.loads(payload)
    if not isinstance(config, dict) or set(config) != CONFIG_FIELDS:
        raise ValueError("Config must contain exactly the documented fields")
    if config["schema_version"] != VERSION or config["unit"] != "mmHg":
        raise ValueError("Unsupported schema_version or BP unit")
    if config["status"] not in (PENDING, APPROVED):
        raise ValueError(f"status must be {PENDING} or {APPROVED}")
    if (config["fit_split"], config["evaluation_split"]) != ("train", "val"):
        raise ValueError("B5 fits on train and evaluates val only")
    if config["b3_feature_set"] != features.VERSION:
        raise ValueError("Unsupported b3_feature_set")
    for field, rule in pipeline.V1_FIELDS.items():
        if config[field] != rule:
            raise ValueError(f"{field} must be {rule!r} (as B3 v1)")
    split = config["split_sha256"]
    if not isinstance(split, dict) or set(split) != {"raw", "inventory", "manifest",
                                                      "config"}:
        raise ValueError("split_sha256 needs raw, inventory, manifest and config")
    if config["model"] != MODEL:
        raise ValueError(f"model must be exactly {MODEL}")
    training = config["training"]
    if not isinstance(training, dict) or set(training) != TRAINING_FIELDS:
        raise ValueError("training must contain exactly the documented fields")
    for field, rule in TRAINING_RULES.items():
        if training[field] != rule:
            raise ValueError(f"training.{field} must be {rule!r}")
    for field in ("seed", "batch_size", "max_epochs", "patience", "eval_batch_size"):
        value = training[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < (
            0 if field == "seed" else 1
        ):
            raise ValueError(f"training.{field} must be a positive integer")
    if not 0 < training["inner_val_fraction"] < 0.5:
        raise ValueError("training.inner_val_fraction must be in (0, 0.5)")
    if not 0 < training["learning_rate"] < 1:
        raise ValueError("training.learning_rate must be in (0, 1)")
    xgb = config["xgboost"]
    if not isinstance(xgb, dict) or set(xgb) != {"seed", "params"}:
        raise ValueError("xgboost needs exactly seed and params")
    try:
        BootstrapConfig(**config["bootstrap"])
    except TypeError as exc:
        raise ValueError("Unsupported bootstrap field") from exc
    return config


def b3_config(config) -> dict:
    """The B3 v1 config the run refits B0/B3 with (same rules, seed, params)."""
    return {"schema_version": pipeline.VERSION_V1, "status": "NOT_TEST_EVALUATED",
            "unit": "mmHg", "fit_split": "train", "evaluation_split": "val",
            "feature_set": config["b3_feature_set"], "label_qc": config["label_qc"],
            "train_weighting": config["train_weighting"],
            "b3": copy.deepcopy(config["xgboost"]),
            "bootstrap": copy.deepcopy(config["bootstrap"])}


def inner_split(subject_ids, fraction, seed):
    """Inner-validation subjects: ``round(fraction * n)`` of the sorted unique train
    subjects, drawn with ``numpy.random.default_rng(seed)``; at least one, and at
    least one left to fit on."""
    unique = np.unique(subjects(subject_ids))
    if len(unique) < 2:
        raise ValueError("B5 needs at least two train subjects")
    count = min(max(1, int(round(fraction * len(unique)))), len(unique) - 1)
    chosen = np.random.default_rng(seed).permutation(len(unique))[:count]
    return set(unique[np.sort(chosen)].tolist())


def waveforms(segments, raw_indices, samples):
    """``(rows, 2, samples)`` float32 of ECG then PPG; refuses another length, a
    masked or a non-finite signal. Reads only ``.ecg`` and ``.ppg``."""
    out = np.empty((len(raw_indices), 2, samples), dtype=np.float32)
    for row, index in enumerate(raw_indices):
        segment = segments[index]
        for channel, values in enumerate((segment.ecg, segment.ppg)):
            if np.ma.isMaskedArray(values):
                raise ValueError("Masked signals are not imputed")
            array = np.asarray(values, dtype=np.float64)
            if array.shape != (samples,) or not np.isfinite(array).all():
                raise ValueError(f"ECG/PPG must be {samples} finite samples")
            out[row, channel] = array
    return out


def channel_scaling(x):
    """Per-channel mean and SD (float64) of the fit rows; a flat channel is refused."""
    mean = x.mean(axis=(0, 2), dtype=np.float64)
    sd = x.std(axis=(0, 2), dtype=np.float64)
    if not np.all(sd > 0):
        raise ValueError("A channel is constant over the fit rows")
    return mean, sd


def subject_balanced_mae(prediction, reference, subject_ids):
    """Mean over subjects of each subject's mean absolute error."""
    frame = pd.DataFrame({"s": subjects(subject_ids),
                          "e": np.abs(np.asarray(prediction) - np.asarray(reference))})
    return float(frame.groupby("s").e.mean().mean())


def _predict(model, x, batch, device, torch):
    model.eval()
    out = []
    with torch.no_grad():
        for start in range(0, len(x), batch):
            out.append(model(x[start:start + batch].to(device)).double().cpu().numpy())
    return np.concatenate(out)


def train_target(x_fit, y_fit, w_fit, x_inner, y_inner, inner_ids, training, device,
                 log=None):
    """Fit one ResNet-18 1D for one target (scaled), keeping the epoch with the
    lowest inner-validation subject-balanced MAE (earliest on a tie), stopping
    after ``patience`` epochs without improvement or at ``max_epochs``.

    ``y_*`` are in mmHg; the loss uses the train-fit standardized target and
    the subject weights. Returns ``(model, history, best_epoch, scale)``."""
    import torch

    from software.models.resnet1d import ResNet18_1d, set_deterministic

    set_deterministic(training["seed"])
    model = ResNet18_1d(in_channels=2, outputs=1).to(device)
    centre, spread = float(np.mean(y_fit)), float(np.std(y_fit))
    if not spread > 0:
        raise ValueError("The target is constant over the fit rows")
    xf = torch.from_numpy(x_fit).to(device)
    yf = torch.from_numpy(((y_fit - centre) / spread).astype(np.float32)).to(device)
    wf = torch.from_numpy(np.asarray(w_fit, dtype=np.float32)).to(device)
    xi = torch.from_numpy(x_inner)
    optimizer = torch.optim.Adam(model.parameters(), lr=training["learning_rate"])
    order = torch.Generator().manual_seed(training["seed"])
    history, best, best_state, waited = [], None, None, 0
    for epoch in range(1, training["max_epochs"] + 1):
        started = time.perf_counter()
        model.train()
        permutation = torch.randperm(len(xf), generator=order).to(device)
        total, seen = 0.0, 0
        for start in range(0, len(xf), training["batch_size"]):
            index = permutation[start:start + training["batch_size"]]
            optimizer.zero_grad(set_to_none=True)
            loss = (wf[index] * (model(xf[index]) - yf[index]) ** 2).mean()
            loss.backward()
            optimizer.step()
            total += float(loss.detach()) * len(index)
            seen += len(index)
        prediction = centre + spread * _predict(model, xi, training["eval_batch_size"],
                                                device, torch)
        mae = subject_balanced_mae(prediction, y_inner, inner_ids)
        history.append({"epoch": epoch, "train_weighted_mse_scaled": total / seen,
                        "inner_subject_balanced_mae": mae,
                        "seconds": time.perf_counter() - started})
        if log is not None:
            log(history[-1])
        if best is None or mae < best[1]:
            best, waited = (epoch, mae), 0
            best_state = {k: v.detach().cpu().clone() for k, v in
                          model.state_dict().items()}
        else:
            waited += 1
            if waited >= training["patience"]:
                break
    model.load_state_dict(best_state)
    return model, history, best[0], {"centre": centre, "spread": spread}


def run_b5(segments, manifest, inventory, config, device="cpu", mode="val", log=None):
    """Fit B5 (SBP and DBP models) on train; ``mode`` ``inner`` or ``val``.

    ``segments`` is indexed by raw_index. Train rows are label-QC'd and weighted
    as in B3 v1; the train subjects are split into fit and inner validation.
    """
    import torch

    from software.models.resnet1d import parameter_count

    if mode not in ("inner", "val"):
        raise ValueError("mode must be inner or val")
    pipeline.verify_inputs(manifest, inventory, segments)
    before_qc = (manifest, inventory)  # run_baselines applies the same QC itself
    manifest, inventory, qc = pipeline.label_qc(manifest, inventory)
    train = pipeline._rows(manifest, "train")
    weights = pipeline.subject_weights(train.subject_id.to_numpy())
    training = config["training"]
    held = inner_split(train.subject_id.to_numpy(), training["inner_val_fraction"],
                       training["seed"])
    inner_mask = train.subject_id.isin(held).to_numpy()
    fit, inner = train[~inner_mask], train[inner_mask]
    samples = config["model"]["samples"]
    x_fit = waveforms(segments, fit.raw_index.tolist(), samples)
    x_inner = waveforms(segments, inner.raw_index.tolist(), samples)
    mean, sd = channel_scaling(x_fit)
    scale = lambda x: ((x - mean[None, :, None]) / sd[None, :, None]).astype(np.float32)  # noqa: E731
    x_fit, x_inner = scale(x_fit), scale(x_inner)
    models, report = {}, {"label_qc": qc, "mode": mode, "device": str(device),
                          "inner_split": {"fit_subjects": int(fit.subject_id.nunique()),
                                          "fit_rows": len(fit),
                                          "inner_subjects": len(held),
                                          "inner_rows": len(inner)},
                          "input_scaling": {"mean": mean.tolist(), "sd": sd.tolist()},
                          "targets": {}}
    for target in TARGETS:
        column = target.lower()
        started = time.perf_counter()
        model, history, best_epoch, target_scale = train_target(
            x_fit, fit[column].to_numpy(), weights[~inner_mask], x_inner,
            inner[column].to_numpy(), inner.subject_id.to_numpy(), training, device,
            None if log is None else (lambda row, t=target: log(t, row)))
        models[target] = model
        report["targets"][target] = {
            "best_epoch": best_epoch, "epochs_run": len(history),
            "best_inner_subject_balanced_mae": min(
                h["inner_subject_balanced_mae"] for h in history),
            "target_scaling": target_scale, "train_seconds": time.perf_counter() - started,
            "history": history}
    report["parameters_per_model"] = parameter_count(models["SBP"])
    if mode == "inner":
        return {"report": report, "models": models}

    val = pipeline._rows(manifest, "val")
    x_val = torch.from_numpy(scale(waveforms(segments, val.raw_index.tolist(), samples)))
    started = time.perf_counter()
    b5 = np.column_stack([
        report["targets"][t]["target_scaling"]["centre"]
        + report["targets"][t]["target_scaling"]["spread"]
        * _predict(models[t], x_val, training["eval_batch_size"], device, torch)
        for t in TARGETS])
    report["val_inference_seconds"] = time.perf_counter() - started
    # B0/B3 refitted on every train row (no inner split), exactly as B3 v1 does.
    baselines = pipeline.run_baselines(segments, *before_qc, b3_config(config))
    table = pd.concat([baselines["predictions"], pd.DataFrame({
        "sample_id": val.sample_id.to_numpy(), "subject_id": val.subject_id.to_numpy(),
        "split": "val", "model": "B5", "pred_sbp": b5[:, 0], "pred_dbp": b5[:, 1]})],
        ignore_index=True)
    evaluation = evaluate_prediction_table(
        manifest, inventory, table, split="val",
        config=BootstrapConfig(**config["bootstrap"]), contrasts=CONTRASTS)
    counts = {split: {"subjects": int(manifest[manifest.split == split]
                                      .subject_id.nunique()),
                      "segments": int((manifest.split == split).sum())}
              for split in ("train", "val", "test")}
    return {"report": report, "models": models, "predictions": table,
            "evaluation": evaluation, "counts": counts,
            "b3_label_qc": baselines["label_qc"]}
