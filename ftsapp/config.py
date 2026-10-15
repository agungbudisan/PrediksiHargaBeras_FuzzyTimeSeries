"""Konfigurasi terpusat: metadata aplikasi, konstanta domain, dan palet warna."""

from __future__ import annotations

APP_TITLE = "Prediksi Harga Beras Premium Jawa Barat"
APP_SUBTITLE = (
    "Analisis & peramalan harga beras kualitas premium di tingkat penggilingan "
    "Provinsi Jawa Barat menggunakan Fuzzy Time Series (Chen, 1996)."
)

COL_TANGGAL = "Tanggal"
COL_HARGA = "Harga"
COL_TAHUN = "Tahun"
COL_BULAN = "Bulan"
COL_BULAN_NAMA = "BulanNama"

# `BulanNama` memakai nama Indonesia. Posisi dalam daftar ini SENGAJA menjadi
# angka bulan (1 = Januari) karena dipakai untuk memetakan label ke kolom
# tanggal. Jangan mengubah urutan tanpa menyesuaikan pemetaannya.
BULAN_NAMA = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

TAHUN_MIN = 2019
TAHUN_MAX = 2023

# pyFTS 1.6 melempar ValueError untuk npart < 3 ("fuzzy set index must be
# between 0 and npart"), jadi slider tidak boleh menawarkan nilai di bawah 3.
# Nilai lama di main.py (1..20) bisa membuat aplikasi crash saat digeser.
N_PART_MIN = 3
N_PART_MAX = 20
N_PART_DEFAULT = 8

# Palet earth-tone yang konsisten antara CSS, matplotlib, dan plotly.
WARNA = {
    "hijau": "#1F4E3D",
    "hijau_muda": "#4E8A6E",
    "emas": "#C9A227",
    "terakota": "#B5643C",
    "biru": "#2E6E8E",
    "abu": "#6B7280",
    "latar": "#FAFAF7",
    "teks": "#1A1A1A",
}