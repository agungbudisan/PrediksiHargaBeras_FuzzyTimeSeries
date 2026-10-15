"""Dashboard Prediksi Harga Beras Premium — Fuzzy Time Series (Chen).

Jalankan dengan::

    streamlit run main.py

Seluruh logika bisnis berada di paket ``ftsapp``; berkas ini hanya merangkai
antarmuka Streamlit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from ftsapp import charts, config as cfg, data as D, fts_model as M, theme
from ftsapp.format import angka, persen, rupiah

st.set_page_config(
    page_title=cfg.APP_TITLE,
    page_icon="\U0001F33E",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _fmt(nilai: float, desimal: int = 0) -> str:
    """Format angka gaya Indonesia (lihat :mod:`ftsapp.format`)."""
    return angka(nilai, desimal)


def _fmt_rp(nilai: float, desimal: int = 0) -> str:
    return rupiah(nilai, desimal)


# ---------------------------------------------------------------- pemuatan

@st.cache_data(show_spinner=False)
def _muat(path: str) -> pd.DataFrame:
    return D.muat_dataset(path)


@st.cache_data(show_spinner="Mengevaluasi model…")
def _dalam_model(harga: tuple[float, ...], n_part: int):
    return M.evaluasi_dalam_model(np.asarray(harga), n_part)


@st.cache_data(show_spinner="Menjalankan validasi data uji…")
def _uji(harga: tuple[float, ...], n_part: int, n_uji: int):
    return M.evaluasi_uji(np.asarray(harga), n_part, n_uji)


@st.cache_data(show_spinner="Menjalankan rolling-origin…")
def _rolling(harga: tuple[float, ...], n_part: int, min_latih: int, tanggal: tuple):
    return M.evaluasi_rolling(
        np.asarray(harga), n_part, min_latih=min_latih, tanggal=pd.to_datetime(list(tanggal))
    )


@st.cache_data(show_spinner="Menghitung kurva partisi…")
def _kurva(harga: tuple[float, ...]) -> pd.DataFrame:
    return M.kurva_partisi(np.asarray(harga), (cfg.N_PART_MIN, cfg.N_PART_MAX))


@st.cache_resource(show_spinner=False)
def _lator(n_part: int, harga: tuple[float, ...]):
    # cache_resource (bukan cache_data) karena objek model pyFTS tidak pickled.
    return M.latih(np.asarray(harga), n_part)


# ------------------------------------------------------------------ header

def header() -> None:
    st.markdown(
        f"""
        <div class="hero">
          <h1>{cfg.APP_TITLE}</h1>
          <p>{cfg.APP_SUBTITLE}</p>
          <span class="tag">Chen Fuzzy Time Series (1996) · pyFTS</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kartu(nilai: dict[str, str]) -> None:
    """Tampilkan sekumpulan kartu metrik dari dict label → nilai terformat."""
    kolom = st.columns(len(nilai))
    for kol, (label, isi) in zip(kolom, nilai.items()):
        kol.markdown(theme.kartu_metrik(label, isi), unsafe_allow_html=True)


def kartu_dari_metrik(hasil: dict[str, float]) -> None:
    """Kartu metrik untuk dict hasil ``metrics.hitung_semua``."""
    kartu(
        {
            "MAE": _fmt_rp(hasil["MAE"]),
            "RMSE": _fmt_rp(hasil["RMSE"]),
            "MAPE": persen(hasil["MAPE"]),
        }
    )


# -------------------------------------------------------------------- tab

