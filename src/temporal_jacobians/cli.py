"""Local command-line interface for the task-fMRI workflow."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from .dynamics import influence_geometry, temporal_jacobian
from .encoding import compare_encoding
from .fmri import event_betas, event_design, nifti_event_betas


def table(path):
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t" if path.suffix == ".tsv" else ","))


def keys(rows):
    values = [r["event_id"] for r in rows]
    if not all(values) or len(values) != len(set(values)):
        raise ValueError("event_id values must be nonempty and unique")
    return values


def run_bold(args):
    events = table(args.events)
    if not events:
        raise ValueError("EVENTS file is empty")
    ids = keys(events) if "event_id" in events[0] else [f"{args.run_id}:source_row:{i}" for i in range(len(events))]
    if "event_id" not in events[0] and not args.run_id:
        raise ValueError("Supply --run-id when the events file has no event_id column")
    timing = [[float(row[col]) for row in events] for col in ("onset", "duration")]
    nuisance = None if args.confounds is None else np.loadtxt(args.confounds, ndmin=2)
    mask = None if args.keep is None else np.loadtxt(args.keep, ndmin=1)
    if mask is not None and not np.isin(mask, [0, 1]).all():
        raise ValueError("The keep file must contain 0 and 1 only")
    beta, parcels = nifti_event_betas(
        args.bold, args.atlas, args.tr, *timing,
        conditions=[r.get("trial_type", "event") for r in events],
        confounds=nuisance, keep=None if mask is None else mask.astype(bool),
    )
    with args.output.open("wb") as stream:
        np.savez_compressed(stream, event_id=np.asarray(ids), beta=beta, parcel_id=parcels)
    print(json.dumps(dict(events=len(ids), parcels=len(parcels), output=str(args.output))))


def run_compare(args):
    rows = table(args.predictors)
    ids = keys(rows)
    joined, parcels = {}, None
    for path in args.betas:
        with np.load(path, allow_pickle=False) as value:
            beta, labels = value["beta"], value["parcel_id"]
            event_ids = value["event_id"]
            if (event_ids.ndim != 1 or event_ids.dtype.kind != "U"
                    or labels.ndim != 1 or len(np.unique(labels)) != len(labels)
                    or beta.shape != (len(event_ids), len(labels))):
                raise ValueError(f"Invalid beta archive: {path}")
            if parcels is None:
                parcels = labels
            elif not np.array_equal(parcels, labels):
                raise ValueError(f"Parcel IDs or order differ in {path}")
            for key, row in zip(event_ids, beta, strict=True):
                if not key or key in joined:
                    raise ValueError(f"Empty or duplicate beta event: {key!r}")
                joined[key] = row
    if set(ids) != set(joined):
        missing = len(set(ids)-set(joined))
        extra = len(set(joined)-set(ids))
        raise ValueError(f"Event sets differ ({missing} without beta, {extra} without predictors)")
    heldout = [line.strip() for line in args.holdout.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    base, enhanced = [
        np.array([[float(r[k]) for k in columns] for r in rows])
        for columns in (args.baseline, args.features)
    ]
    result = compare_encoding(base, enhanced, np.stack([joined[i] for i in ids]),
                              [r["participant_id"] for r in rows], heldout, alpha=args.alpha)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("participant_scores", "excluded_participants")}))


def run_demo(args):
    rng = np.random.default_rng(41)
    dest = args.output
    dest.mkdir(parents=True, exist_ok=True)
    onsets = np.arange(6, 6 + 16 * 24, 16)
    duration = np.zeros(len(onsets))
    design = event_design(280, 1.5, onsets, duration)
    state_covariance = np.eye(2)
    rows, target = [], []
    for subject in range(10):
        for_trial = rng.normal(size=(len(onsets), 2))
        j = np.stack([temporal_jacobian(lambda h, x: 0.8*h+x, lambda h: h**2, h, [0])
                      for h in for_trial])
        geometry = influence_geometry(j, state_covariance)
        feature = np.log1p(geometry[:, 0, 0])
        baseline = np.arange(len(onsets)) % 2
        embedded = 0.3*baseline + feature
        signal = np.column_stack((embedded, -0.6*embedded, 0.4*embedded))
        timeseries = design @ signal + rng.normal(scale=0.025, size=(len(design), 3))
        target.extend(event_betas(timeseries, 1.5, onsets, duration, conditions=baseline))
        rows.extend([dict(
            event_id=f"sim{subject:02d}:run1:source_row:{i}", participant_id=f"sim{subject:02d}",
            condition=int(c), geometry=float(g),
        ) for i, (c, g) in enumerate(zip(baseline, feature, strict=True))])
    with (dest/"predictors.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    np.savez_compressed(dest/"betas.npz", event_id=np.asarray(keys(rows)), beta=np.asarray(target),
                        parcel_id=np.array([1, 2, 3]))
    (dest/"holdout.txt").write_text("sim07\nsim08\nsim09\n", encoding="utf-8")
    run_compare(argparse.Namespace(
        predictors=dest/"predictors.csv", betas=[dest/"betas.npz"], holdout=dest/"holdout.txt",
        baseline=["condition"], features=["geometry"], alpha=1, output=dest/"encoding.json",
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")
    demo = commands.add_parser("demo", help="Generate and analyze synthetic parcel time series")
    demo.add_argument("--output", type=Path, default=Path("temporal-jacobians-demo"))
    demo.set_defaults(run=run_demo)
    bold = commands.add_parser("bold", help="Estimate event-wise betas from a preprocessed NIfTI run")
    for name in ("bold", "atlas", "events", "output"):
        bold.add_argument(f"--{name}", type=Path, required=True)
    bold.add_argument("--tr", type=float, required=True)
    bold.add_argument("--run-id")
    bold.add_argument("--confounds", type=Path)
    bold.add_argument("--keep", type=Path)
    bold.set_defaults(run=run_bold)
    compare = commands.add_parser("compare", help="Compare baseline and extended encoding on held-out people")
    for name in ("predictors", "holdout", "output"):
        compare.add_argument(f"--{name}", type=Path, required=True)
    compare.add_argument("--betas", type=Path, nargs="+", required=True)
    compare.add_argument("--baseline", nargs="+", required=True)
    compare.add_argument("--features", nargs="+", required=True)
    compare.add_argument("--alpha", type=float, default=100)
    compare.set_defaults(run=run_compare)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, OSError, KeyError, RuntimeError) as exc:
        parser.exit(2, f"temporal-jacobians: {exc}\n")


if __name__ == "__main__":
    main()
