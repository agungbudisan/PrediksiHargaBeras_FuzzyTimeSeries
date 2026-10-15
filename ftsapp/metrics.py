"""Metrik evaluasi untuk membandingkan nilai aktual dan prediksi."""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def _as_array(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("Metrik tidak dapat dihitung dari data kosong.")
    return arr


def mae(aktual: Sequence[float], prediksi: Sequence[float]) -> float:
    """Mean Absolute Error."""
    a, p = _as_array(aktual), _as_array(prediksi)
    return float(np.mean(np.abs(a - p)))


def rmse(aktual: Sequence[float], prediksi: Sequence[float]) -> float:
    """Root Mean Squared Error."""
    a, p = _as_array(aktual), _as_array(prediksi)
    return float(np.sqrt(np.mean((a - p) ** 2)))


def mape(aktual: Sequence[float], prediksi: Sequence[float]) -> float:
    """Mean Absolute Percentage Error dalam persen.

    Titik dengan nilai aktual nol dilewati karena MAPE tidak terdefinisi di sana.
    """
    a, p = _as_array(aktual), _as_array(prediksi)
    mask = a != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((a[mask] - p[mask]) / a[mask])) * 100)


def hitung_semua(aktual: Sequence[float], prediksi: Sequence[float]) -> Dict[str, float]:
    """Hitung MAE, RMSE, dan MAPE sekaligus."""
    return {
        "MAE": mae(aktual, prediksi),
        "RMSE": rmse(aktual, prediksi),
        "MAPE": mape(aktual, prediksi),
    }


def ringkas(hasil: Dict[str, float]) -> str:
    """Format metrik menjadi satu baris ringkas (gaya Indonesia)."""
    from .format import angka, persen

    return (
        f"MAE {angka(hasil['MAE'], 2)} · "
        f"RMSE {angka(hasil['RMSE'], 2)} · "
        f"MAPE {persen(hasil['MAPE'])}"
    )