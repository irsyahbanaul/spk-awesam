"""Logika inti SPK Penjadwalan & Perencanaan Kapasitas MTO-MTS (Konveksi AWESAM).
Semua data/parameter default adalah CONTOH/ASUMSI, bukan data asli."""
import math
from dataclasses import dataclass, replace
from datetime import date, timedelta
import numpy as np
import pandas as pd

PRODUK = ["Kaos polos", "Kaos sablon", "Polo", "Rompi/Jaket"]


@dataclass
class Params:
    penjahit: int = 14
    potong: int = 2
    jam_kerja: float = 8.0
    efisiensi: float = 0.85
    hari_minggu: int = 5
    reservasi_mto: float = 0.70
    lembur_jam: float = 0.0          # jam lembur tambahan per hari
    mulai: date = date(2026, 11, 23)  # harus hari kerja
    tarif_dalam: float = 4000
    tarif_luar: float = 5250
    faktor_lembur: float = 1.25
    batas_lembur_hari: float = 4
    batas_lembur_minggu: float = 18
    ambang_berisiko: int = 1
    toleransi_lembur_minggu: float = 2
    lead_rekanan_hari: int = 5        # ASUMSI: lama pengerjaan rekanan (hari kerja)

    @property
    def batas_lembur_efektif(self):
        return min(self.batas_lembur_hari, self.batas_lembur_minggu / self.hari_minggu)


def default_waktu_baku():
    return pd.DataFrame(
        {"produk": PRODUK,
         "jam_jahit": [0.12, 0.12, 0.20, 0.45],
         "jam_potong": [0.02, 0.02, 0.03, 0.05],
         "lead_hari": [1, 3, 2, 2]}).set_index("produk")


def sample_orders():
    d = lambda m, dd: date(2026, m, dd)
    rows = [
        ("MTO-001", "Panitia Dies Natalis", "Kaos sablon", 255, d(11, 26), "MTO"),
        ("MTO-002", "Komunitas Lari Malang", "Kaos polos", 205, d(11, 27), "MTO"),
        ("MTO-003", "SMA Contoh A", "Polo", 155, d(11, 30), "MTO"),
        ("MTO-004", "Himpunan Mahasiswa", "Kaos sablon", 410, d(12, 1), "MTO"),
        ("MTO-005", "Toko Seragam B", "Kaos polos", 340, d(12, 2), "MTO"),
        ("MTO-006", "Kantor Desa C", "Rompi/Jaket", 100, d(12, 2), "MTO"),
        ("MTO-007", "Event Organizer D", "Kaos sablon", 305, d(12, 3), "MTO"),
        ("MTO-008", "Klub Sepeda E", "Polo", 185, d(12, 3), "MTO"),
        ("MTO-009", "Koperasi F", "Kaos polos", 240, d(12, 4), "MTO"),
        ("MTO-010", "Bimbel G", "Kaos sablon", 160, d(12, 4), "MTO"),
        ("MTO-011", "Panitia Wisuda", "Polo", 270, d(12, 7), "MTO"),
        ("MTO-012", "Pesantren H", "Kaos polos", 375, d(12, 7), "MTO"),
        ("MTO-013", "Dealer Motor I", "Rompi/Jaket", 135, d(12, 8), "MTO"),
        ("MTO-014", "Sekolah J", "Kaos sablon", 220, d(12, 8), "MTO"),
        ("MTO-015", "UKM Kuliner K", "Polo", 120, d(12, 9), "MTO"),
        ("MTO-016", "Karang Taruna L", "Kaos polos", 290, d(12, 9), "MTO"),
        ("MTO-017", "Perusahaan M", "Polo", 340, d(12, 10), "MTO"),
        ("MTO-018", "Komunitas Hobi N", "Kaos sablon", 205, d(12, 10), "MTO"),
        ("MTO-019", "Yayasan O", "Kaos polos", 255, d(12, 11), "MTO"),
        ("MTO-020", "Hotel P", "Rompi/Jaket", 155, d(12, 11), "MTO"),
        ("MTO-021", "Event Natal Q", "Kaos sablon", 270, d(12, 11), "MTO"),
        ("MTO-022", "Toko Online R", "Kaos polos", 12, d(12, 3), "MTO"),
        ("MTO-023", "Panitia Seminar S", "Kaos sablon", 170, d(12, 1), "MTO"),
        ("MTO-024", "Instansi T", "Polo", 145, d(12, 9), "MTO"),
        ("MTS-001", "Stok toko - kaos polos", "Kaos polos", 510, d(12, 4), "MTS"),
        ("MTS-002", "Stok toko - kaos sablon", "Kaos sablon", 340, d(12, 9), "MTS"),
        ("MTS-003", "Stok toko - polo", "Polo", 205, d(12, 11), "MTS"),
    ]
    return pd.DataFrame(rows, columns=["no_order", "pelanggan", "produk", "qty", "dateline", "tipe"])


