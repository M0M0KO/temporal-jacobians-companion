# Task-fMRI input and Python interface

[README](../README.md) · [中文概览](../README.zh-CN.md)


The input is a **preprocessed 4D BOLD NIfTI**, a **same-grid 3D integer label atlas**, a run-level BIDS `events.tsv` and the TR in seconds. Supply a run ID that is unique across participants, sessions and runs. Use the same atlas across runs. Motion or physiological regressors can be passed as a finite, whitespace-separated numeric matrix with one row per acquired volume. A 0/1 keep mask can censor motion-contaminated volumes.

```bash
temporal-jacobians bold --bold sub-01_preproc_bold.nii.gz --atlas atlas_in_bold_grid.nii.gz --events sub-01_events.tsv --tr 1.5 --run-id sub-01_task-flanker_run-1 --output run1.npz
```

The command averages voxels in each parcel, convolves event regressors with a double-gamma HRF, and estimates least-squares-separate (LSS) coefficients. Each fit isolates one target event and groups the other events by condition. It includes an intercept, linear drift and any supplied confounds. All regressors are constructed on the acquisition timeline before censoring. The caller is responsible for preprocessing, spatial registration, atlas coverage, QC and verifying the TR. The supplied HRF and least-squares model are transparent defaults for task fMRI. Other modalities and resting-state data need their own measurement model.

The predictor table contains one row per event, with `event_id`, `participant_id`, numeric baseline columns and numeric Jacobian columns. The output NPZ stores `event_id`, `parcel_id` and `beta`, where beta has shape (events, parcels). With standard `events.tsv` lacking an `event_id`, IDs use `<run-id>:source_row:<zero-based data row>`. For externally estimated betas, create the same three NPZ arrays and use identical parcel labels and order.

```bash
temporal-jacobians compare --betas run1.npz run2.npz run3.npz run4.npz --predictors predictors.tsv --holdout holdout.txt --baseline task_indicator reaction_time --features g00 g01 g11 --alpha 100 --output comparison.json
```

The holdout file lists one participant ID per line. The command matches exact event IDs, fits both ridge models on development participants and reports paired changes in mean parcel correlation on the holdout, with participant-bootstrap intervals. Fix alpha and feature definitions before opening the holdout. Estimate any model and covariance used to produce predictor columns on development data too.

### Call from Python

```python
import numpy as np
from temporal_jacobians import influence_geometry, temporal_jacobian

state = np.array([0.4, -0.2])
future = [np.array([0.1, 0.0]), np.zeros(2)]
def step(h, x):
    return np.tanh(0.8 * h + x)
def readout(h):
    return np.array([h[0], h.sum()])

j = temporal_jacobian(step, readout, state, future)
g = influence_geometry(j, np.eye(2))  # Use development-state covariance in an analysis.
```

The callable fixes future inputs and uses central differences to estimate the derivative of the final readout with respect to the initial hidden state. Use one contiguous run per sequence. The resulting geometry is `G = J Σ Jᵀ`. Use `event_betas` for in-memory scan-by-parcel time series and `compare_encoding` for in-memory predictors and trial beta arrays.
