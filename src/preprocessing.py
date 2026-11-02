from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def standardize_acoustic_spectrum(
    spectrum: pd.DataFrame,
) -> tuple[np.ndarray, StandardScaler]:
    """Z-score acoustic bands only; metadata must not be passed to this function."""
    if spectrum.empty or spectrum.columns.empty:
        raise ValueError("The acoustic spectrum must contain rows and frequency bands.")
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in spectrum.dtypes):
        raise TypeError("Every acoustic frequency band must be numeric.")

    values = spectrum.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(values).all():
        raise ValueError("The acoustic spectrum contains missing or non-finite values.")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(values)
    return scaled, scaler
