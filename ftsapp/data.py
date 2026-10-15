"""Pemuatan, validasi, dan penyaringan dataset harga beras."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config as cfg

KOLOM_SUMBER_TANGGAL = "Bulan-Tahun"
KOLOM_SUMBER_HARGA = "Harga"


def muat_dataset(path: str | Path = "dataset.csv") -> pd.DataFrame:
    """Baca dataset dan kembalikan frame dengan kolom turunan.

    Mengembalikan kolom ``Tanggal`` (datetime64), ``Harga`` (float),
    ``Tahun``, ``Bulan``, dan ``BulanNama``.

    Raises:
        FileNotFoundError: bila file tidak ditemukan.
        ValueError: bila kolom wajib tidak ada atau tanggal tidak bisa diparse.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset '{path}' tidak ditemukan. Jalankan aplikasi dari root repository."
        )

    df = pd.read_csv(path)

    hilang = {KOLOM_SUMBER_TANGGAL, KOLOM_SUMBER_HARGA} - set(df.columns)
    if hilang:
        raise ValueError(
            f"Kolom wajib tidak ditemukan pada dataset: {sorted(hilang)}. "
            f"Kolom yang tersedia: {list(df.columns)}"
        )

    # Coerce memaksa tanggal tidak valid menjadi NaT alih-alih melempar error,
    # sehingga baris rusak bisa dilaporkan dengan jelas oleh validate_dataset.
    df[cfg.COL_TANGGAL] = pd.to_datetime(df[KOLOM_SUMBER_TANGGAL], errors="coerce")
    df[cfg.COL_HARGA] = pd.to_numeric(df[KOLOM_SUMBER_HARGA], errors="coerce")

    df = df.dropna(subset=[cfg.COL_TANGGAL, cfg.COL_HARGA])
    df = df[[cfg.COL_TANGGAL, cfg.COL_HARGA]].copy()
    df[cfg.COL_TANGGAL] = df[cfg.COL_TANGGAL].dt.to_period("M").dt.to_timestamp()
    df[cfg.COL_TAHUN] = df[cfg.COL_TANGGAL].dt.year
    df[cfg.COL_BULAN] = df[cfg.COL_TANGGAL].dt.month
    df[cfg.COL_BULAN_NAMA] = df[cfg.COL_BULAN].map(
        lambda m: cfg.BULAN_NAMA[m - 1] if 1 <= m <= 12 else None
    )

    return df.sort_values(cfg.COL_TANGGAL).reset_index(drop=True)


def validate_dataset(df: pd.DataFrame, path: str | Path = "dataset.csv") -> list[str]:
    """Kembalikan daftar peringatan kualitas data (kosong berarti data bersih)."""
    peringatan: list[str] = []
    awal = len(df)

    if awal == 0:
        return [f"Dataset '{path}' tidak berisi satu pun baris yang valid."]

    jumlah_mentah = len(pd.read_csv(path))

    if awal < jumlah_mentah:
        peringatan.append(
            f"{jumlah_mentah - awal} baris dibuang karena tanggal atau harga tidak valid."
        )

    duplikat = int(df[cfg.COL_TANGGAL].duplicated().sum())
    if duplikat:
        peringatan.append(f"{duplikat} tanggal duplikat ditemukan.")

    rentang = (
        f"{df[cfg.COL_TANGGAL].min():%Y-%m} sampai {df[cfg.COL_TANGGAL].max():%Y-%m}"
    )
    hilang_bulan = (
        len(pd.period_range(df[cfg.COL_TANGGAL].min(), df[cfg.COL_TANGGAL].max(), freq="M"))
        - awal
    )
    if hilang_bulan > 0:
        peringatan.append(
            f"{hilang_bulan} bulan berurutan tidak ada di dataset (rentang data: {rentang})."
        )

    if (df[cfg.COL_HARGA] <= 0).any():
        peringatan.append("Terdapat harga nol atau negatif.")

    return peringatan


def saring(df: pd.DataFrame, tahun: int | None = None, bulan: int | None = None) -> pd.DataFrame:
    """Saring berdasarkan tahun dan/atau bulan. ``None`` berarti semua."""
    hasil = df
    if tahun is not None:
        hasil = hasil[hasil[cfg.COL_TAHUN] == tahun]
    if bulan is not None:
        hasil = hasil[hasil[cfg.COL_BULAN] == bulan]
    return hasil.reset_index(drop=True)


def deret_harga(df: pd.DataFrame) -> pd.Series:
    """Ambil deret harga sebagai numpy float64 untuk pyFTS."""
    return df[cfg.COL_HARGA].to_numpy(dtype=float)


def label_bulan(bulan: int) -> str:
    """Ubah angka bulan menjadi nama Indonesia."""
    return cfg.BULAN_NAMA[bulan - 1] if 1 <= bulan <= 12 else str(bulan)