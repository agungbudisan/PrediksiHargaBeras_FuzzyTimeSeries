"""Pembungkus Fuzzy Time Series Chen (1996) beserta evaluasi out-of-sample.

Modul ini mengimpor :mod:`ftsapp.compat` lebih dulu sehingga patch ``np.int``
selalu aktif sebelum pyFTS dipakai.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from collections import Counter

import numpy as np
import pandas as pd

from . import compat  # noqa: F401  (patches numpy untuk pyFTS)
from . import metrics as met

from pyFTS.models import chen
from pyFTS.partitioners import Grid

from . import config as cfg

# Jumlah data minimum agar partisi bermakna dan FLR bisa terbentuk.
MIN_DATA_LATIH = 12


@dataclass
class HasilEvaluasi:
    """Hasil evaluasi model: metrik agregat dan prediksi per titik."""

    metrik: dict[str, float]
    prediksi: list[float]
    aktual: list[float]
    tanggal: list[pd.Timestamp] = field(default_factory=list)
    n_latih: int = 0

    def ringkas(self) -> str:
        return met.ringkas(self.metrik)


def _partitioner(data: np.ndarray, n_part: int) -> Grid.GridPartitioner:
    return Grid.GridPartitioner(data=data, npart=int(n_part))


def latih(data: Sequence[float], n_part: int):
    """Bangun dan latih model Chen FTS pada `data`."""
    arr = np.asarray(data, dtype=float)
    if arr.size == 0:
        raise ValueError("Data latih kosong.")
    if n_part < 1:
        raise ValueError("Jumlah partisi minimal 1.")

    model = chen.ConventionalFTS(partitioner=_partitioner(arr, n_part))
    model.fit(arr)
    return model


def prediksi_dalam_model(model, data: Sequence[float]) -> list[float]:
    """Prediksi in-sample (data yang sama dengan data latih)."""
    arr = np.asarray(data, dtype=float)
    return [float(v) for v in model.predict(arr)]


def peramalan(model, data: Sequence[float], langkah: int) -> list[float]:
    """Peramalan rekursif `langkah` periode ke depan.

    Catatan: Chen first-order (order=1) hanya memakai nilai sebelumnya, sehingga
    peramalan cenderung mencapai fixed point setelah langkah pertama.
    """
    arr = np.asarray(data, dtype=float)
    if arr.size == 0:
        raise ValueError("Data kosong, tidak ada yang bisa diramal.")
    if langkah < 1:
        return []
    nilai = arr.tolist()
    return [float(v) for v in model.forecast_ahead(nilai, int(langkah))]


def aturan_flrg(model) -> pd.DataFrame:
    """Ubah basis aturan fuzzy logical relationship menjadi tabel."""
    baris = []
    for nama, flrg in sorted(model.flrgs.items(), key=lambda kv: kv[0]):
        try:
            tengah = float(flrg.get_midpoint(model.sets))
        except Exception:  # pragma: no cover - bergantung kondisi data
            tengah = float("nan")
        aturan = ", ".join(sorted(str(rhs) for rhs in flrg.RHS))
        baris.append(
            {
                "LHS": nama,
                "Aturan FLR": f"{nama} → {{{aturan}}}",
                "Jumlah Aturan": len(flrg.RHS),
                "Nilai Tengah": tengah,
            }
        )
    return pd.DataFrame(baris)


def rentang_partisi(model) -> pd.DataFrame:
    """Batas tiap fuzzy set beserta nilai tengahnya.

    ``model.sets`` pada pyFTS 1.6 berupa dict ``{nama: FuzzySet}``; batas
    bawah/atas diambil dari atribut ``lower`` dan ``upper``.
    """
    baris = []
    for nama in sorted(model.sets):
        fuzzy_set = model.sets[nama]
        bawah, atas = float(fuzzy_set.lower), float(fuzzy_set.upper)
        baris.append(
            {
                "Himpunan": fuzzy_set.name,
                "Batas Bawah": bawah,
                "Batas Atas": atas,
                "Lebar": atas - bawah,
                "Nilai Tengah": float(fuzzy_set.centroid),
            }
        )
    return pd.DataFrame(baris).sort_values("Batas Bawah").reset_index(drop=True)


def sebaran_himpunan(model, data: Sequence[float]) -> pd.DataFrame:
    """Jumlah data aktual pada tiap fuzzy set (hasil fuzzyfikasi).

    Catatan: ``mode='sets'`` pada pyFTS mengembalikan *nama* himpunan (string),
    bukan objek FuzzySet, sehingga yang dihitung langsung adalah nama tersebut.
    """
    arr = np.asarray(data, dtype=float)
    #(pyFTS 1.6, fuzzyfy(..., method='maximum', mode='sets') -> nama himpunan)
    nama = model.partitioner.fuzzyfy(arr, method="maximum", mode="sets")

    jumlah = Counter(str(n) for n in nama)
    return (
        pd.DataFrame(
            {"Himpunan": list(jumlah.keys()), "Jumlah Data": list(jumlah.values())}
        )
        .sort_values("Himpunan")
        .reset_index(drop=True)
    )


def evaluasi_dalam_model(data: Sequence[float], n_part: int) -> HasilEvaluasi:
    """Metrik in-sample: latih dan uji pada data yang sama.

    Angka ini cenderung terlalu optimistis dan tidak boleh dipresentasikan
    sebagai performa generalisasi model.
    """
    arr = np.asarray(data, dtype=float)
    model = latih(arr, n_part)
    pred = prediksi_dalam_model(model, arr)
    return HasilEvaluasi(
        metrik=met.hitung_semua(arr, pred),
        prediksi=pred,
        aktual=[float(v) for v in arr],
        n_latih=len(arr),
    )


def evaluasi_uji(data: Sequence[float], n_part: int, n_uji: int) -> HasilEvaluasi:
    """Split temporal: latih pada bagian awal, uji pada bagian akhir.

    Ini adalah estimasi out-of-sample yang jujur — model tidak pernah melihat
    data uji saat dilatih.
    """
    arr = np.asarray(data, dtype=float)
    if len(arr) < MIN_DATA_LATIH + 1:
        raise ValueError(
            f"Perlu minimal {MIN_DATA_LATIH + 1} titik untuk split latih/uji, "
            f"tersedia {len(arr)}."
        )

    n_uji = max(1, min(int(n_uji), len(arr) - MIN_DATA_LATIH))
    batas = len(arr) - n_uji
    latih_data, uji_data = arr[:batas], arr[batas:]

    model = latih(latih_data, n_part)
    pred = [float(v) for v in model.predict(uji_data)]

    return HasilEvaluasi(
        metrik=met.hitung_semua(uji_data, pred),
        prediksi=pred,
        aktual=[float(v) for v in uji_data],
        n_latih=batas,
    )


def evaluasi_rolling(
    data: Sequence[float],
    n_part: int,
    min_latih: int = MIN_DATA_LATIH,
    maks_langkah: int | None = None,
    tanggal: Sequence[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    """Rolling-origin evaluation (expanding window).

    Untuk setiap t >= min_latih, model dilatih ulang pada data[:t] lalu
    memprediksi data[t]. Menghasilkan deret error per waktu, bukan hanya satu
    angka agregat, sehingga pola bias/errors terlihat jelas.

    Args:
        tanggal: label waktu sejajar dengan `data`. Bila diberikan, dipakai
            sebagai kolom ``Tanggal`` pada hasil.
    """
    arr = np.asarray(data, dtype=float)
    if len(arr) <= min_latih:
        raise ValueError(
            f"Rolling evaluation butuh lebih dari {min_latih} titik, tersedia {len(arr)}."
        )
    if tanggal is not None and len(tanggal) != len(arr):
        raise ValueError("Panjang `tanggal` harus sama dengan panjang `data`.")

    total = len(arr) - min_latih
    if maks_langkah is not None:
        total = min(total, int(maks_langkah))

    baris = []
    for i in range(total):
        t = min_latih + i
        model = latih(arr[:t], n_part)
        pred = float(model.predict(arr[t : t + 1])[0])
        aktual = float(arr[t])
        baris.append(
            {
                "t": t,
                "Tanggal": pd.Timestamp(tanggal[t]) if tanggal is not None else pd.NaT,
                "Aktual": aktual,
                "Prediksi": pred,
                "Error": aktual - pred,
                "APE": abs((aktual - pred) / aktual) * 100 if aktual else np.nan,
            }
        )
    return pd.DataFrame(baris)


def metrik_rolling(hasil: pd.DataFrame) -> dict[str, float]:
    """Agregat metrik dari hasil rolling-origin."""
    return met.hitung_semua(hasil["Aktual"], hasil["Prediksi"])


def kurva_partisi(
    data: Sequence[float],
    rentang: tuple[int, int] = (cfg.N_PART_MIN, cfg.N_PART_MAX),
) -> pd.DataFrame:
    """Hitung RMSE out-of-sample untuk tiap jumlah partisi.

    Dipakai untuk melihat pengaruh hyperparameter `npart` terhadap error, bukan
    hanya menebak nilainya lewat slider.
    """
    arr = np.asarray(data, dtype=float)
    baris = []
    for n_part in range(int(rentang[0]), int(rentang[1]) + 1):
        try:
            res = evaluasi_uji(arr, n_part, n_uji=max(1, len(arr) // 5))
            baris.append(
                {"Jumlah Partisi": n_part, "RMSE": res.metrik["RMSE"], "MAPE": res.metrik["MAPE"]}
            )
        except Exception:
            continue
    return pd.DataFrame(baris)


def tanggal_masa_depan(tanggal_terakhir: pd.Timestamp, langkah: int) -> list[pd.Timestamp]:
    """Beri label bulan untuk periode peramalan ke depan."""
    awal = pd.Timestamp(tanggal_terakhir).normalize() + pd.offsets.MonthBegin(1)
    return [awal + pd.offsets.MonthBegin(i) for i in range(int(langkah))]