def _dt(x):
    return np.datetime64(pd.Timestamp(x).date())


def workday(start, n):
    """Setara Excel WORKDAY(start-1, n): hari kerja ke-n mulai dari 'start' (Senin-Jumat)."""
    return pd.Timestamp(np.busday_offset(_dt(start) - np.timedelta64(1, "D"), int(n), roll="backward"))


def kapasitas_harian(p: Params):
    eff_jam = p.jam_kerja + p.lembur_jam
    return dict(jahit=p.penjahit * eff_jam * p.efisiensi,
                potong=p.potong * eff_jam * p.efisiensi)


def _siapkan(orders, wb):
    df = orders.copy().reset_index(drop=True)
    df["dateline"] = pd.to_datetime(df["dateline"])
    df = df[df["no_order"].astype(str).str.len() > 0].copy()
    df["jam_jahit"] = df["qty"] * df["produk"].map(wb["jam_jahit"])
    df["jam_potong"] = df["qty"] * df["produk"].map(wb["jam_potong"])
    df["lead"] = df["produk"].map(wb["lead_hari"])
    return df


def _status(finish, dateline, ambang):
    if finish > dateline:
        return "Terlambat"
    slack = int(np.busday_count(_dt(finish), _dt(dateline) + np.timedelta64(1, "D"))) - 1
    return "Kritis" if slack <= ambang else "Aman"


def jadwal(orders, wb, p: Params, reservasi=None):
    """Jadwalkan order MTO dengan aturan EDD. Return DataFrame (urut EDD).
    tambahan: dict(jam_jahit, jam_potong) = beban order baru yang disisipkan (what-if)."""
    res = p.reservasi_mto if reservasi is None else reservasi
    cap = kapasitas_harian(p)
    df = _siapkan(orders, wb)
    m = df[df["tipe"] == "MTO"].copy()
    m["_i"] = range(len(m))
    m["waktu_proses"] = m["jam_jahit"] + m["jam_potong"]          # SPT sebagai pemecah seri
    m = m.sort_values(["dateline", "waktu_proses", "_i"], kind="stable").reset_index(drop=True)
    m["urutan"] = m.index + 1
    m["kum_jahit"] = m["jam_jahit"].cumsum()
    m["kum_potong"] = m["jam_potong"].cumsum()
    m["hari_produksi"] = [max(math.ceil(a / (cap["jahit"] * res)), math.ceil(b / (cap["potong"] * res)))
                          for a, b in zip(m["kum_jahit"], m["kum_potong"])]
    m["estimasi_selesai"] = [workday(p.mulai, h + l) for h, l in zip(m["hari_produksi"], m["lead"])]
    m["selisih_hari"] = (m["dateline"] - m["estimasi_selesai"]).dt.days
    m["status"] = [_status(f, d, p.ambang_berisiko) for f, d in zip(m["estimasi_selesai"], m["dateline"])]
    return m.drop(columns=["_i"])


