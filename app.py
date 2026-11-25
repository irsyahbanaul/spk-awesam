"""SPK Penjadwalan & Perencanaan Kapasitas MTO–MTS – Konveksi AWESAM (prototipe).
Jalankan:  streamlit run app.py     |  Akun demo: lihat halaman login.
Data & parameter default = CONTOH/ASUMSI (bukan data asli AWESAM)."""
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st
import logic as L
import store

st.set_page_config(page_title="SPK AWESAM", page_icon="🧵", layout="wide")
store.init()
ss = st.session_state
ASSETS = Path(__file__).parent / "assets"
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]

CSS = """
<style>
.stApp {background:#F5F4EF;}
[data-testid="stHeader"] {background:transparent;}
.block-container {padding-top:1.2rem; max-width:1280px;}
h1,h2,h3,h4 {color:#1B3550;}
/* Sidebar */
[data-testid="stSidebar"] {background:#1B3550; border-right:none;}
[data-testid="stSidebar"] * {color:#DCE6F0;}
[data-testid="stSidebarNavLink"] {border-radius:10px; padding:.4rem .8rem; margin-bottom:2px; border-left:3px solid transparent;}
[data-testid="stSidebarNavLink"]:hover {background:rgba(255,255,255,.07);}
[data-testid="stSidebarNavLink"][aria-current="page"] {background:rgba(255,255,255,.12); border-left:3px solid #D9B77E;}
[data-testid="stSidebarNavLink"][aria-current="page"] span {color:#FFFFFF; font-weight:700;}
[data-testid="stNavSectionHeader"] {text-transform:uppercase; letter-spacing:.08em; font-size:.68rem; opacity:.65;}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.15);}
[data-testid="stSidebar"] .stButton button {background:transparent; border:1px solid rgba(255,255,255,.35); color:#fff;}
[data-testid="stSidebar"] .stButton button:hover {background:rgba(255,255,255,.1);}
/* Top bar & cards */
.topbar {display:flex; justify-content:space-between; color:#6B7C8F; font-size:.85rem; padding:.2rem 0 .9rem 0;
         border-bottom:1px solid #E3E1D8; margin-bottom:1.2rem;}
.pt {font-size:2.1rem; font-weight:800; color:#1B3550; margin:.1rem 0 0 0; line-height:1.2;}
.ps {color:#6B7C8F; margin:.2rem 0 1.2rem 0;}
.kpi {background:#fff; border:1px solid #E6E4DB; border-radius:16px; padding:16px 18px; height:132px;}
.kpi.dark {background:linear-gradient(135deg,#2C5F8A,#1F4468); border-color:#1F4468;}
.kpi .kl {font-size:.82rem; color:#6B7C8F;} .kpi .kv {font-size:1.55rem; font-weight:800; color:#1B3550; margin:.55rem 0 .25rem 0;}
.kpi .ks {font-size:.74rem; color:#8A97A6;}
.kpi.dark .kl,.kpi.dark .kv,.kpi.dark .ks {color:#fff;}
.kpi.red .kv {color:#B3402A;} .kpi.amber .kv {color:#A87400;} .kpi.green .kv {color:#2E7D4F;}
.card {background:#fff; border:1px solid #E6E4DB; border-radius:16px; padding:18px 20px; margin-bottom:14px;}
div[data-testid="stDataFrame"] {border:1px solid #E6E4DB; border-radius:12px; overflow:hidden;}
.stButton button[kind="primary"], .stFormSubmitButton button {background:#1B3550; border:none; color:#fff; border-radius:10px;}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)

STATUS_COLOR = {"Terlambat": "#F8CBAD", "Kritis": "#FFE699", "Aman": "#C6E0B4",
                "Kekurangan kapasitas": "#F8CBAD", "Cukup": "#C6E0B4", "Layak": "#C6E0B4",
                "Tidak layak": "#F8CBAD", "Menunggu": "#FFE699", "Disetujui": "#C6E0B4", "Ditolak": "#F8CBAD"}
warna = lambda v: f"background-color: {STATUS_COLOR[v]}" if v in STATUS_COLOR else ""


def warn_cell(v):
    return "background-color: #F8CBAD" if isinstance(v, str) and "melebihi" in v else ""


def fmt_tgl(df, cols):
    df = df.copy()
    for c in cols:
        df[c] = pd.to_datetime(df[c]).dt.strftime("%d/%m/%Y")
    return df


def kpi(label, value, sub="", cls=""):
    return f'<div class="kpi {cls}"><div class="kl">{label}</div><div class="kv">{value}</div><div class="ks">{sub}</div></div>'


def page_header(title, subtitle=""):
    t = datetime.now()
    st.markdown(f'<div class="topbar"><span>Konveksi AWESAM · SPK Penjadwalan MTO–MTS</span>'
                f'<span>{t.day} {BULAN[t.month - 1]} {t.year}</span></div>'
                f'<div class="pt">{title}</div><div class="ps">{subtitle}</div>', unsafe_allow_html=True)


# =============================== LOGIN ===============================
if "user" not in ss:
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl']{display:none}</style>",
                unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.write(""); st.write("")
        st.image(str(ASSETS / "logo.png"), width=300)
        st.markdown('<div class="pt" style="font-size:1.6rem">Masuk ke SPK Produksi</div>'
                    '<div class="ps">Sistem pendukung keputusan penjadwalan & kapasitas MTO–MTS.</div>',
                    unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Nama pengguna")
            pw = st.text_input("Kata sandi", type="password")
            ok = st.form_submit_button("Masuk", width="stretch")
        if ok:
            user = store.login(u, pw)
            if user:
                ss.user = user
                st.rerun()
            st.error("Nama pengguna atau kata sandi salah.")
        with (st.expander("Akun demo (prototipe)") if not store.pakai_secrets() else st.container()):
          if not store.pakai_secrets():
            st.table(pd.DataFrame([(u_, store.ROLE_LABEL[v[1]], v[2]) for u_, v in store.DEMO_USERS.items()],
                                  columns=["Pengguna", "Peran", "Kata sandi"]))
            st.caption("Hapus akun demo dan gunakan st.secrets sebelum dipakai sungguhan.")
    st.stop()

user = ss.user
ROLE = user["role"]
KP, ADM = ROLE == "kepala_produksi", ROLE == "admin_produksi"

# =============================== STATE & PARAMETER ===============================
PD = dict(p_penjahit=14, p_potong=2, p_jam=8.0, p_efisiensi=0.85, p_reservasi=0.70, p_lembur=0.0,
          p_mulai=date(2026, 11, 23), p_tarif_dalam=4000, p_tarif_luar=5250, p_faktor=1.25,
          p_ambang=1, p_toleransi=2.0, p_lead=5)
if "cfg_ok" not in ss:
    cfg = store.load_config()
    for k_, v_ in PD.items():
        val = (cfg or {}).get("p", {}).get(k_, v_)
        ss[k_] = date.fromisoformat(val) if k_ == "p_mulai" and isinstance(val, str) else val
    ss.wb_df = (pd.DataFrame(cfg["wb"]).set_index("produk") if cfg and "wb" in cfg else L.default_waktu_baku())
    ss.cfg_ok = True
for k_ in PD:
    ss[k_] = ss[k_]                                # keep-alive antar halaman
ss.setdefault("ed_ver", 0); ss.setdefault("wb_ver", 0)


def get_params():
    return L.Params(penjahit=ss.p_penjahit, potong=ss.p_potong, jam_kerja=ss.p_jam, efisiensi=ss.p_efisiensi,
                    reservasi_mto=ss.p_reservasi, lembur_jam=ss.p_lembur, mulai=ss.p_mulai,
                    tarif_dalam=ss.p_tarif_dalam, tarif_luar=ss.p_tarif_luar, faktor_lembur=ss.p_faktor,
                    ambang_berisiko=ss.p_ambang, toleransi_lembur_minggu=ss.p_toleransi,
                    lead_rekanan_hari=ss.p_lead)


def ctx(need_jadwal=True):
    p, wb, orders = get_params(), ss.wb_df, store.load_orders()
    if p.mulai.weekday() >= 5:
        st.error("Tanggal mulai perencanaan harus hari kerja (Senin–Jumat). Ubah di menu Parameter.")
        st.stop()
    jad = None
    if need_jadwal:
        if not (orders["tipe"] == "MTO").any():
            st.warning("Belum ada order bertipe MTO."); st.stop()
        jad = L.jadwal(orders, wb, p)
    return p, wb, orders, jad


def show_schedule(jad):
    show = fmt_tgl(jad[["urutan", "no_order", "pelanggan", "produk", "qty", "dateline", "hari_produksi",
                        "estimasi_selesai", "selisih_hari", "status"]], ["dateline", "estimasi_selesai"]).rename(
        columns={"urutan": "Urutan", "no_order": "No Order", "pelanggan": "Pelanggan", "produk": "Produk",
                 "qty": "Qty", "dateline": "Dateline", "hari_produksi": "Hari produksi",
                 "estimasi_selesai": "Estimasi selesai", "selisih_hari": "Selisih (hari)", "status": "Status"})
    st.dataframe(show.style.map(warna, subset=["Status"]), width="stretch", hide_index=True)


# =============================== HALAMAN ===============================
def pg_dashboard():
    p, wb, orders, jad = ctx()
    page_header("Dashboard", "Pantau status order, beban stasiun, dan keputusan yang perlu diambil.")
    n = len(jad); cnt = jad["status"].value_counts()
    kap = L.kapasitas_mingguan(orders, wb, p)
    otd = (cnt.get("Aman", 0) + cnt.get("Kritis", 0)) / n
    c = st.columns(5)
    c[0].markdown(kpi("Order MTO aktif", n, f"{int(jad['qty'].sum()):,} pcs total", "dark"), unsafe_allow_html=True)
    c[1].markdown(kpi("Terlambat", int(cnt.get("Terlambat", 0)), "estimasi selesai > dateline", "red"), unsafe_allow_html=True)
    c[2].markdown(kpi("Kritis", int(cnt.get("Kritis", 0)), f"sisa waktu ≤ {p.ambang_berisiko} hari kerja", "amber"), unsafe_allow_html=True)
    c[3].markdown(kpi("Estimasi On-Time Delivery", f"{otd:.0%}", f"{int(cnt.get('Aman', 0))} order aman", "green"), unsafe_allow_html=True)
    uj, up_ = kap["Utilisasi Jahit"].max(), kap["Utilisasi Potong"].max()
    c[4].markdown(kpi("Utilisasi stasiun puncak", f"{max(uj, up_):.0%}", f"jahit {uj:.0%} · potong {up_:.0%}",
                      "red" if max(uj, up_) > 1 else ""), unsafe_allow_html=True)
    st.write("")
    if KP:
        pend = (store.load_persetujuan()["status"] == "Menunggu").sum()
        if pend:
            st.warning(f"**{pend} pengajuan order mendesak** menunggu persetujuan Anda (menu Persetujuan).")
    w = kap[kap["Peringatan"] != "OK"]
    for _, r in w.iterrows():
        st.error(f"⚠️ Minggu {int(r['Minggu'])}: {r['Peringatan']}")
    kp_ = L.keputusan(jad, p)
    st.info("**Rekomendasi:** " + kp_["rekomendasi"])
    a, b = st.columns(2)
    with a:
        st.markdown("**Order yang perlu perhatian**")
        att = jad[jad["status"] != "Aman"][["urutan", "no_order", "pelanggan", "dateline", "estimasi_selesai", "status"]]
        att = fmt_tgl(att, ["dateline", "estimasi_selesai"])
        att.columns = ["Urutan", "No Order", "Pelanggan", "Dateline", "Estimasi selesai", "Status"]
        st.dataframe(att.style.map(warna, subset=["Status"]), hide_index=True, width="stretch", height=300)
    with b:
        st.markdown("**What-if: reservasi kapasitas MTO**")
        sk = pd.DataFrame({"Reservasi MTO": [f"{r:.0%}" for r in (.6, .7, .8, .9)],
                           "Order terlambat": [int((L.jadwal(orders, wb, p, reservasi=r)["status"] == "Terlambat").sum())
                                               for r in (.6, .7, .8, .9)]}).set_index("Reservasi MTO")
        st.bar_chart(sk, height=300, color="#1B3550")
        st.caption("Makin besar jatah MTO → makin sedikit order terlambat, tetapi jatah MTS menyusut.")


def pg_order():
    p, wb, orders, jad = ctx()
    page_header("Order & Jadwal", "Penjadwalan otomatis: Earliest Due Date, pemecah seri Shortest Processing Time.")
    if KP:
        st.markdown("**Daftar order** (Kepala Produksi dapat mengubah data; perubahan disimpan ke basis data)")
        ed = st.data_editor(orders, num_rows="dynamic", width="stretch", key=f"ed_{ss.ed_ver}", column_config={
            "produk": st.column_config.SelectboxColumn("Produk", options=L.PRODUK, required=True),
            "tipe": st.column_config.SelectboxColumn("Tipe", options=["MTO", "MTS"], required=True),
            "qty": st.column_config.NumberColumn("Qty (pcs)", min_value=1, step=1, required=True),
            "dateline": st.column_config.DateColumn("Dateline", format="DD/MM/YYYY", required=True)})
        c1, c2, c3 = st.columns([1, 1, 3])
        if c1.button("💾 Simpan perubahan", type="primary"):
            store.save_orders(ed.dropna(subset=["no_order", "produk", "qty", "dateline", "tipe"]))
            ss.ed_ver += 1; st.rerun()
        if c2.button("Reset data contoh"):
            store.reset_orders(); ss.ed_ver += 1; st.rerun()
        up = st.file_uploader("Atau unggah CSV (no_order, pelanggan, produk, qty, dateline, tipe)", type="csv")
        if up is not None and st.button("Pakai CSV ini"):
            store.save_orders(pd.read_csv(up, parse_dates=["dateline"])); ss.ed_ver += 1; st.rerun()
    else:
        st.caption("Order baru ditambahkan lewat menu Cek Dateline. Perubahan jadwal order mendesak "
                   "harus disetujui Kepala Produksi.")
    st.markdown("**Hasil penjadwalan (urut EDD → SPT)**")
    show_schedule(jad)


def pg_cek():
    p, wb, orders, jad = ctx()
    page_header("Cek Dateline Order Baru", "Kalkulator kelayakan deadline: realistis atau tidak, sebelum order diterima.")
    c1, c2 = st.columns(2)
    pel = c1.text_input("Nama pelanggan", "Pelanggan baru")
    prod = c2.selectbox("Jenis produk", L.PRODUK, index=1)
    c3, c4, c5 = st.columns(3)
    qty = c3.number_input("Qty (pcs)", 1, 100000, 300)
    dl = c4.date_input("Dateline diminta pelanggan", date(2026, 12, 3))
    urgent = c5.checkbox("Order mendesak (menyela jadwal)", help="Order mendesak wajib disetujui Kepala Produksi.")
    r = L.cek_dateline(orders, wb, p, prod, qty, dl)
    {"terima": st.success, "negosiasi": st.warning, "tolak": st.error}[r["kode"]]("**Rekomendasi sistem:** " + r["rekomendasi"])
    m = st.columns(3)
    m[0].markdown(kpi("Estimasi selesai", f"{r['estimasi_selesai']:%d/%m/%Y}", f"lead time tambahan {r['lead']} hari kerja"), unsafe_allow_html=True)
    m[1].markdown(kpi("Selisih ke dateline", f"{r['selisih']} hari", "+ = masih ada sisa waktu"), unsafe_allow_html=True)
    m[2].markdown(kpi("Order lain jadi terlambat", len(r["order_terdampak"]), ", ".join(r["order_terdampak"]) or "tidak ada"), unsafe_allow_html=True)
    st.write("")
    ok_biasa = r["kode"] == "terima" and not urgent
    st.markdown("#### Tindak lanjut")
    if KP:
        if st.button("✅ Masukkan ke jadwal (Kepala Produksi)", type="primary"):
            no = store.add_order(pel, prod, qty, dl); st.success(f"Order {no} dimasukkan ke jadwal."); st.rerun()
    elif ok_biasa:
        if st.button("✅ Terima & masukkan ke jadwal", type="primary"):
            no = store.add_order(pel, prod, qty, dl); st.success(f"Order {no} dimasukkan ke jadwal."); st.rerun()
    else:
        st.info("Order ini mendesak / berisiko mengganggu jadwal, sehingga **harus diajukan ke Kepala Produksi**.")
        with st.form("ajukan"):
            alasan = st.text_area("Alasan / catatan negosiasi dengan pelanggan")
            if st.form_submit_button("📨 Ajukan persetujuan Kepala Produksi"):
                store.ajukan(user["nama"], pel, prod, qty, dl, r["rekomendasi"], alasan)
                st.success("Pengajuan terkirim. Pantau statusnya di menu Persetujuan.")


def pg_kap():
    p, wb, orders, jad = ctx()
    page_header("Kapasitas Stasiun", "Perbandingan beban dan kapasitas stasiun potong & jahit per minggu.")
    kap = L.kapasitas_mingguan(orders, wb, p)
    for _, r in kap[kap["Peringatan"] != "OK"].iterrows():
        st.error(f"⚠️ Minggu {int(r['Minggu'])} ({r['Mulai']:%d/%m}–{r['Akhir']:%d/%m}): {r['Peringatan']}")
    v = pd.DataFrame({"Minggu": kap["Minggu"],
                      "Periode": kap["Mulai"].dt.strftime("%d/%m") + " – " + kap["Akhir"].dt.strftime("%d/%m"),
                      "Kapasitas Jahit (jam)": kap["Kapasitas Jahit (jam)"],
                      "Beban Jahit (jam)": kap["Beban MTO Jahit (jam)"] + kap["Beban MTS Jahit (jam)"],
                      "Utilisasi Jahit": kap["Utilisasi Jahit"],
                      "Kapasitas Potong (jam)": kap["Kapasitas Potong (jam)"],
                      "Beban Potong (jam)": kap["Beban MTO Potong (jam)"] + kap["Beban MTS Potong (jam)"],
                      "Utilisasi Potong": kap["Utilisasi Potong"],
                      "Status": kap["Status"], "Peringatan": kap["Peringatan"]})
    fm = {c: "{:,.0f}" for c in v.columns if "(jam)" in c} | {"Utilisasi Jahit": "{:.0%}", "Utilisasi Potong": "{:.0%}"}
    st.dataframe(v.style.map(warna, subset=["Status"]).map(warn_cell, subset=["Peringatan"]).format(fm),
                 hide_index=True, width="stretch")
    st.markdown("**Utilisasi per minggu (1,0 = 100% kapasitas)**")
    st.bar_chart(kap.set_index("Minggu")[["Utilisasi Potong", "Utilisasi Jahit"]], color=["#D9B77E", "#1B3550"], stack=False)
    st.caption(f"Jatah MTO {p.reservasi_mto:.0%} dari kapasitas; MTS mengisi sisanya. Beban dihitung menurut minggu dateline.")


def pg_keputusan():
    p, wb, orders, jad = ctx()
    page_header("Keputusan Lembur / Rekanan", "Perbandingan opsi untuk order yang terlambat, lengkap dengan biaya dan tanggal selesai.")
    kp_ = L.keputusan(jad, p)
    c = st.columns(4)
    c[0].markdown(kpi("Order terlambat", kp_["n_telat"], "", "red"), unsafe_allow_html=True)
    c[1].markdown(kpi("Pcs terlambat", f"{kp_['pcs']:,.0f}", ""), unsafe_allow_html=True)
    c[2].markdown(kpi("Batas lembur (terkunci)", f"{p.batas_lembur_efektif:.1f} jam/hari", "maks. 4 jam/hari & 18 jam/minggu"), unsafe_allow_html=True)
    c[3].markdown(kpi("Toleransi lembur", f"{p.toleransi_lembur_minggu:g} minggu", "atur di menu Parameter"), unsafe_allow_html=True)
    st.write("")
    t = kp_["tabel"].copy(); t["Tanggal selesai"] = pd.to_datetime(t["Tanggal selesai"]).dt.strftime("%d/%m/%Y").fillna("-")
    st.dataframe(t.style.map(warna, subset=["Layak"]).format(
        {"Pcs lembur": "{:,.0f}", "Pcs rekanan": "{:,.0f}", "Biaya (Rp)": "Rp {:,.0f}"}), hide_index=True, width="stretch")
    st.success("**Rekomendasi:** " + kp_["rekomendasi"])
    st.caption("Pilihan akhir tetap di Kepala Produksi. Tarif, faktor lembur & lead time rekanan = asumsi; "
               "risiko kualitas rekanan dan kelelahan operator belum dimodelkan.")


def pg_harian():
    p, wb, orders, jad = ctx()
    page_header("Urutan Kerja Harian", "Daftar kerja per stasiun untuk Kepala Jahit dan Kepala Potong.")
    default = {"kepala_jahit": 0, "kepala_potong": 1}.get(ROLE, 0)
    c1, c2 = st.columns(2)
    stasiun = c1.radio("Stasiun", ["Jahit", "Potong"], index=default, horizontal=True)
    tgl = c2.date_input("Tanggal", max(date.today(), p.mulai) if date.today() < date(2026, 12, 31) else p.mulai)
    df = L.urutan_harian(jad, p, tgl, stasiun.lower())
    if df.empty:
        st.info("Tidak ada pekerjaan terjadwal pada tanggal ini (akhir pekan, sebelum tanggal mulai, atau semua order sudah selesai).")
        return
    cap = L.kapasitas_harian(p)[stasiun.lower()] * p.reservasi_mto
    st.markdown(kpi(f"Kapasitas MTO stasiun {stasiun.lower()}", f"{cap:,.1f} jam/hari", f"{len(df)} order dikerjakan hari ini"), unsafe_allow_html=True)
    st.write("")
    d = fmt_tgl(df, ["Dateline"])
    st.dataframe(d.style.map(warna, subset=["Status"]), hide_index=True, width="stretch")
    st.download_button("⬇️ Unduh CSV", d.to_csv(index=False).encode(), f"urutan_{stasiun.lower()}_{tgl}.csv", "text/csv")
    st.caption("Kerjakan dari atas ke bawah. Order berstatus Kritis didahulukan jika ada kendala bahan.")


def pg_realisasi():
    p, wb, orders, jad = ctx()
    page_header("Realisasi & Kinerja", "Lembar pencatatan realisasi untuk menghitung ukuran kinerja.")
    rec = store.load_realisasi()
    belum = jad[~jad["no_order"].isin(rec["no_order"])]
    with st.form("real"):
        st.markdown("**Catat realisasi order**")
        a, b, c = st.columns(3)
        opsi = a.selectbox("Order", list(belum["no_order"] + " – " + belum["pelanggan"]) or ["(semua tercatat)"])
        tgl = b.date_input("Tanggal selesai aktual", date.today())
        qty = c.number_input("Qty jadi (pcs)", 0, 100000, 0)
        d, e = st.columns(2)
        lembur = d.number_input("Total jam lembur", 0.0, 500.0, 0.0, 0.5)
        jalur = e.selectbox("Jalur pengerjaan", ["Internal", "Lembur", "Rekanan"])
        if st.form_submit_button("Simpan realisasi") and not belum.empty:
            store.add_realisasi(opsi.split(" – ")[0], tgl, qty, lembur, jalur, user["nama"]); st.rerun()
    if rec.empty:
        st.info("Belum ada realisasi tercatat.")
    else:
        m = rec.merge(orders[["no_order", "pelanggan", "qty", "dateline"]], on="no_order", how="left")
        otd = (m["tgl_selesai"] <= m["dateline"]).mean()
        ofr = m["qty_aktual"].sum() / m["qty"].sum()
        rek = m.loc[m["jalur"] == "Rekanan", "qty_aktual"].sum() / max(m["qty_aktual"].sum(), 1)
        k = st.columns(4)
        k[0].markdown(kpi("On-Time Delivery", f"{otd:.0%}", f"{len(m)} order tercatat", "dark"), unsafe_allow_html=True)
        k[1].markdown(kpi("Order Fulfillment Rate", f"{ofr:.0%}", "qty jadi ÷ qty pesanan"), unsafe_allow_html=True)
        k[2].markdown(kpi("Total jam lembur", f"{m['jam_lembur'].sum():,.1f}", "overtime tracking"), unsafe_allow_html=True)
        k[3].markdown(kpi("Porsi rekanan", f"{rek:.0%}", "pcs rekanan ÷ total pcs"), unsafe_allow_html=True)
        st.write("")
        t = m[["no_order", "pelanggan", "qty", "qty_aktual", "dateline", "tgl_selesai", "jam_lembur", "jalur", "dicatat_oleh"]]
        t = fmt_tgl(t, ["dateline", "tgl_selesai"])
        t.columns = ["No Order", "Pelanggan", "Qty pesan", "Qty jadi", "Dateline", "Selesai aktual", "Jam lembur", "Jalur", "Dicatat oleh"]
        st.dataframe(t, hide_index=True, width="stretch")
        st.download_button("⬇️ Unduh CSV", t.to_csv(index=False).encode(), "realisasi.csv", "text/csv")
    if KP:
        c1, c2 = st.columns(2)
        if c1.button("Muat contoh realisasi (demo)"):
            for i, (_, r) in enumerate(jad.head(8).iterrows()):
                sel = L.workday(p.mulai, r["hari_produksi"] + r["lead"] + [0, 1, 0, 2, 0, 0, 1, 0][i])
                store.add_realisasi(r["no_order"], sel, r["qty"] - (5 if i % 4 == 3 else 0), 4.0 if i % 3 == 0 else 0,
                                    "Lembur" if i % 3 == 0 else "Internal", user["nama"])
            st.rerun()
        if c2.button("Hapus semua realisasi"):
            store.clear_realisasi(); st.rerun()


def pg_persetujuan():
    p, wb, orders, jad = ctx(need_jadwal=False)
    ps = store.load_persetujuan()
    if not KP:
        page_header("Status Pengajuan", "Pantau pengajuan order mendesak yang Anda kirim ke Kepala Produksi.")
        if ps.empty:
            st.info("Belum ada pengajuan.")
        else:
            t = fmt_tgl(ps[["id", "waktu", "pelanggan", "produk", "qty", "dateline", "status", "catatan"]], ["dateline"])
            st.dataframe(t.style.map(warna, subset=["status"]), hide_index=True, width="stretch")
        return
    page_header("Persetujuan Order Mendesak", "Jadwal tidak berubah sebelum Kepala Produksi menyetujui.")
    pend = ps[ps["status"] == "Menunggu"]
    if pend.empty:
        st.success("Tidak ada pengajuan yang menunggu.")
    for _, r in pend.iterrows():
        with st.container(border=True):
            st.markdown(f"**#{r['id']} · {r['pelanggan']}** — {r['produk']}, {r['qty']} pcs, dateline "
                        f"{pd.Timestamp(r['dateline']):%d/%m/%Y}  \nDiajukan oleh {r['pengaju']} ({r['waktu']})")
            cd = L.cek_dateline(orders, wb, p, r["produk"], r["qty"], r["dateline"])
            st.markdown(f"Analisis terkini: {cd['rekomendasi']}")
            if r["alasan"]:
                st.caption("Alasan pengaju: " + r["alasan"])
            cat = st.text_input("Catatan keputusan", key=f"cat{r['id']}")
            a, b, _ = st.columns([1, 1, 4])
            if a.button("✅ Setujui", key=f"ok{r['id']}", type="primary"):
                store.putuskan(int(r["id"]), True, user["nama"], cat); st.rerun()
            if b.button("❌ Tolak", key=f"no{r['id']}"):
                store.putuskan(int(r["id"]), False, user["nama"], cat); st.rerun()
    st.markdown("**Riwayat keputusan**")
    h = ps[ps["status"] != "Menunggu"]
    if not h.empty:
        t = fmt_tgl(h[["id", "waktu", "pelanggan", "produk", "qty", "dateline", "status", "diputuskan_oleh", "catatan"]], ["dateline"])
        st.dataframe(t.style.map(warna, subset=["status"]), hide_index=True, width="stretch")


def pg_parameter():
    page_header("Parameter & Asumsi", "Ganti dengan hasil time study & data AWESAM. Berlaku di semua menu.")
    p = get_params()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Kapasitas**")
        st.number_input("Jumlah penjahit", 1, 100, key="p_penjahit")
        st.number_input("Operator potong", 1, 20, key="p_potong")
        st.number_input("Jam kerja per hari", 1.0, 12.0, step=0.5, key="p_jam")
        st.slider("Efisiensi", 0.5, 1.0, step=0.01, key="p_efisiensi")
        st.date_input("Tanggal mulai perencanaan (hari kerja)", key="p_mulai")
    with c2:
        st.markdown("**Kebijakan**")
        st.slider("Reservasi kapasitas MTO (sisanya MTS)", 0.3, 1.0, step=0.05, key="p_reservasi")
        st.slider(f"Lembur tambahan per hari (jam) – dikunci maks. {p.batas_lembur_efektif:.1f}", 0.0,
                  p.batas_lembur_efektif, step=0.1, key="p_lembur")
        st.number_input("Ambang 'Kritis' (hari kerja sisa)", 0, 5, key="p_ambang")
        st.number_input("Toleransi lama lembur (minggu)", 0.5, 8.0, step=0.5, key="p_toleransi")
    with c3:
        st.markdown("**Biaya & rekanan**")
        st.number_input("Tarif produksi dalam (Rp/pcs)", 0, 100000, step=250, key="p_tarif_dalam")
        st.number_input("Tarif rekanan (Rp/pcs)", 0, 100000, step=250, key="p_tarif_luar")
        st.number_input("Faktor biaya lembur", 1.0, 3.0, step=0.05, key="p_faktor")
        st.number_input("Lead time rekanan (hari kerja)", 1, 30, key="p_lead")
    st.markdown("**Waktu baku & lead time (ASUMSI – ganti dengan hasil time study)**")
    ss.wb_df = st.data_editor(ss.wb_df, key=f"wb_ed_{ss.wb_ver}", width="stretch",
                              column_config={"jam_jahit": "Jam jahit/pcs", "jam_potong": "Jam potong/pcs",
                                             "lead_hari": "Lead time tambahan (hari kerja)"})
    a, b, _ = st.columns([1, 1, 3])
    if a.button("💾 Simpan parameter", type="primary"):
        store.save_config({"p": {k: (ss[k].isoformat() if k == "p_mulai" else ss[k]) for k in PD},
                           "wb": ss.wb_df.reset_index().to_dict("records")})
        st.success("Parameter tersimpan.")
    if b.button("Kembalikan default"):
        for k_, v_ in PD.items():
            ss[k_] = v_
        ss.wb_df = L.default_waktu_baku(); ss.wb_ver += 1; st.rerun()


def pg_petunjuk():
    page_header("Petunjuk", "Ringkasan fungsi alat bantu.")
    st.markdown("""
