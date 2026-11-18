"""State-to-output derivatives with fixed future inputs."""

from collections.abc import Callable, Sequence

import numpy as np


def _vector(value, name):
    array = np.asarray(value, dtype=float)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite nonempty vector")
    return array


def temporal_jacobian(
    step: Callable, readout: Callable, state, future_inputs: Sequence, *, relative_step: float = 1e-5
):
    """Central difference of readout(step^k(state, future_inputs)) w.r.t. state.

    step(h, x) and readout(h) should be deterministic and free of side effects.
    The caller supplies one contiguous run segment and fixes the future inputs.
    Return shape is (number of output dimensions, number of state dimensions).
    """
    state = _vector(state, "state")
    sequence = tuple(future_inputs)
    if not sequence or not np.isfinite(relative_step) or relative_step <= 0:
        raise ValueError("Provide future inputs and a positive finite relative_step")

    def advance(h):
        for x in sequence:
            candidate = _vector(step(h, x), "next state")
            if candidate.shape != state.shape:
                raise ValueError("step changed the hidden-state shape")
            h = candidate
        return _vector(np.atleast_1d(readout(h)), "readout")

    columns = []
    for coordinate, reference in enumerate(state):
        eps = relative_step * max(1.0, abs(reference))
        upper, lower = state.copy(), state.copy()
        upper[coordinate] += eps
        lower[coordinate] -= eps
        above, below = advance(upper), advance(lower)
        if above.shape != below.shape:
            raise ValueError("readout changed output shape")
        columns.append((above - below) / (2 * eps))
    return np.stack(columns, axis=1)


def influence_geometry(jacobian, state_covariance):
    """Compute J Σ Jᵀ, accepting one Jacobian or a batch of Jacobians."""
    jacobian = np.asarray(jacobian, dtype=float)
    covariance = np.asarray(state_covariance, dtype=float)
    if (jacobian.ndim < 2 or not np.isfinite(jacobian).all()
            or covariance.shape != (jacobian.shape[-1], jacobian.shape[-1])
            or not np.isfinite(covariance).all() or not np.allclose(covariance, covariance.T)):
        raise ValueError("Expected compatible finite Jacobians and symmetric state covariance")
    return (jacobian @ covariance) @ np.swapaxes(jacobian, -1, -2)
