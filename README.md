# Temporal Jacobians

An offline browser companion for the synthetic and human behavioral results in *From cognitive prediction to mechanism: validating recurrent models with temporal Jacobians*.

Download the source ZIP, extract it, and open **`index.html`** in a browser. The page runs locally and requires no installation or network connection.

| Button | What runs |
|---|---|
| Recompute recovery summary | Counts exact measurements, perturbation passes, and complete generator recovery from the frozen public synthetic tables. |
| Check behavioral equivalence | Checks the published participant-bootstrap intervals against the original equivalence band and displays the closest recurrent models. |
| Run example | Simulates a two-state system, compares the predicted and recomputed finite changes, and checks invariance under an affine change of state coordinates. |

The synthetic button reapplies all five recovery criteria to each published cohort row. The behavioral button uses the archived confidence intervals and reapplies the equivalence rule. Full model fitting and participant-level resampling use the original analysis pipeline and its frozen derived inputs. The example is a small, separate simulation with adjustable settings.

`source-data/` contains the aggregate CSVs and the relevant summary fields from the [original code and data repository, commit 6233df2](https://github.com/pwa209/Temporal-Jacobians-predict-fitted-model-interventions-without-recovering-known-latent-dynamics/tree/6233df2584e2176fe65794a3b741c8bda2c98605). To regenerate the single-file browser page from these tables, run `python build_browser.py` from this directory.