<div class="card">

**Fungsi utama**
1. **Penjadwalan otomatis** – Earliest Due Date, Shortest Processing Time sebagai pemecah seri, penanda order *Kritis*.
2. **Kalkulator kelayakan deadline** – Admin Produksi langsung tahu deadline realistis atau tidak.
3. **Reservasi kapasitas MTO** – MTO mendapat jatah lebih dulu, MTS mengisi sisanya.
4. **Beban vs kapasitas** stasiun potong & jahit, dengan peringatan bila beban melebihi kapasitas.
5. **Lembur / rekanan / kombinasi** – biaya dan tanggal selesai; batas lembur terkunci 4 jam/hari & 18 jam/minggu (PP 35/2021).
6. **Urutan kerja harian** untuk Kepala Jahit & Kepala Potong, plus **lembar realisasi** untuk ukuran kinerja.
7. **Persetujuan Kepala Produksi** untuk order mendesak agar jadwal tidak diubah sembarangan.

**Peran:** Admin Produksi · Kepala Produksi · Kepala Jahit · Kepala Potong.

**Komponen DSS:** data management (basis data SQLite) · model management (`logic.py`) · antarmuka (Streamlit) · pengambil keputusan (manusia).

**Keterbatasan:** satu stasiun jahit gabungan, tanpa hari libur/setup time; semua angka default adalah asumsi;
login demo bukan untuk produksi.
</div>""", unsafe_allow_html=True)


# =============================== NAVIGASI ===============================
P = lambda fn, title, icon, path: st.Page(fn, title=title, icon=icon, url_path=path)
PG = dict(dash=P(pg_dashboard, "Dashboard", ":material/dashboard:", "dashboard"),
          order=P(pg_order, "Order & Jadwal", ":material/event_note:", "order"),
          cek=P(pg_cek, "Cek Dateline", ":material/fact_check:", "cek"),
          kap=P(pg_kap, "Kapasitas", ":material/bar_chart:", "kapasitas"),
          kep=P(pg_keputusan, "Lembur / Rekanan", ":material/balance:", "keputusan"),
          harian=P(pg_harian, "Urutan Kerja Harian", ":material/checklist:", "harian"),
          real=P(pg_realisasi, "Realisasi & Kinerja", ":material/monitoring:", "realisasi"),
          setuju=P(pg_persetujuan, "Persetujuan" if KP else "Status Pengajuan", ":material/approval:", "persetujuan"),
          param=P(pg_parameter, "Parameter", ":material/tune:", "parameter"),
          info=P(pg_petunjuk, "Petunjuk", ":material/info:", "petunjuk"))
MENU = {
    "admin_produksi": {"Perencanaan": ["dash", "order", "cek", "kap", "kep"], "Eksekusi": ["real", "setuju"], "Bantuan": ["info"]},
    "kepala_produksi": {"Perencanaan": ["dash", "order", "cek", "kap", "kep"], "Eksekusi": ["harian", "real", "setuju"],
                        "Pengaturan": ["param", "info"]},
    "kepala_jahit": {"Pantauan": ["dash"], "Eksekusi": ["harian", "real"], "Bantuan": ["info"]},
    "kepala_potong": {"Pantauan": ["dash"], "Eksekusi": ["harian", "real"], "Bantuan": ["info"]},
}[ROLE]
if (ASSETS / "logo_light.png").exists():
    st.logo(str(ASSETS / "logo_light.png"), icon_image=str(ASSETS / "icon.png"), size="large")
nav = st.navigation({sec: [PG[k] for k in keys] for sec, keys in MENU.items()}, position="sidebar")
if ss.get("prev_page") != nav.title:                    # editor di-reset saat masuk halaman baru
    ss.wb_ver += 1; ss.ed_ver += 1; ss.prev_page = nav.title
with st.sidebar:
    st.divider()
    st.markdown(f"**{user['nama']}**  \n<span style='font-size:.8rem;opacity:.8'>masuk sebagai @{user['username']}</span>",
                unsafe_allow_html=True)
    if st.button("Keluar", key="logout"):
        for k_ in list(ss.keys()):
            del ss[k_]
        st.rerun()
nav.run()
