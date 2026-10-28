import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "prediksi_diabetes.db"

# ── Database ──────────────────────────────────────────────
def init_db():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS pasien (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_pasien     TEXT    NOT NULL,
                usia            INTEGER NOT NULL,
                gula_darah      REAL    NOT NULL,
                bmi             REAL    NOT NULL,
                riwayat_ortu    TEXT    NOT NULL,
                hasil_prediksi  TEXT    NOT NULL
            )
        """)

def simpan_pasien(nama, usia, gula, bmi, riwayat, hasil):
    with sqlite3.connect(DB_NAME) as con:
        con.execute(
            "INSERT INTO pasien (nama_pasien, usia, gula_darah, bmi, riwayat_ortu, hasil_prediksi) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nama, usia, gula, bmi, riwayat, hasil)
        )

def ambil_semua_pasien():
    with sqlite3.connect(DB_NAME) as con:
        return con.execute(
            "SELECT id, nama_pasien, usia, gula_darah, bmi, riwayat_ortu, hasil_prediksi FROM pasien"
        ).fetchall()

def hapus_pasien(id_pasien: int):
    with sqlite3.connect(DB_NAME) as con:
        con.execute("DELETE FROM pasien WHERE id = ?", (id_pasien,))

def hapus_semua_pasien():
    with sqlite3.connect(DB_NAME) as con:
        con.execute("DELETE FROM pasien")

# ── Logika prediksi ───────────────────────────────────────
WARNA_RISIKO = {
    "Rendah":       "#27ae60",
    "Waspada":      "#f39c12",
    "Sedang":       "#e67e22",
    "Tinggi":       "#e74c3c",
    "Sangat Tinggi":"#8e1a0e",
}

def prediksi(gula, bmi, riwayat_ya: bool) -> str:
    if gula >= 200:
        return "Sangat Tinggi" if (bmi >= 30 or riwayat_ya) else "Tinggi"
    if gula >= 140:
        if bmi >= 30 and riwayat_ya:
            return "Tinggi"
        if bmi >= 30 or riwayat_ya:
            return "Sedang"
        return "Sedang"
    # gula < 140
    if bmi >= 30:
        return "Sedang" if riwayat_ya else "Waspada"
    return "Waspada" if riwayat_ya else "Rendah"

# ── Jendela Lihat Data ────────────────────────────────────
class JendelaData(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Riwayat Data Pasien")
        self.geometry("880x480")
        self.configure(bg="#f0f4f8")
        self.resizable(True, True)
        self._build()

    def _build(self):
        cols = ("ID", "Nama Pasien", "Usia", "Gula Darah", "BMI", "Riwayat Ortu", "Hasil Prediksi")

        tree_frame = tk.Frame(self, bg="#f0f4f8")
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(16, 4))

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=16,
                                  selectmode="extended")
        widths = (40, 180, 60, 100, 70, 110, 130)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        sb_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        for risiko, warna in WARNA_RISIKO.items():
            self.tree.tag_configure(risiko, foreground=warna)

        # ── Tombol ──
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🗑  Hapus Data Terpilih",
                  font=("Helvetica", 10, "bold"), bg="#e74c3c", fg="white",
                  padx=14, pady=7, relief="flat", cursor="hand2",
                  command=self._hapus_terpilih).pack(side="left", padx=8)

        tk.Button(btn_frame, text="⚠  Hapus Semua Data",
                  font=("Helvetica", 10, "bold"), bg="#8e1a0e", fg="white",
                  padx=14, pady=7, relief="flat", cursor="hand2",
                  command=self._hapus_semua).pack(side="left", padx=8)

        self._muat_data()

    def _muat_data(self):
        self.tree.delete(*self.tree.get_children())
        for row in ambil_semua_pasien():
            self.tree.insert("", "end", values=row, tags=(row[6],))

    def _hapus_terpilih(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Hapus", "Pilih baris yang ingin dihapus terlebih dahulu.", parent=self)
            return
        nama = self.tree.item(selected[0], "values")[1]
        jumlah = len(selected)
        konfirmasi = (f"Hapus data pasien '{nama}'?"
                      if jumlah == 1 else f"Hapus {jumlah} data yang dipilih?")
        if not messagebox.askyesno("Konfirmasi", konfirmasi, parent=self):
            return
        for item in selected:
            hapus_pasien(int(self.tree.item(item, "values")[0]))
        self._muat_data()

    def _hapus_semua(self):
        if not ambil_semua_pasien():
            messagebox.showinfo("Hapus Semua", "Database sudah kosong.", parent=self)
            return
        if not messagebox.askyesno("Konfirmasi",
                                    "Hapus SELURUH data pasien?\nTindakan ini tidak dapat dibatalkan.",
                                    icon="warning", parent=self):
            return
        hapus_semua_pasien()
        self._muat_data()

def buka_lihat_data():
    JendelaData()

# ── Aplikasi Utama ────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Prediksi Risiko Diabetes")
        self.geometry("480x560")
        self.resizable(False, False)
        self.configure(bg="#f0f4f8")
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg="#2980b9", pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🩺 Prediksi Risiko Diabetes",
                 font=("Helvetica", 17, "bold"), bg="#2980b9", fg="white").pack()
        tk.Label(hdr, text="Sistem Deteksi Dini Berbasis Faktor Risiko",
                 font=("Helvetica", 9), bg="#2980b9", fg="#d6eaf8").pack()

        # ── Form ──
        form = tk.Frame(self, bg="#f0f4f8", padx=30, pady=20)
        form.pack(fill="both", expand=True)

        fields = [
            ("Nama Pasien",       "nama"),
            ("Usia (tahun)",      "usia"),
            ("Gula Darah (mg/dL)","gula"),
            ("BMI (kg/m²)",       "bmi"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(form, text=label, font=("Helvetica", 10, "bold"),
                     bg="#f0f4f8", anchor="w").grid(row=i, column=0, sticky="w", pady=6)
            var = tk.StringVar()
            tk.Entry(form, textvariable=var, font=("Helvetica", 11),
                     width=28, relief="groove", bd=2).grid(row=i, column=1, padx=(10,0), pady=6)
            self.vars[key] = var

        # Riwayat orang tua
        tk.Label(form, text="Riwayat Diabetes Orang Tua",
                 font=("Helvetica", 10, "bold"), bg="#f0f4f8", anchor="w").grid(
                     row=4, column=0, sticky="w", pady=6)
        self.var_riwayat = tk.StringVar(value="Tidak")
        cb = ttk.Combobox(form, textvariable=self.var_riwayat,
                          values=["Ya", "Tidak"], state="readonly",
                          font=("Helvetica", 11), width=26)
        cb.grid(row=4, column=1, padx=(10,0), pady=6)

        # ── Tombol ──
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="🔍  Prediksi", font=("Helvetica", 11, "bold"),
                  bg="#2980b9", fg="white", padx=18, pady=8, relief="flat",
                  cursor="hand2", command=self.jalankan_prediksi).pack(side="left", padx=8)

        tk.Button(btn_frame, text="📋  Lihat Data", font=("Helvetica", 11, "bold"),
                  bg="#27ae60", fg="white", padx=18, pady=8, relief="flat",
                  cursor="hand2", command=buka_lihat_data).pack(side="left", padx=8)

        tk.Button(btn_frame, text="🗑  Reset", font=("Helvetica", 11, "bold"),
                  bg="#7f8c8d", fg="white", padx=18, pady=8, relief="flat",
                  cursor="hand2", command=self.reset_form).pack(side="left", padx=8)

        # ── Hasil ──
        hasil_frame = tk.Frame(self, bg="#f0f4f8")
        hasil_frame.pack(fill="x", padx=30, pady=(10, 20))

        tk.Label(hasil_frame, text="Hasil Prediksi :", font=("Helvetica", 10, "bold"),
                 bg="#f0f4f8").pack(anchor="w")

        self.lbl_hasil = tk.Label(hasil_frame, text="—", font=("Helvetica", 20, "bold"),
                                   bg="#ecf0f1", fg="#555", width=28, pady=10,
                                   relief="groove", bd=2)
        self.lbl_hasil.pack(pady=4)

        self.lbl_info = tk.Label(hasil_frame, text="", font=("Helvetica", 9),
                                  bg="#f0f4f8", fg="#555", wraplength=400, justify="center")
        self.lbl_info.pack()

    # ── Validasi ──────────────────────────────────────────
    def _validasi(self):
        nama = self.vars["nama"].get().strip()
        if not nama:
            messagebox.showwarning("Validasi", "Nama pasien tidak boleh kosong.")
            return None

        try:
            usia = int(self.vars["usia"].get())
            assert 1 <= usia <= 120
        except (ValueError, AssertionError):
            messagebox.showwarning("Validasi", "Usia harus bilangan bulat antara 1–120.")
            return None

        try:
            gula = float(self.vars["gula"].get())
            assert 0 < gula <= 600
        except (ValueError, AssertionError):
            messagebox.showwarning("Validasi", "Gula darah harus angka antara 1–600 mg/dL.")
            return None

        try:
            bmi = float(self.vars["bmi"].get())
            assert 5 <= bmi <= 80
        except (ValueError, AssertionError):
            messagebox.showwarning("Validasi", "BMI harus angka antara 5–80 kg/m².")
            return None

        return nama, usia, gula, bmi

    # ── Aksi ──────────────────────────────────────────────
    def jalankan_prediksi(self):
        data = self._validasi()
        if data is None:
            return
        nama, usia, gula, bmi = data
        riwayat = self.var_riwayat.get()
        hasil = prediksi(gula, bmi, riwayat == "Ya")

        warna = WARNA_RISIKO[hasil]
        self.lbl_hasil.config(text=f"Risiko : {hasil}", fg=warna, bg="#ecf0f1")

        info_map = {
            "Rendah":       "Kondisi baik. Pertahankan pola hidup sehat.",
            "Waspada":      "Ada faktor risiko. Pantau rutin kadar gula dan berat badan.",
            "Sedang":       "Risiko moderat. Konsultasikan ke dokter dan ubah pola makan.",
            "Tinggi":       "Risiko tinggi. Segera konsultasikan ke dokter.",
            "Sangat Tinggi":"Risiko sangat tinggi. Segera periksakan diri ke tenaga medis!",
        }
        self.lbl_info.config(text=info_map[hasil], fg=warna)

        simpan_pasien(nama, usia, gula, bmi, riwayat, hasil)

    def reset_form(self):
        for var in self.vars.values():
            var.set("")
        self.var_riwayat.set("Tidak")
        self.lbl_hasil.config(text="—", fg="#555", bg="#ecf0f1")
        self.lbl_info.config(text="")


if __name__ == "__main__":
    init_db()
    App().mainloop()
