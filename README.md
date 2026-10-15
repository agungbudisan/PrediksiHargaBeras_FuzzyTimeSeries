Project Title: Prediksi Harga Beras Kualitas Premium di Penggilingan Provinsi Jawa Barat menurut Bulan Menggunakan Fuzzy Time Series

Project Goal: Membangun model analisis dan peramalan harga beras kualitas premium bulanan di tingkat penggilingan Provinsi Jawa Barat, disajikan melalui dashboard interaktif berbasis Fuzzy Time Series.

## Metode

Conventional Fuzzy Time Series (Chen, 1996) berorder satu, diimplementasikan
lewat pustaka `pyFTS`:
1. Data harga difuzzifikasi menjadi *fuzzy sets* menggunakan partisi grid.
2. Transisi antar fuzzy set membentuk basis aturan fuzzy logical relationship (FLRG).
3. Nilai berikutnya diprediksi lewat titik tengah (*midpoint*) dari himpunan hasil defuzzifikasi.

## Built With

**Python**, **Streamlit** (dashboard), **Plotly** (grafik), **Matplotlib** (visualisasi
himpunan fuzzy), **pandas**/**NumPy** (pengolahan data).

## Fitur

| Tab | Isi |
|-----|-----|
| **Ringkasan** | Statistik data utama dan metrik performa out-of-sample |
| **Data** | EDA: tren harga, grafik batang per bulan, tabel, statistik deskriptif |
| **Model** | Himpunan fuzzy, rincian partisi, sebaran data, basis aturan FLRG |
| **Validasi** | Perbandingan in-sample vs data uji, *rolling-origin evaluation*, kurva tuning `npart` |
| **Peramalan** | Peramalan ke depan + unduh CSV |

### Catatan metodologis

Metrik **in-sample** (pelatihan dan pengujian pada data yang sama) cenderung
terlalu optimistis. Aplikasi sengaja menampilkan perbandingan dengan metrik
**out-of-sample** — split temporal dan *rolling-origin evaluation* — agar
kemampuan generalisasi model dapat dinilai dengan jujur.

Peramalan jangka panjang pada Chen first-order mencapai *fixed point* (nilai
konstan) sejak langkah pertama; hal ini dijelaskan langsung di tab Peramalan,
bukan disembunyikan.

## Struktur Proyek

```
main.py              # Orkestrasi UI Streamlit
dataset.csv          # Data harga bulanan (60 titik, 2019-01 s.d. 2023-12)
requirements.txt
ftsapp/
  config.py          # Metadata, konstanta domain, palet warna
  compat.py          # Patch kompatibilitas numpy untuk pyFTS
  data.py            # Pemuatan, validasi, penyaringan dataset
  metrics.py         # MAE, RMSE, MAPE
  format.py          # Format angka gaya Indonesia (13.500,75)
  fts_model.py       # Latih/prediksi/peramalan + evaluasi out-of-sample
  charts.py          # Pembuat grafik Plotly & render himpunan fuzzy
  theme.py           # Tema visual (CSS)
```

## Getting Started

### Installation

1. Create python environment (Python 3.12)

```sh
python -m venv env
```

2. Activate python environment

for Windows OS
```sh
env\Scripts\activate
```

for Unix Based OS (Linux, MacOS, etc)
```sh
source env/bin/activate
```

3. Install python library

```sh
pip install -r requirements.txt
```

4. Run the app

```sh
streamlit run main.py
```

Aplikasi harus dijalankan dari root repository karena `dataset.csv` dimuat
melalui path relatif.

## Format Angka

Seluruh nominal harga ditulis mengikuti konvensi Indonesia: **pemisah ribuan memakai
titik** dan **pemisah desimal memakai koma**, misalnya `Rp 13.500,75` dan `MAPE 1,85%`.
Implementasi berada di `ftsapp/format.py`; sumbu grafik dan tooltip ikut diformat
ulang karena Plotly tidak mendukung pengaturan locale.

## Catatan Teknis

- **`ftsapp/compat.py`** — pyFTS 1.6 masih memakai alias `np.int` yang dihapus
  pada numpy 1.24. Patch di modul tersebut dijalankan otomatis saat impor.
- **Jumlah partisi** dibatasi mulai dari 3 karena pyFTS melempar `ValueError`
  untuk nilai yang lebih kecil.
- Tidak ada dependensi `pmdarima`, `scikit-learn`, `statsmodels`, atau `seaborn`;
  aplikasi tidak mengimpornya.