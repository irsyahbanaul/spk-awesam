# SPK Penjadwalan & Perencanaan Kapasitas MTO–MTS – Konveksi AWESAM (prototipe)
Data & parameter = CONTOH/ASUMSI (bukan data asli).

## Jalankan lokal
    pip install -r requirements.txt
    streamlit run app.py

## Akun demo (ganti sebelum dipakai sungguhan)
| Pengguna | Peran | Kata sandi |
|---|---|---|
| admin | Admin Produksi | admin123 |
| kepro | Kepala Produksi | kepro123 |
| jahit | Kepala Jahit | jahit123 |
| potong | Kepala Potong | potong123 |

Untuk akun sungguhan: isi `[users.<nama>]` (name, role, hash) di `.streamlit/secrets.toml`; hash dibuat dengan
`store._hash("kata-sandi")`.

## Struktur
- `app.py` antarmuka & navigasi per peran · `logic.py` model (EDD+SPT, kapasitas, lembur/rekanan, urutan harian)
- `store.py` basis data SQLite (`data/awesam.db`, dibuat otomatis) & login
- `assets/` logo (timpa `logo.png`, `logo_light.png`, `icon.png` dengan logo asli) · `.streamlit/config.toml` tema

## Deploy (Streamlit Community Cloud)
Unggah ke GitHub → share.streamlit.io → main file `app.py`.
Catatan: penyimpanan SQLite di Community Cloud bersifat sementara (hilang saat aplikasi restart/redeploy);
cukup untuk demo, bukan untuk data produksi.
