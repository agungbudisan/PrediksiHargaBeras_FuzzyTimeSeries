"""Tema visual: CSS kustom agar tampilan terasa rapi dan formal."""

from __future__ import annotations

import streamlit as st

from . import config as cfg

CSS = f"""
<style>
  .stApp {{ background: {cfg.WARNA['latar']}; }}

  /* ---------- Judul ---------- */
  h1, h2, h3 {{ letter-spacing: -0.01em; }}
  .app-subtitle {{
      color: {cfg.WARNA['abu']};
      font-size: 1.02rem;
      line-height: 1.55;
      margin-top: -0.6rem;
      margin-bottom: 1.2rem;
      max-width: 60rem;
  }}

  /* ---------- Kartu metrik ---------- */
  .kartu {{
      background: #FFFFFF;
      border: 1px solid #E6E3DC;
      border-radius: 14px;
      padding: 1rem 1.1rem;
      height: 100%;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }}
  .kartu-label {{
      font-size: 0.74rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: {cfg.WARNA['abu']};
      margin-bottom: 0.35rem;
  }}
  .kartu-nilai {{
      font-size: 1.65rem;
      font-weight: 650;
      color: {cfg.WARNA['hijau']};
      line-height: 1.15;
  }}
  .kartu-catatan {{
      font-size: 0.78rem;
      color: {cfg.WARNA['abu']};
      margin-top: 0.3rem;
  }}

  /* ---------- Info blok metodologi ---------- */
  .metode {{
      background: #F3F1EA;
      border-left: 4px solid {cfg.WARNA['emas']};
      border-radius: 0 10px 10px 0;
      padding: 0.85rem 1.05rem;
      font-size: 0.88rem;
      line-height: 1.6;
      color: #3A3A3A;
      margin: 0.4rem 0 1rem 0;
  }}

  /* ---------- Tabel & sidebar ---------- */
  [data-testid="stSidebar"] {{
      background: #FFFFFF;
      border-right: 1px solid #E6E3DC;
  }}
  [data-testid="stSidebar"] h3 {{
      color: {cfg.WARNA['hijau']};
      font-size: 0.95rem;
  }}

  /* ---------- Footer ---------- */
  .footer {{
      margin-top: 3rem;
      padding-top: 1rem;
      border-top: 1px solid #E6E3DC;
      font-size: 0.78rem;
      color: {cfg.WARNA['abu']};
      line-height: 1.6;
  }}

  /* ---------- Hero ---------- */
  .hero {{
      background: linear-gradient(120deg, {cfg.WARNA['hijau']} 0%, {cfg.WARNA['hijau_muda']} 100%);
      color: #FFFFFF;
      border-radius: 16px;
      padding: 1.5rem 1.7rem;
      margin-bottom: 1.4rem;
  }}
  .hero h1 {{
      color: #FFFFFF;
      font-size: 1.75rem;
      margin: 0 0 0.35rem 0;
  }}
  .hero p {{
      color: rgba(255,255,255,0.92);
      margin: 0;
      font-size: 0.97rem;
      line-height: 1.5;
  }}
  .hero .tag {{
      display: inline-block;
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.35);
      border-radius: 999px;
      padding: 0.15rem 0.7rem;
      font-size: 0.74rem;
      margin-top: 0.7rem;
  }}
</style>
"""


def terapkan() -> None:
    """Suntikkan CSS ke halaman Streamlit."""
    st.markdown(CSS, unsafe_allow_html=True)


def kartu_metrik(label: str, nilai: str, catatan: str = "") -> str:
    """Kembalikan HTML untuk satu kartu metrik."""
    catatan_html = f'<div class="kartu-catatan">{catatan}</div>' if catatan else ""
    return (
        f'<div class="kartu">'
        f'<div class="kartu-label">{label}</div>'
        f'<div class="kartu-nilai">{nilai}</div>'
        f'{catatan_html}'
        f"</div>"
    )