def cek_dateline(orders, wb, p: Params, produk, qty, dateline):
    """Order promising: simulasikan sisip order baru berdasar EDD."""
    dateline = pd.Timestamp(dateline)
    cap = kapasitas_harian(p)
    res = p.reservasi_mto
    jj = qty * wb.loc[produk, "jam_jahit"]
    jp = qty * wb.loc[produk, "jam_potong"]
    lead = int(wb.loc[produk, "lead_hari"])
    base = jadwal(orders, wb, p)
    pre = base[base["dateline"] <= dateline]
    kj = pre["jam_jahit"].sum() + jj
    kp = pre["jam_potong"].sum() + jp
    hari = max(math.ceil(kj / (cap["jahit"] * res)), math.ceil(kp / (cap["potong"] * res)))
    selesai = workday(p.mulai, hari + lead)
    selisih = (dateline - selesai).days
    # dampak ke order lain (dateline lebih lama): beban kumulatif bertambah
    post = base[base["dateline"] > dateline]
    baru_telat = []
    for _, r in post.iterrows():
        h = max(math.ceil((r["kum_jahit"] + jj) / (cap["jahit"] * res)),
                math.ceil((r["kum_potong"] + jp) / (cap["potong"] * res)))
        f = workday(p.mulai, h + r["lead"])
        if f > r["dateline"] and r["status"] != "Terlambat":
            baru_telat.append(r["no_order"])
    if selisih >= 0:
        if not baru_telat:
            rek, kode = f"TERIMA – estimasi selesai {selesai:%d/%m/%Y}, tidak mengganggu order lain.", "terima"
        else:
            rek, kode = (f"NEGOSIASI – order baru bisa tepat waktu, tetapi {len(baru_telat)} order lain jadi "
                         f"terlambat. Pertimbangkan lembur/rekanan."), "negosiasi"
    elif -selisih <= 3:
        rek, kode = f"NEGOSIASI – usulkan dateline {selesai:%d/%m/%Y} (lewat {-selisih} hari).", "negosiasi"
    else:
        rek, kode = (f"TOLAK / REKANAN – butuh {-selisih} hari lebih lama dari dateline; usulkan dateline "
                     f"{selesai:%d/%m/%Y} atau alihkan ke rekanan."), "tolak"
    return dict(jam_jahit=jj, jam_potong=jp, lead=lead, hari_produksi=hari, estimasi_selesai=selesai,
                selisih=selisih, order_terdampak=baru_telat, rekomendasi=rek, kode=kode)


def kapasitas_mingguan(orders, wb, p: Params, n_minggu=6):
    """Beban vs kapasitas per minggu untuk stasiun potong DAN jahit, lengkap dengan peringatan."""
    cap = kapasitas_harian(p)
    df = _siapkan(orders, wb)
    tot = {"jahit": cap["jahit"] * p.hari_minggu, "potong": cap["potong"] * p.hari_minggu}
    rows, kum = [], {"jahit": 0.0, "potong": 0.0}
    kumcap = {"jahit": 0.0, "potong": 0.0}
    for i in range(n_minggu):
        mulai = pd.Timestamp(p.mulai) + pd.Timedelta(days=7 * i)
        akhir = mulai + pd.Timedelta(days=6)
        lo = pd.Timestamp("1900-01-01") if i == 0 else mulai
        row = {"Minggu": i + 1, "Mulai": mulai, "Akhir": akhir}
        warn, kurang = [], False
        for st_, kol in (("jahit", "jam_jahit"), ("potong", "jam_potong")):
            sel = df[(df["dateline"] >= lo) & (df["dateline"] <= akhir)]
            b_mto = sel[sel["tipe"] == "MTO"][kol].sum()
            b_mts = sel[sel["tipe"] == "MTS"][kol].sum()
            util = (b_mto + b_mts) / tot[st_]
            kum[st_] += b_mto; kumcap[st_] += tot[st_] * p.reservasi_mto
            nm = st_.capitalize()
            row.update({f"Kapasitas {nm} (jam)": tot[st_], f"Beban MTO {nm} (jam)": b_mto,
                        f"Beban MTS {nm} (jam)": b_mts, f"Utilisasi {nm}": util,
                        f"Selisih MTO kum. {nm} (jam)": kumcap[st_] - kum[st_]})
            if util > 1:
                warn.append(f"{nm} melebihi kapasitas ({util:.0%})")
            if kumcap[st_] - kum[st_] < 0:
                kurang = True
        row["Status"] = "Kekurangan kapasitas" if kurang else "Cukup"
        row["Peringatan"] = "; ".join(warn) if warn else "OK"
        rows.append(row)
    return pd.DataFrame(rows)


