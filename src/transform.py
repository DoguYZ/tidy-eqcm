from src.experiment import ToyExperiment

from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
import numpy as np
from numpy.typing import NDArray
from typing import Any


def add_potential_and_cycle_number(
    experiment: ToyExperiment, time_diff: float = 0.0
) -> None:
    # don't get decimal cycle numbers
    f = interp1d(
        experiment.cv.timestamp_s,
        experiment.cv.cycle_number,
        kind="nearest",
        bounds_error=False,
        fill_value=(
            experiment.cv.cycle_number.iloc[0],
            experiment.cv.cycle_number.iloc[-1],
        ),  # type: ignore[attr-defined] # scipy type stubs are incomplete
    )

    experiment.time_diff += time_diff
    experiment.eqcm.timestamp_s += time_diff
    experiment.eqcm = experiment.eqcm.assign(
        potential_V=lambda x: np.interp(
            x.timestamp_s,
            experiment.cv.timestamp_s,
            experiment.cv.potential_V,
        )
    )
    experiment.eqcm = experiment.eqcm.assign(
        cycle_number=lambda d: f(d.timestamp_s)
    )


def add_savgol(experiment: ToyExperiment) -> None:
    experiment.eqcm.frequency_savgol_Hz = savgol_filter(
        experiment.eqcm.frequency_Hz,
        experiment.savgol_window,
        experiment.savgol_order,
    )


def fit_drift(experiment: ToyExperiment) -> NDArray[Any]:
    cv_extremes_timestamps = (
        experiment.cv.loc[
            experiment.cv.groupby(["cycle_number"])["potential_V"].idxmax()
        ]
        .reset_index(drop=True)
        .timestamp_s.tolist()
    )

    cv_cycle_lengths = experiment.cv.groupby(["cycle_number"]).count()

    # whether or not to use the last CV/EQCM cycle to fit
    if (
        cv_cycle_lengths.iloc[-1]["timestamp_s"]
        < 0.75 * cv_cycle_lengths.iloc[-2]["timestamp_s"]
    ):
        cv_extremes_timestamps.pop()

    eqcm_extremes_locations = [
        find_nearest(experiment.eqcm.timestamp_s, t)
        for t in cv_extremes_timestamps
    ]
    extremes_eqcm_values = [
        experiment.eqcm.loc[
            experiment.eqcm.timestamp_s == t, "frequency_savgol_Hz"
        ].values[0]
        for t in eqcm_extremes_locations
    ]

    poly_fit = np.polynomial.Polynomial.fit(
        eqcm_extremes_locations,
        extremes_eqcm_values,
        deg=experiment.drift_order,
    )

    drift = poly_fit(experiment.eqcm.timestamp_s)

    return drift


def remove_drift(experiment: ToyExperiment, drift: NDArray[Any]) -> None:
    experiment.eqcm.frequency_Hz = (
        experiment.eqcm.frequency_Hz - drift + drift[0]
    )
    experiment.eqcm.frequency_savgol_Hz = (
        experiment.eqcm.frequency_savgol_Hz - drift + drift[0]
    )


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]
