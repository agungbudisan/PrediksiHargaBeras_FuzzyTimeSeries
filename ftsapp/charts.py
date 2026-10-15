"""Pembuat grafik (Plotly) dan render himpunan fuzzy (Matplotlib).

Semua angka pada sumbu dan tooltip diformat gaya Indonesia lewat
:mod:`ftsapp.format` (pemisah ribuan titik, desimal koma).
"""

from __future__ import annotations

import io
import warnings
from typing import Sequence

import pandas as pd
import plotly.graph_objects as go

from . import config as cfg
from .format import rupiah, tick_rupiah

_FON = "Source Sans Pro, Segoe UI, sans-serif"


def _customdata(nilai: Sequence[float]) -> list[str]:
    """Label rupiah siap tampil untuk tooltip."""
    return [rupiah(v, 2) for v in nilai]


def _sumbu_keuangan(fig: go.Figure, nilai_y: Sequence[float], judul_y: str = "Harga (Rp)") -> None:
    """Terapkan tema, grid, dan label sumbu Y bergaya Indonesia."""
    fig.update_layout(
        template="simple_white",
        height=430,
        margin=dict(l=10, r=10, t=60, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        font=dict(family=_FON, size=13, color=cfg.WARNA["teks"]),
    )
    fig.update_xaxes(gridcolor="#E8E6E1", zeroline=False)
    vals, labels = tick_rupiah(min(nilai_y), max(nilai_y)) if len(nilai_y) else ([], [])
    fig.update_yaxes(
        title_text=judul_y,
        gridcolor="#E8E6E1",
        zeroline=False,
        tickmode="array",
        tickvals=vals,
        ticktext=labels,
    )


def garis_harga(df: pd.DataFrame) -> go.Figure:
    """Grafik garis harga bulanan."""
    y = df[cfg.COL_HARGA].tolist()
    fig = go.Figure(
        go.Scatter(
            x=df[cfg.COL_TANGGAL],
            y=y,
            customdata=_customdata(y),
            mode="lines+markers",
            name="Harga",
            line=dict(color=cfg.WARNA["hijau"], width=2.5),
            marker=dict(size=5),
            hovertemplate="<b>%{x|%B %Y}</b><br>Harga: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(title="Tren Harga Beras Premium Bulanan")
    _sumbu_keuangan(fig, y)
    return fig


def batang_harga_bulanan(df: pd.DataFrame) -> go.Figure:
    """Grafik batang harga per bulan, dikelompokkan menurut tahun."""
    fig = go.Figure()
    semua: list[float] = []
    for tahun, grup in df.groupby(cfg.COL_TAHUN):
        grup = grup.set_index(cfg.COL_BULAN).reindex(range(1, 13))
        y = grup[cfg.COL_HARGA].tolist()
        semua.extend([v for v in y if pd.notna(v)])
        fig.add_trace(
            go.Bar(
                x=cfg.BULAN_NAMA,
                y=y,
                customdata=_customdata(y),
                name=str(tahun),
                hovertemplate="<b>%{x}</b><br>Harga: %{customdata}<extra></extra>",
            )
        )
    tahun_urut = ", ".join(str(t) for t in sorted(df[cfg.COL_TAHUN].unique()))
    fig.update_layout(title=f"Harga per Bulan ({tahun_urut})", barmode="group")
    _sumbu_keuangan(fig, semua or [0, 1])
    return fig


def perbandingan_aktual_prediksi(
    tanggal: Sequence, aktual: Sequence[float], prediksi: Sequence[float], judul: str
) -> go.Figure:
    """Grafik aktual vs prediksi."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(tanggal),
            y=list(aktual),
            customdata=_customdata(aktual),
            mode="lines",
            name="Aktual",
            line=dict(color=cfg.WARNA["hijau"], width=2.5),
            hovertemplate="<b>%{x|%B %Y}</b><br>Aktual: %{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(tanggal),
            y=list(prediksi),
            customdata=_customdata(prediksi),
            mode="lines",
            name="Prediksi",
            line=dict(color=cfg.WARNA["emas"], width=2.5, dash="dash"),
            hovertemplate="<b>%{x|%B %Y}</b><br>Prediksi: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(title=judul)
    _sumbu_keuangan(fig, list(aktual) + list(prediksi))
    return fig


def grafik_peramalan(
    tanggal_riwayat: Sequence,
    harga_riwayat: Sequence[float],
    tanggal_depan: Sequence,
    harga_depan: Sequence[float],
) -> go.Figure:
    """Grafik riwayat + garis peramalan ke depan."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(tanggal_riwayat),
            y=list(harga_riwayat),
            customdata=_customdata(harga_riwayat),
            mode="lines",
            name="Historis",
            line=dict(color=cfg.WARNA["hijau"], width=2.5),
            hovertemplate="<b>%{x|%B %Y}</b><br>Historis: %{customdata}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=list(tanggal_depan),
            y=list(harga_depan),
            customdata=_customdata(harga_depan),
            mode="lines+markers",
            name="Peramalan",
            line=dict(color=cfg.WARNA["emas"], width=2.5, dash="dash"),
            marker=dict(size=7),
            hovertemplate="<b>%{x|%B %Y}</b><br>Peramalan: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(title="Peramalan Harga Beras ke Depan")
    _sumbu_keuangan(fig, list(harga_riwayat) + list(harga_depan))
    return fig


def grafik_error_waktu(hasil: pd.DataFrame) -> go.Figure:
    """Bar plot error per waktu (aktual - prediksi)."""
    y = hasil["Error"].tolist()
    warna = [cfg.WARNA["terakota"] if e < 0 else cfg.WARNA["hijau_muda"] for e in y]
    fig = go.Figure(
        go.Bar(
            x=hasil["Tanggal"],
            y=y,
            customdata=_customdata(y),
            marker_color=warna,
            hovertemplate="<b>%{x|%B %Y}</b><br>Error: %{customdata}<extra></extra>",
        )
    )
    fig.add_hline(y=0, line=dict(color=cfg.WARNA["abu"], width=1))
    fig.update_layout(
        title="Error per Periode (Aktual − Prediksi)",
        template="simple_white",
        height=320,
        margin=dict(l=10, r=10, t=50, b=10),
        font=dict(family=_FON, size=13, color=cfg.WARNA["teks"]),
    )
    fig.update_xaxes(gridcolor="#E8E6E1")
    vals, labels = tick_rupiah(min(y), max(y))
    fig.update_yaxes(
        title_text="Error (Rp)",
        gridcolor="#E8E6E1",
        zeroline=False,
        tickmode="array",
        tickvals=vals,
        ticktext=labels,
    )
    return fig


def kurva_partisi(kurva: pd.DataFrame, terpilih: int) -> go.Figure:
    """RMSE out-of-sample terhadap jumlah partisi."""
    y = kurva["RMSE"].tolist()
    fig = go.Figure(
        go.Scatter(
            x=kurva["Jumlah Partisi"],
            y=y,
            customdata=_customdata(y),
            mode="lines+markers",
            name="RMSE (uji)",
            line=dict(color=cfg.WARNA["biru"], width=2.5),
            marker=dict(size=7),
            hovertemplate="<b>%{x} partisi</b><br>RMSE: %{customdata}<extra></extra>",
        )
    )
    fig.add_vline(
        x=terpilih,
        line=dict(color=cfg.WARNA["emas"], width=2, dash="dot"),
        annotation_text=f"dipakai: {terpilih}",
        annotation_position="top",
    )
    fig.update_layout(
        title="Pengaruh Jumlah Partisi terhadap Error (data uji)",
        template="simple_white",
        height=380,
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(family=_FON, size=13, color=cfg.WARNA["teks"]),
    )
    fig.update_xaxes(title_text="Jumlah Partisi (npart)", gridcolor="#E8E6E1")
    vals, labels = tick_rupiah(min(y), max(y))
    fig.update_yaxes(
        title_text="RMSE (Rp)",
        gridcolor="#E8E6E1",
        zeroline=False,
        tickmode="array",
        tickvals=vals,
        ticktext=labels,
    )
    return fig


def render_himpunan_fuzzy(model, n_data: int) -> bytes:
    """Render memberships fuzzy set ke PNG bytes.

    Dirender via Agg + BytesIO supaya tidak bergantung pada instance pyplot
    global yang sudah deprecated di Streamlit modern.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.set_xlim(0, max(n_data, 1))
    ax.set_ylim(-0.1, 0.1)

    with warnings.catch_warnings():
        # pyFTS memanggil set_ticklabels() tanpa FixedLocator; kosmetik saja
        # dan membingungkan di log Streamlit.
        warnings.simplefilter("ignore", UserWarning)
        model.partitioner.plot(ax)

    ax.set_title("Derajat Keanggotaan Fuzzy Set", fontsize=14)
    ax.set_xlabel("Indeks data")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()