def tab_ringkasan(df_all: pd.DataFrame, df: pd.DataFrame, n_part: int) -> None:
    harga = D.deret_harga(df)

    st.subheader("Ringkasan Data")
    kartu(
        {
            "Jumlah Data": f"{len(df)}",
            "Rata-rata": _fmt_rp(harga.mean()),
            "Tertinggi": _fmt_rp(harga.max()),
            "Terendah": _fmt_rp(harga.min()),
        }
    )

    if len(df) < M.MIN_DATA_LATIH + 1:
        st.warning(
            f"Minimal **{M.MIN_DATA_LATIH + 1} titik** diperlukan untuk evaluasi "
            "latih/uji. Longgarkan filter pada sidebar untuk melihat perbandingan metrik."
        )
        return

    st.markdown("")

    with st.spinner("Menghitung metrik…"):
        uji = _uji(tuple(harga), n_part, 12)
        roll = _rolling(
            tuple(harga), n_part, M.MIN_DATA_LATIH, tuple(df[cfg.COL_TANGGAL])
        )

    metrik_roll = M.metrik_rolling(roll)

    st.subheader("Performa Model")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            theme.kartu_metrik(
                "MAPE — data uji",
                persen(uji.metrik["MAPE"]),
                f"12 bulan terakhir, RMSE {_fmt_rp(uji.metrik['RMSE'])}",
            ),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            theme.kartu_metrik(
                "MAPE — rolling origin",
                persen(metrik_roll["MAPE"]),
                f"{len(roll)} periode, RMSE {_fmt_rp(metrik_roll['RMSE'])}",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""<div class="metode">
        <b>Cara membaca angka ini.</b> Metrik <i>in-sample</i> (pelatihan dan pengujian
        pada data yang sama) cenderung terlalu optimistis karena model sudah "menghafal"
        data tersebut. Angka di atas dihitung pada data yang <b>tidak pernah dilihat model
        saat dilatih</b>, sehingga lebih mencerminkan kemampuan generalisasi.
        </div>""",
        unsafe_allow_html=True,
    )


def tab_data(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    st.subheader("Eksplorasi Data (EDA)")

    peringatan = D.validate_dataset(df_all)
    if peringatan:
        with st.expander(f"Catatan kualitas data ({len(peringatan)})"):
            for p in peringatan:
                st.markdown(f"- {p}")

    st.plotly_chart(charts.garis_harga(df), use_container_width=True)

    st.plotly_chart(charts.batang_harga_bulanan(df), use_container_width=True)

    with st.expander("Tabel data"):
        # Dibangun eksplisit agar tidak ada tabrakan nama kolom (Bulan angka vs Bulan nama).
        tampil = pd.DataFrame(
            {
                "Tanggal": df[cfg.COL_TANGGAL].dt.strftime("%Y-%m"),
                "Bulan": df[cfg.COL_BULAN_NAMA],
                "Tahun": df[cfg.COL_TAHUN],
                "Harga (Rp)": df[cfg.COL_HARGA].round(2),
            }
        )
        st.dataframe(tampil, use_container_width=True, hide_index=True)
        st.download_button(
            "Unduh data terfilter (CSV)",
            tampil.to_csv(index=False).encode("utf-8"),
            file_name="harga_beras_filtered.csv",
            mime="text/csv",
        )

    with st.expander("Statistik deskriptif"):
        st.dataframe(
            df[cfg.COL_HARGA].describe().to_frame("Harga (Rp)"), use_container_width=True
        )


def tab_model(df: pd.DataFrame, n_part: int) -> None:
    st.subheader("Pemodelan Fuzzy Time Series")

    harga = D.deret_harga(df)
    if len(harga) < 4:
        st.warning("Data terlalu sedikit untuk membentuk partisi yang bermakna.")
        return

    model = _lator(n_part, tuple(harga))

    st.plotly_chart(
        charts.perbandingan_aktual_prediksi(
            df[cfg.COL_TANGGAL],
            harga,
            M.prediksi_dalam_model(model, harga),
            "Kesesuaian model terhadap data (in-sample)",
        ),
        use_container_width=True,
    )

    st.markdown("##### Himpunan fuzzy hasil partisi data")
    st.image(charts.render_himpunan_fuzzy(model, len(harga)), use_column_width=True)

    with st.expander("Rincian partisi"):
        st.dataframe(M.rentang_partisi(model), use_container_width=True, hide_index=True)

    with st.expander("Sebaran data pada tiap himpunan fuzzy"):
        st.dataframe(M.sebaran_himpunan(model, harga), use_container_width=True, hide_index=True)

    st.markdown("##### Basis aturan fuzzy logical relationship (FLRG)")
    st.markdown(
        f"""<div class="metode">
        Setiap baris menunjukkan aturan <code>LHS → {{RHS}}</code>. Aturan ini adalah
        "pengetahuan" yang dipakai model untuk memprediksi nilai berikutnya.
        </div>""",
        unsafe_allow_html=True,
    )
    st.dataframe(M.aturan_flrg(model), use_container_width=True, hide_index=True)

    hasil = _dalam_model(tuple(harga), n_part)
    st.caption(
        f"Metrik in-sample (tidak dipakai sebagai ukuran performa utama): {hasil.ringkas()}"
    )


def tab_validasi(df: pd.DataFrame, n_part: int) -> None:
    st.subheader("Validasi Out-of-Sample")

    harga = D.deret_harga(df)
    if len(harga) < M.MIN_DATA_LATIH + 1:
        st.warning(f"Perlu minimal {M.MIN_DATA_LATIH + 1} titik untuk validasi.")
        return

    n_uji = st.slider("Jumlah data uji (bulan terakhir)", 3, 24, 12, step=1)

    uji = _uji(tuple(harga), n_part, n_uji)
    dalam = _dalam_model(tuple(harga), n_part)

    st.markdown("##### Perbandingan metrik")
    st.dataframe(
        pd.DataFrame(
            {
                "Metrik": ["MAE", "RMSE", "MAPE"],
                "In-sample": [
                    angka(dalam.metrik["MAE"], 2),
                    angka(dalam.metrik["RMSE"], 2),
                    persen(dalam.metrik["MAPE"]),
                ],
                f"Data uji ({uji.n_latih} latih / {len(uji.aktual)} uji)": [
                    angka(uji.metrik["MAE"], 2),
                    angka(uji.metrik["RMSE"], 2),
                    persen(uji.metrik["MAPE"]),
                ],
            }
        ).set_index("Metrik"),
        use_container_width=True,
    )

    # `uji.n_latih` adalah titik batas split, jadi data uji adalah potongan ekor.
    tanggal_uji = df[cfg.COL_TANGGAL].iloc[uji.n_latih : uji.n_latih + len(uji.aktual)]

    st.plotly_chart(
        charts.perbandingan_aktual_prediksi(
            pd.to_datetime(tanggal_uji),
            uji.aktual,
            uji.prediksi,
            f"Prediksi pada {len(uji.aktual)} data uji (tidak dilihat saat pelatihan)",
        ),
        use_container_width=True,
    )

    st.markdown("##### Rolling-origin evaluation")
    st.caption(
        "Model dilatih ulang secara berulang pada window yang meluas, lalu memprediksi "
        "satu periode berikutnya. Metodologi ini lebih stabil daripada split tunggal."
    )

    roll = _rolling(tuple(harga), n_part, M.MIN_DATA_LATIH, tuple(df[cfg.COL_TANGGAL]))
    kartu_dari_metrik(M.metrik_rolling(roll))

    st.plotly_chart(charts.grafik_error_waktu(roll), use_container_width=True)
    with st.expander("Tabel hasil rolling-origin"):
        st.dataframe(
            roll[["Tanggal", "Aktual", "Prediksi", "Error", "APE"]].rename(
                columns={
                    "Tanggal": "Tanggal",
                    "Aktual": "Aktual (Rp)",
                    "Prediksi": "Prediksi (Rp)",
                    "Error": "Error (Rp)",
                    "APE": "APE (%)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("##### Tuning jumlah partisi")
    kurva = _kurva(tuple(harga))
    if not kurva.empty:
        st.plotly_chart(charts.kurva_partisi(kurva, n_part), use_container_width=True)
        terbaik = kurva.loc[kurva["RMSE"].idxmin()]
        st.info(
            f"Berdasarkan data uji, jumlah partisi **{int(terbaik['Jumlah Partisi'])}** "
            f"memberikan RMSE terendah (**{_fmt_rp(terbaik['RMSE'])}**). "
            f"Slider saat ini berada di **{n_part}**."
        )


def tab_peramalan(df: pd.DataFrame, n_part: int) -> None:
    st.subheader("Peramalan (Forecasting)")

    harga = D.deret_harga(df)
    if len(harga) < 4:
        st.warning("Data terlalu sedikit untuk melakukan peramalan.")
        return

    langkah = st.slider("Horizon peramalan (bulan)", 1, 12, 6)
    model = _lator(n_part, tuple(harga))
    nilai = M.peramalan(model, harga, langkah)

    tanggal_depan = M.tanggal_masa_depan(df[cfg.COL_TANGGAL].max(), langkah)

    st.plotly_chart(
        charts.grafik_peramalan(
            df[cfg.COL_TANGGAL], harga, tanggal_depan, nilai
        ),
        use_container_width=True,
    )

    # Peringatan hanya muncul bila memang terjadi, bukan asumsi.
    if len({round(v, 6) for v in nilai}) == 1:
        st.warning(
            f"Seluruh {langkah} nilai peramalan bernilai sama "
            f"({_fmt_rp(nilai[0])}). Ini adalah sifat bawaan **Chen first-order "
            "(order = 1)**: aturan basis hanya bergantung pada satu nilai sebelumnya, "
            "sehingga setelah langkah pertama nilai peramalan masuk ke *fixed point*. "
            "Horizon panjang tidak menambah informasi baru pada model ini."
        )

    tabel = pd.DataFrame(
        {
            "Tanggal": pd.to_datetime(tanggal_depan).strftime("%Y-%m"),
            "Peramalan": [rupiah(v, 2) for v in nilai],
        }
    )

    st.markdown("##### Hasil peramalan")
    st.dataframe(tabel, use_container_width=True, hide_index=True)
    st.download_button(
        "Unduh hasil peramalan (CSV)",
        tabel.to_csv(index=False).encode("utf-8"),
        file_name="peramalan_harga_beras.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------------- main

def main() -> None:
    theme.terapkan()
    header()

    # ---------------------------------------------------------- sidebar
    with st.sidebar:
        st.markdown("### Pengaturan Data")
        try:
            df_all = _muat("dataset.csv")
        except (FileNotFoundError, ValueError) as exc:
            st.error(f"Gagal memuat dataset: {exc}")
            return

        tahun_tersedia = sorted(df_all[cfg.COL_TAHUN].unique())
        tahun = st.selectbox(
            "Tahun", ["Semua"] + [str(t) for t in tahun_tersedia], index=0
        )
        bulan = st.selectbox("Bulan", ["Semua"] + cfg.BULAN_NAMA, index=0)

        df = D.saring(
            df_all,
            tahun=None if tahun == "Semua" else int(tahun),
            bulan=None if bulan == "Semua" else cfg.BULAN_NAMA.index(bulan) + 1,
        )

        st.markdown("---")
        st.markdown("### Pengaturan Model")
        n_part = st.slider(
            "Jumlah partisi (npart)",
            cfg.N_PART_MIN,
            cfg.N_PART_MAX,
            cfg.N_PART_DEFAULT,
            help=(
                "Jumlah himpunan fuzzy yang membagi universe of discourse. "
                f"Minimal {cfg.N_PART_MIN} karena pyFTS menolak nilai yang lebih kecil."
            ),
        )

        st.caption(f"Data aktif: **{len(df)}** titik · **{n_part}** partisi")

    # ------------------------------------------------------------ body
    if df.empty:
        st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
        return

    t_ringkasan, t_data, t_model, t_validasi, t_forecast = st.tabs(
        ["Ringkasan", "Data", "Model", "Validasi", "Peramalan"]
    )

    with t_ringkasan:
        tab_ringkasan(df_all, df, n_part)
    with t_data:
        tab_data(df_all, df)
    with t_model:
        tab_model(df, n_part)
    with t_validasi:
        tab_validasi(df, n_part)
    with t_forecast:
        tab_peramalan(df, n_part)

    st.markdown(
        f"""<div class="footer">
        <b>Tugas Besar Kecerdasan Buatan</b> — Analisis dan Peramalan Harga Beras
        Kualitas Premium di Penggilingan Provinsi Jawa Barat.<br/>
        Kelompok 7 · Informatika A/2022 · Universitas Sebelas Maret.
        Metode: Conventional Fuzzy Time Series (Chen, 1996).
        </div>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()