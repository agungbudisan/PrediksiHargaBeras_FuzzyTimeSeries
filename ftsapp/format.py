"""Format angka gaya Indonesia.

Konvensi yang dipakai: pemisah ribuan memakai titik (``.``) dan pemisah
desimal memakai koma (``,``), misalnya ``Rp 13.500,75``.

Plotly tidak punya Locale bawaan, sehingga label sumbu dan nilai pada hover
juga perlu diformat ulang di sini — memformat ulang secara manual lebih
dibanding hopesi plotly menampilkan ``1,234.5`` gaya Inggris.
"""

from __future__ import annotations

import math

_PENANDA = "\x00"


def angka(nilai: float, desimal: int = 0) -> str:
    """Format angka gaya Indonesia: ``13500.75`` -> ``13.500,75``."""
    kasar = f"{nilai:,.{desimal}f}"
    # Tukar sementara agar titik (desimal) dan koma ( ribuan ) tidak saling menimpa.
    return kasar.replace(",", _PENANDA).replace(".", ",").replace(_PENANDA, ".")


def rupiah(nilai: float, desimal: int = 0) -> str:
    """Format nominal uang: ``13500.75`` -> ``Rp 13.500,75``."""
    return f"Rp {angka(nilai, desimal)}"


def persen(nilai: float, desimal: int = 2) -> str:
    """Format persentase: ``1.8532`` -> ``1,85%``."""
    return f"{angka(nilai, desimal)}%"


def tick_rupiah(nilai_min: float, nilai_max: float, jumlah: int = 6) -> tuple[list[float], list[str]]:
    """Buat pasangan ``(tickvals, ticktext)`` dengan label gaya Indonesia.

    Plotly memilih posisi tick-nya sendiri bila diberi ``tickvals``, sehingga
    nilai dan label harus dihitung bersamaan agar tetap sejajar.
    """
    if not math.isfinite(nilai_min) or not math.isfinite(nilai_max):
        return [], []
    if nilai_max <= nilai_min:
        nilai_max = nilai_min + 1.0

    kasar = (nilai_max - nilai_min) / max(jumlah - 1, 1)
    magnitud = 10 ** math.floor(math.log10(kasar)) if kasar > 0 else 1.0
    langkah = magnitud
    for pengali in (1, 2, 2.5, 5, 10):
        if kasar <= pengali * magnitud:
            langkah = pengali * magnitud
            break

    nilai = math.floor(nilai_min / langkah) * langkah
    tickvals: list[float] = []
    # Toleransi kecil agar tick terakhir yang sedikit di atas maks tetap diambil.
    while nilai <= nilai_max + langkah * 1e-9:
        tickvals.append(round(nilai, 10))
        nilai += langkah

    # Sesuaikan presisi label dengan besar langkahnya.
    desimal = max(0, min(2, -int(math.floor(math.log10(langkah))) if langkah < 1 else 0))
    return tickvals, [angka(v, desimal) for v in tickvals]