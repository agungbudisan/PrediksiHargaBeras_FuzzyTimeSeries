"""Kompatibilitas dengan pustaka pihak ketiga.

pyFTS 1.6 masih memakai alias numpy yang sudah dihapus (lihat
``env/Lib/site-packages/pyFTS/partitioners/partitioner.py`` pada baris yang
memakai ``np.int``). NumPy >= 1.24 menghapus alias tersebut, sehingga
``model.fit()`` akan melempar ``AttributeError``.

Modul ini harus diimpor sebelum pyFTS digunakan. ``fts_model`` mengimpornya
secara otomatis, jadi kode aplikasi tidak perlu memikul responsibility ini.
"""

from __future__ import annotations

import numpy as np

# Guard agar aman bila dipanggil berulang kali.
if not hasattr(np, "int"):
    np.int = int  # type: ignore[attr-defined]