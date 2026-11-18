"""Compare fixed ridge encoders on independent participants."""

import numpy as np


def compare_encoding(baseline, features, beta, participant, holdout, *, alpha=100, seed=20261118):
    """Return paired participant-level differences in mean parcel correlation."""
    base, extra, y = [np.asarray(x, dtype=float) for x in (baseline, features, beta)]
    people = np.asarray(participant, dtype=str)
    if (people.ndim != 1 or any(x.ndim != 2 or len(x) != len(people) or not x.shape[1]
                               or not np.isfinite(x).all() for x in (base, extra, y))
            or not np.isfinite(alpha) or alpha <= 0):
        raise ValueError("Arrays must have matching event rows and finite values. Alpha must be positive.")
    unique = np.unique(people)
    requested = set(holdout)
    if not requested <= set(unique) or len(requested) < 2 or len(unique) - len(requested) < 2:
        raise ValueError("Require at least two development and two specified held-out participants")
    test = np.isin(people, list(requested))
    hold = people[test]
    actual = y[test]

    def predict(x):
        train = x[~test]
        center, scale = train.mean(axis=0), train.std(axis=0)
        scale[scale < 1e-12] = 1
        design = (train - center) / scale
        intercept = y[~test].mean(axis=0)
        penalty = alpha * np.eye(design.shape[1])
        weights = np.linalg.solve(design.T @ design + penalty, design.T @ (y[~test] - intercept))
        return ((x[test] - center) / scale) @ weights + intercept

    basic, expanded = predict(base), predict(np.column_stack((base, extra)))
    paired, excluded = [], []
    for person in sorted(requested):
        mask = hold == person
        if np.count_nonzero(mask) < 3:
            excluded.append(dict(participant=person, reason="fewer_than_three_events"))
            continue
        observed, before, after = [z[mask] - z[mask].mean(axis=0) for z in (actual, basic, expanded)]
        observed_norm, before_norm, after_norm = [np.linalg.norm(z, axis=0) for z in (observed, before, after)]
        valid = (observed_norm > 1e-12) & (before_norm > 1e-12) & (after_norm > 1e-12)
        if not valid.any():
            excluded.append(dict(participant=person, reason="no_common_nonconstant_parcel"))
            continue
        b = ((observed[:, valid] * before[:, valid]).sum(axis=0) / (observed_norm * before_norm)[valid]).mean()
        a = ((observed[:, valid] * after[:, valid]).sum(axis=0) / (observed_norm * after_norm)[valid]).mean()
        paired.append(dict(participant=person, baseline_r=float(b), extended_r=float(a),
                           delta_r=float(a-b), events=int(mask.sum()), parcels=int(valid.sum())))
    if len(paired) < 2:
        raise ValueError("Fewer than two held-out participants have scorable events")
    delta = np.asarray([row["delta_r"] for row in paired])
    rng = np.random.default_rng(seed)
    draws = delta[rng.integers(len(delta), size=(5000, len(delta)))].mean(axis=1)
    return dict(alpha=alpha, n_development=len(unique)-len(requested), n_test=len(paired),
                mean_delta_r=float(delta.mean()), bootstrap_ci95=np.quantile(draws, [0.025, 0.975]).tolist(),
                participant_scores=paired, excluded_participants=excluded)