def keputusan(jadwal_df, p: Params):
    """Bandingkan lembur / rekanan / kombinasi untuk order yang terlambat (biaya + tanggal selesai)."""
    telat = jadwal_df[jadwal_df["status"] == "Terlambat"]
    pcs = float(telat["qty"].sum()); jam_j = float(telat["jam_jahit"].sum()); jam_p = float(telat["jam_potong"].sum())
    cap = kapasitas_harian(p)
    lim = p.batas_lembur_efektif                       # dikunci: <=4 jam/hari & <=18 jam/minggu
    ex_j = p.penjahit * lim * p.efisiensi              # tambahan kapasitas lembur per hari
    ex_p = p.potong * lim * p.efisiensi
    hari_full = 0 if pcs == 0 else (99 if min(ex_j, ex_p) == 0 else
                                     max(math.ceil(jam_j / ex_j), math.ceil(jam_p / ex_p)))
    tol_hari = p.toleransi_lembur_minggu * p.hari_minggu
    layak_a = hari_full <= tol_hari
    frac = 1.0 if hari_full == 0 else min(1.0, tol_hari / hari_full)
    pcs_l = pcs * frac; pcs_o = pcs - pcs_l
    hari_c = math.ceil(hari_full * frac)
    tgl = lambda h: workday(p.mulai, max(h, 1)) if pcs else None
    tgl_a = tgl(hari_full) if hari_full < 99 else None
    tgl_b = tgl(p.lead_rekanan_hari)
    tgl_c = None
    if pcs:
        tgl_c = tgl(max(hari_c, p.lead_rekanan_hari if pcs_o > 0 else 0))
    c_lembur = p.tarif_dalam * p.faktor_lembur
    tabel = pd.DataFrame([
        {"Opsi": "A. Lembur penuh", "Pcs lembur": pcs, "Pcs rekanan": 0, "Biaya (Rp)": pcs * c_lembur,
         "Hari lembur": hari_full, "Tanggal selesai": tgl_a, "Layak": "Layak" if layak_a else "Tidak layak"},
        {"Opsi": "B. Rekanan penuh", "Pcs lembur": 0, "Pcs rekanan": pcs, "Biaya (Rp)": pcs * p.tarif_luar,
         "Hari lembur": 0, "Tanggal selesai": tgl_b, "Layak": "Layak"},
        {"Opsi": "C. Kombinasi", "Pcs lembur": pcs_l, "Pcs rekanan": pcs_o,
         "Biaya (Rp)": pcs_l * c_lembur + pcs_o * p.tarif_luar, "Hari lembur": hari_c,
         "Tanggal selesai": tgl_c, "Layak": "Layak"}])
    if len(telat) == 0:
        rek = "Tidak perlu tindakan: semua order MTO terjadwal aman."
    elif layak_a:
        rek = (f"Lembur penuh – biaya terendah dan dalam batas aturan "
               f"({hari_full} hari lembur, selesai {tgl_a:%d/%m/%Y}).")
    else:
        rek = (f"Kombinasi – lembur ±{pcs_l:,.0f} pcs ({hari_c} hari, maks. {p.toleransi_lembur_minggu:g} minggu) + "
               f"rekanan {pcs_o:,.0f} pcs; selesai {tgl_c:%d/%m/%Y}.")
    return dict(n_telat=len(telat), pcs=pcs, jam=jam_j, kap_lembur=ex_j * p.hari_minggu,
                tabel=tabel, rekomendasi=rek)


def urutan_harian(jadwal_df, p: Params, tanggal, stasiun):
    """Daftar kerja harian per stasiun ('jahit'/'potong') mengikuti urutan EDD+SPT."""
    tanggal = pd.Timestamp(tanggal)
    if tanggal.weekday() >= 5 or tanggal < pd.Timestamp(p.mulai):
        return pd.DataFrame()
    d = int(np.busday_count(_dt(p.mulai), _dt(tanggal))) + 1
    cap = kapasitas_harian(p)[stasiun] * p.reservasi_mto
    kol = "jam_jahit" if stasiun == "jahit" else "jam_potong"
    kum = jadwal_df[kol].cumsum()
    out = []
    for (_, r), k in zip(jadwal_df.iterrows(), kum):
        prev = k - r[kol]
        if int(prev // cap) + 1 <= d <= math.ceil(k / cap):
            jam = min(k, d * cap) - max(prev, (d - 1) * cap)
            per_pcs = r[kol] / r["qty"]
            out.append({"Urutan": int(r["urutan"]), "No Order": r["no_order"], "Pelanggan": r["pelanggan"],
                        "Produk": r["produk"], "Qty order": int(r["qty"]),
                        "Target hari ini (pcs)": int(round(jam / per_pcs)), "Dateline": r["dateline"],
                        "Status": r["status"]})
    return pd.DataFrame(out)
