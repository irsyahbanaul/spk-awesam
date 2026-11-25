"""Penyimpanan (SQLite) & autentikasi sederhana untuk prototipe SPK AWESAM.
Catatan: untuk produksi ganti akun demo dengan st.secrets dan basis data terkelola."""
import hashlib, hmac, json, sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import logic as L

DB = Path(__file__).parent / "data" / "awesam.db"

# ---------------- Akun & peran ----------------
# peran: admin_produksi, kepala_produksi, kepala_jahit, kepala_potong
DEMO_USERS = {
    "admin":  ("Admin Produksi", "admin_produksi", "admin123"),
    "kepro":  ("Kepala Produksi", "kepala_produksi", "kepro123"),
    "jahit":  ("Kepala Jahit", "kepala_jahit", "jahit123"),
    "potong": ("Kepala Potong", "kepala_potong", "potong123"),
}
ROLE_LABEL = {"admin_produksi": "Admin Produksi", "kepala_produksi": "Kepala Produksi",
              "kepala_jahit": "Kepala Jahit", "kepala_potong": "Kepala Potong"}
SALT = "awesam-spk-prototipe"


def _hash(pw):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), SALT.encode(), 100_000).hex()


def _users():
    try:
        import streamlit as st
        if "users" in st.secrets:      # [users.admin] name=..., role=..., hash=...
            return {u: (v["name"], v["role"], v["hash"]) for u, v in st.secrets["users"].items()}
    except Exception:
        pass
    return {u: (n, r, _hash(pw)) for u, (n, r, pw) in DEMO_USERS.items()}


def pakai_secrets():
    try:
        import streamlit as st
        return "users" in st.secrets
    except Exception:
        return False


def login(username, password):
    u = _users().get(username.strip().lower())
    if u and hmac.compare_digest(u[2], _hash(password)):
        return {"username": username.strip().lower(), "nama": u[0], "role": u[1]}
    return None


# ---------------- Basis data ----------------
def _c():
    DB.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB)


def init():
    with _c() as c:
        c.execute("create table if not exists orders(no_order text, pelanggan text, produk text, qty integer, dateline text, tipe text)")
        c.execute("create table if not exists realisasi(no_order text, tgl_selesai text, qty_aktual integer, jam_lembur real, jalur text, dicatat_oleh text, waktu text)")
        c.execute("create table if not exists persetujuan(id integer primary key autoincrement, waktu text, pengaju text, pelanggan text, produk text, qty integer, dateline text, rekomendasi text, alasan text, status text, diputuskan_oleh text, catatan text)")
        c.execute("create table if not exists config(k text primary key, v text)")
        if c.execute("select count(*) from orders").fetchone()[0] == 0:
            save_orders(L.sample_orders(), c)


def load_orders():
    with _c() as c:
        df = pd.read_sql("select * from orders", c)
    df["dateline"] = pd.to_datetime(df["dateline"])
    return df


def save_orders(df, c=None):
    d = df.copy()
    d["dateline"] = pd.to_datetime(d["dateline"]).dt.strftime("%Y-%m-%d")
    d = d[["no_order", "pelanggan", "produk", "qty", "dateline", "tipe"]]
    own = c is None
    c = c or _c()
    d.to_sql("orders", c, if_exists="replace", index=False)
    if own:
        c.commit(); c.close()


def reset_orders():
    save_orders(L.sample_orders())


def next_no(prefix="MTO"):
    df = load_orders()
    n = [int(x.split("-")[1]) for x in df["no_order"] if str(x).startswith(prefix + "-") and x.split("-")[1].isdigit()]
    return f"{prefix}-{(max(n) if n else 0) + 1:03d}"


def add_order(pelanggan, produk, qty, dateline, tipe="MTO"):
    no = next_no(tipe)
    with _c() as c:
        c.execute("insert into orders values(?,?,?,?,?,?)",
                  (no, pelanggan, produk, int(qty), pd.Timestamp(dateline).strftime("%Y-%m-%d"), tipe))
    return no


def load_realisasi():
    with _c() as c:
        df = pd.read_sql("select * from realisasi", c)
    df["tgl_selesai"] = pd.to_datetime(df["tgl_selesai"])
    return df


def add_realisasi(no, tgl, qty, lembur, jalur, oleh):
    with _c() as c:
        c.execute("delete from realisasi where no_order=?", (no,))
        c.execute("insert into realisasi values(?,?,?,?,?,?,?)",
                  (no, pd.Timestamp(tgl).strftime("%Y-%m-%d"), int(qty), float(lembur), jalur, oleh,
                   datetime.now().strftime("%Y-%m-%d %H:%M")))


def clear_realisasi():
    with _c() as c:
        c.execute("delete from realisasi")


def load_persetujuan():
    with _c() as c:
        return pd.read_sql("select * from persetujuan order by id desc", c)


def ajukan(pengaju, pelanggan, produk, qty, dateline, rekomendasi, alasan):
    with _c() as c:
        c.execute("insert into persetujuan(waktu,pengaju,pelanggan,produk,qty,dateline,rekomendasi,alasan,status) values(?,?,?,?,?,?,?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), pengaju, pelanggan, produk, int(qty),
                   pd.Timestamp(dateline).strftime("%Y-%m-%d"), rekomendasi, alasan, "Menunggu"))


def putuskan(id_, setuju, oleh, catatan):
    with _c() as c:
        row = c.execute("select pelanggan,produk,qty,dateline from persetujuan where id=?", (id_,)).fetchone()
        c.execute("update persetujuan set status=?, diputuskan_oleh=?, catatan=? where id=?",
                  ("Disetujui" if setuju else "Ditolak", oleh, catatan, id_))
    if setuju and row:
        add_order(*row)


def load_config():
    with _c() as c:
        r = c.execute("select v from config where k='cfg'").fetchone()
    return json.loads(r[0]) if r else None


def save_config(cfg):
    with _c() as c:
        c.execute("insert or replace into config values('cfg',?)", (json.dumps(cfg),))
