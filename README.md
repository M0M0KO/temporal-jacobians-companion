# Temporal Jacobians

[中文](README.zh-CN.md) · [Browser companion](https://m0m0ko.github.io/temporal-jacobians-companion/) · [Archived results](source-data/analysis_summary.json) · [Task-fMRI guide](docs/task-fmri.md)

Code and browser companion for *From prediction to mechanism in psychoradiology: validation of recurrent neural networks using temporal Jacobians*.

## Research question

If a recurrent model predicts behavior and the output changes caused by perturbing its own state, has it recovered the dynamics that generated the data?

We test behavioral prediction, model-intervention prediction and generator recovery separately. This repository provides temporal Jacobian calculations, interactive checks of public results and tools for event-aligned task-fMRI encoding.

## Main findings

| Test | Result |
| --- | --- |
| Measurement of the known generator | Exact measurements passed the recovery criteria in **60/60** synthetic cohorts. |
| Fitted-model responses and generator recovery | Finite-perturbation R² and sign checks passed, while trained models achieved complete generator recovery in **3/60** cohorts. |
| Equivalence in human behavioral prediction | Across **109 participants and 73,219 common events**, **0/24** architecture-ensemble comparisons met the original equivalence criterion. |

These results distinguish prediction of model responses from recovery of the generator. Human evidence comes from behavior; the task-fMRI tools provide a simulated example and an interface for new data. See the [summary](source-data/analysis_summary.json) and [equivalence table](source-data/figure4b_architecture_equivalence.csv).

## Quick start

### Explore the results in a browser

[Open the companion](https://m0m0ko.github.io/temporal-jacobians-companion/), or download the source ZIP and open `index.html` locally.

| Button | What runs |
| --- | --- |
| Recompute recovery summary | Reapplies all five recovery criteria to frozen public tables and summarizes exact measurements, perturbation checks and complete recovery |
| Check behavioral equivalence | Reapplies the original equivalence rule to archived participant-bootstrap intervals |
| Run example | Simulates a two-state system, compares predicted and recomputed finite changes and checks invariance under an affine state-coordinate change |

The first two buttons check public tables and decision rules. Full model fitting and participant-level resampling use the original analysis pipeline and frozen inputs.

### Run the Python example

Use Python 3.10 or later. This command pins release `v0.1.0`:

```bash
python -m pip install "temporal-jacobians[fmri] @ git+https://github.com/M0M0KO/temporal-jacobians-companion.git@v0.1.0"
temporal-jacobians demo --output demo-output
```

The example generates simulated parcel time series, estimates trial betas, computes geometry features from a known two-state system and compares two encoders on three held-out simulated participants. The simulated signal is constructed to covary with the geometry feature to demonstrate the workflow.

| Output | Contents |
| --- | --- |
| `predictors.csv` | Events, participants and predictors |
| `betas.npz` | Event betas, event IDs and parcel IDs |
| `holdout.txt` | Held-out simulated participants |
| `encoding.json` | Encoder comparisons and participant-level results |

## Use your task-fMRI data

Prepare a preprocessed 4D BOLD NIfTI, a same-grid 3D integer label atlas, BIDS `events.tsv` and the TR in seconds. Estimate event-wise parcel betas, then compare a baseline encoder with an encoder that adds Jacobian features:

```bash
temporal-jacobians bold --bold sub-01_preproc_bold.nii.gz --atlas atlas_in_bold_grid.nii.gz --events sub-01_events.tsv --tr 1.5 --run-id sub-01_task-flanker_run-1 --output run1.npz
temporal-jacobians compare --betas run1.npz run2.npz run3.npz run4.npz --predictors predictors.tsv --holdout holdout.txt --baseline task_indicator reaction_time --features g00 g01 g11 --alpha 100 --output comparison.json
```

The second command uses multiple prepared runs and a predictor table. See the [task-fMRI guide](docs/task-fmri.md) for fields, exact event matching, confounds, censoring and the Python interface.

Events are matched by ID. Models are fit on development participants and scored on distinct held-out participants, with participant-level intervals. Fix regularization, feature definitions and state covariance before opening held-out results. Preprocessing, registration, atlas coverage and QC belong to the data-analysis workflow.

## Reproduction coverage

| Component | Included here | Additional inputs |
| --- | --- | --- |
| Checks of published aggregate results | Frozen source tables, decision rules and browser companion | Full fitting and participant resampling use the original analysis inputs |
| Two-state and task-fMRI demonstrations | Generated data and runnable examples | No human imaging required |
| Encoding with new task-fMRI data | Event estimation, Jacobian features and participant-held-out comparison | QC-approved images, atlas, events, predictors and predefined roles |

## Repository structure

| Location | Contents |
| --- | --- |
| [`index.html`](index.html) | Offline single-file browser companion |
| [`template.html`](template.html) · [`build_browser.py`](build_browser.py) | Page template and build script |
| [`source-data/`](source-data/) | Recovery, behavioral equivalence and summary results |
| [`src/temporal_jacobians/`](src/temporal_jacobians/) | Jacobians, geometry, event estimation and encoding comparisons |
| [`docs/task-fmri.md`](docs/task-fmri.md) | Task-fMRI input contract and Python interface |

## Data

Public tables and summary fields come from [the original code and data repository at commit 6233df2](https://github.com/pwa209/Temporal-Jacobians-predict-fitted-model-interventions-without-recovering-known-latent-dynamics/tree/6233df2584e2176fe65794a3b741c8bda2c98605). Run `python build_browser.py` from the source root to regenerate the browser page from these tables.

## Citation

Cite the study using the manuscript title above. When citing code or the browser companion, include the [repository URL](https://github.com/M0M0KO/temporal-jacobians-companion) and the commit or release used.

## License

Code and software documentation are available under the [MIT License](LICENSE). Archived results in `source-data/` and their copies embedded in `index.html` retain the terms of their original source.
