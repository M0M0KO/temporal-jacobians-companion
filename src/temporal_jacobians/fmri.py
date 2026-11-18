"""Estimate event-wise parcel betas from an aligned, preprocessed BOLD run."""

from math import factorial
from pathlib import Path

import numpy as np


def event_design(n_scans, tr, onsets, durations, *, oversampling=16):
    """Build one double-gamma HRF regressor per event in acquisition order."""
    onsets = np.asarray(onsets, dtype=float)
    durations = np.asarray(durations, dtype=float)
    if (n_scans < 2 or not np.isfinite(tr) or tr <= 0 or not isinstance(oversampling, int)
            or oversampling < 1 or onsets.ndim != 1 or not len(onsets)
            or durations.shape != onsets.shape or not np.isfinite(onsets).all()
            or not np.isfinite(durations).all() or (onsets < 0).any()
            or (durations < 0).any() or (onsets + durations > n_scans * tr).any()):
        raise ValueError("Check TR, scan count, and finite, in-run onset/duration values")
    step = tr / oversampling
    time = np.arange(0, 32 + step, step)
    hrf = np.exp(-time) * (time**5 / factorial(5) - time**15 / (6 * factorial(15)))
    hrf /= hrf.sum()
    size = n_scans * oversampling
    design = np.empty((n_scans, len(onsets)))
    for i, (onset, duration) in enumerate(zip(onsets, durations, strict=True)):
        stimulus = np.zeros(size)
        start = int(np.floor(onset / step))
        end = min(size, start + max(1, int(np.ceil(duration / step))))
        if start >= size:
            raise ValueError(f"Event {i} starts after acquisition")
        stimulus[start:end] = 1
        if duration == 0:
            stimulus[start] = oversampling
        design[:, i] = np.convolve(stimulus, hrf)[:size:oversampling]
    return design


def event_betas(bold, tr, onsets, durations, *, conditions=None, confounds=None, keep=None):
    """Least-squares-separate betas with optional condition-specific other trials.

    bold has shape (scans, parcels). keep is a Boolean mask of retained frames.
    Censoring is applied after HRF convolution on the original time grid.
    """
    y = np.asarray(bold, dtype=float)
    if y.ndim != 2 or not y.shape[1] or not np.isfinite(y).all():
        raise ValueError("bold must contain a finite (scans, parcels) array")
    n = len(y)
    events = event_design(n, tr, onsets, durations)
    labels = np.asarray(conditions if conditions is not None else ["event"] * events.shape[1], dtype=str)
    if labels.ndim != 1 or len(labels) != events.shape[1]:
        raise ValueError("conditions must have one value per event")
    nuisance = np.column_stack((np.ones(n), np.linspace(-1, 1, n)))
    if confounds is not None:
        confounds = np.asarray(confounds, dtype=float)
        if confounds.ndim != 2 or len(confounds) != n or not np.isfinite(confounds).all():
            raise ValueError("confounds must be a finite matrix with one row per acquired scan")
        nuisance = np.column_stack((nuisance, confounds))
    keep = np.ones(n, dtype=bool) if keep is None else np.asarray(keep)
    if keep.shape != (n,) or keep.dtype.kind != "b":
        raise ValueError("keep must be a Boolean mask with one value per acquired scan")
    y = y[keep]
    events = events[keep]
    nuisance = nuisance[keep]
    condition_names = np.unique(labels)
    summed = {key: events[:, labels == key].sum(axis=1) for key in condition_names}
    beta = []
    for i, key in enumerate(labels):
        trial = events[:, i]
        others = [summed[k] - trial if k == key else summed[k] for k in condition_names]
        x = np.column_stack([trial, *others, nuisance])
        if len(x) < 4:
            raise ValueError("Too few retained scans")
        # The target coefficient is identifiable only if its regressor has a
        # component outside the span of the other trials and nuisance terms.
        z = x[:, 1:]
        target = trial - z @ np.linalg.lstsq(z, trial, rcond=None)[0]
        denominator = target @ target
        if denominator <= np.finfo(float).eps * len(trial) * max(1.0, trial @ trial):
            raise ValueError(f"Cannot estimate event {i} with this design and censor mask")
        beta.append((target @ y) / denominator)
    return np.stack(beta)


def nifti_event_betas(
    bold_path: str | Path, atlas_path: str | Path, tr, onsets, durations, **kwargs
):
    """Estimate betas from preprocessed 4D NIfTI and a same-grid label atlas."""
    try:
        import nibabel as nib
    except ImportError as exc:
        raise RuntimeError("Install the fmri extra to read NIfTI files") from exc
    bold = nib.load(str(bold_path))
    atlas = nib.load(str(atlas_path))
    if (len(bold.shape) != 4 or bold.shape[:3] != atlas.shape
            or not np.allclose(bold.affine, atlas.affine, atol=1e-4, rtol=0)):
        raise ValueError("BOLD and 3D label atlas must share the same voxel shape and affine")
    atlas_values = np.asarray(atlas.dataobj)
    if (not np.isfinite(atlas_values).all() or (atlas_values < 0).any()
            or not np.array_equal(atlas_values, np.floor(atlas_values))):
        raise ValueError("Atlas values must be nonnegative integers")
    labels = np.unique(atlas_values)
    labels = labels[labels != 0].astype(int)
    if not len(labels):
        raise ValueError("Atlas has no positive labels")
    # Read consecutive volumes in blocks to bound memory and limit repeated I/O.
    identifiers = atlas_values.ravel().astype(int)
    active = identifiers > 0
    bins = np.searchsorted(labels, identifiers[active])
    counts = np.bincount(bins, minlength=len(labels))
    data = np.empty((bold.shape[3], len(labels)))
    for start in range(0, bold.shape[3], 16):
        stop = min(start+16, bold.shape[3])
        block = np.asarray(bold.dataobj[..., start:stop], dtype=np.float32).reshape(-1, stop-start)
        for offset in range(stop-start):
            weights = block[active, offset]
            data[start+offset] = np.bincount(bins, weights=weights, minlength=len(labels)) / counts
    return event_betas(data, tr, onsets, durations, **kwargs), labels
