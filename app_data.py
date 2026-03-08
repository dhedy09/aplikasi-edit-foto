import streamlit as st
import openpyxl
import io
import re
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
from supabase import create_client, Client
from collections import defaultdict

# ==========================================
# 1. PENGATURAN HALAMAN
# ==========================================
st.set_page_config(page_title="Olah Data & SIPD", layout="wide", page_icon="📊")

# ==========================================
# 2. KONEKSI KE DATABASE SUPABASE
# ==========================================
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Gagal terhubung ke Database. Pastikan SUPABASE_URL dan SUPABASE_KEY sudah ada di Streamlit Secrets!")
    st.stop()

# ==========================================
# 3. SISTEM LOGIN
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terbatas")
    st.write("Aplikasi ini bersifat privat. Silakan masukkan kata sandi untuk melanjutkan.")
    
    with st.form("login_form"):
        password_input = st.text_input("Kata Sandi:", type="password")
        tombol_masuk = st.form_submit_button("Masuk")
        
        if tombol_masuk:
            if password_input == st.secrets["APP_PASSWORD"]: 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Kata sandi salah!")
    st.stop()

# ==========================================
# 4. MENU NAVIGASI MODERN (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>📊 Mamayo Data</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu_pilihan = option_menu(
        menu_title=None,
        options=["Alat Excel", "Import SIPD", "Rekap SIPD"],
        icons=["wrench-adjustable", "cloud-arrow-up-fill", "bar-chart-steps"], 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#ffc107", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#262730"},
            "nav-link-selected": {"background-color": "#0083B8", "color": "white"},
        }
    )
    
    st.markdown("---")
    st.caption("🚀 Dikembangkan dengan Python & Streamlit")


# ==========================================
# 5. KONTEN BERDASARKAN MENU YANG DIPILIH
# ==========================================

# -------------------------------------------------------------------------
# --- MODUL 1: ALAT EXCEL ---
# -------------------------------------------------------------------------
if menu_pilihan == "Alat Excel":
    st.title("🛠️ Manipulasi Petik & Pembersih Karakter")
    st.write("Gunakan alat ini untuk merapikan data Dapodik/SIPD dalam satu kali jalan.")
    
    file_excel = st.file_uploader("📥 Unggah File Excel (.xlsx)", type=["xlsx"], key="excel_upload")
    if file_excel:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 1️⃣ Pengaturan Tanda Petik")
            kolom_petik = st.text_input("🔠 Kolom Petik (Cth: C, D):").upper()
            mode_excel = st.radio("⚙️ Aksi:", ["+ Tambah Petik Tersembunyi", "- Hapus Semua Petik"], horizontal=True)
        with col2:
            st.markdown("#### 2️⃣ Pengaturan Pembersih Karakter")
            kolom_bersih = st.text_input("🧹 Kolom Ekstrak Angka (Cth: F, G):").upper()
            
        if st.button("🚀 PROSES FILE EXCEL", type="primary", use_container_width=True):
            if not kolom_petik and not kolom_bersih:
                st.error("⚠️ Mohon isi minimal salah satu kolom!")
            else:
                with st.spinner("Memproses data..."):
                    try:
                        list_petik = [k.strip() for k in kolom_petik.split(",") if k.strip()]
                        list_bersih = [k.strip() for k in kolom_bersih.split(",") if k.strip()]
                        wb = openpyxl.load_workbook(file_excel)
                        ws = wb.active
                        
                        if list_bersih:
                            for col in list_bersih:
                                for row in range(2, ws.max_row + 1):
                                    cell = ws[f"{col}{row}"]
                                    if cell.value is not None:
                                        val_str = re.sub(r'\D', '', str(cell.value).strip())
                                        cell.value = val_str
                        if list_petik:
                            for col in list_petik:
                                for row in range(2, ws.max_row + 1):
                                    cell = ws[f"{col}{row}"]
                                    if cell.value is not None:
                                        val_str = str(cell.value).strip()
                                        if mode_excel == "+ Tambah Petik Tersembunyi":
                                            val_str = val_str[1:] if val_str.startswith("'") else val_str
                                            cell.value = val_str
                                            cell.quotePrefix = True
                                        else:
                                            cell.value = val_str.replace("'", "")
                                            cell.quotePrefix = False 
                                            cell.number_format = '@'

                        output_excel = io.BytesIO()
                        wb.save(output_excel)
                        output_excel.seek(0)
                        st.success("✅ File berhasil diproses!")
                        st.download_button(
                            label="📥 Download Hasil Excel",
                            data=output_excel,
                            file_name=f"Selesai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_excel.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")

# -------------------------------------------------------------------------
# --- MODUL 2: IMPORT SIPD KE DATABASE ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Import SIPD":
    st.title("☁️ Upload SIPD ke Database Cloud")
    st.write("Data Excel tarikan SIPD akan otomatis diformat dan disimpan ke server Supabase Anda secara permanen.")
    
    col_upload, col_tahapan = st.columns([2, 1])
    
    with col_upload:
        file_sipd = st.file_uploader("Unggah Excel Tarikan SIPD (.xlsx / .xls)", type=["xlsx", "xls"])
        
    with col_tahapan:
        nama_tahapan = st.text_input("🏷️ Nama Tahapan", placeholder="Cth: APBD Pokok 2026")
        
    if file_sipd and nama_tahapan:
        if st.button("⚡ UPLOAD KE DATABASE SUPABASE", type="primary", use_container_width=True):
            with st.spinner("🚀 Sedang menyedot dan mengirim data ke cloud... (Mohon tunggu)"):
                try:
                    df_sipd = pd.read_excel(file_sipd)
                    df_sipd['TAHAPAN'] = nama_tahapan
                    
                    pemetaan_kolom = {
                        "NO": "no_urut",
                        "TAHUN": "tahun",
                        "KODE URUSAN": "kode_urusan",
                        "NAMA URUSAN": "nama_urusan",
                        "KODE SKPD": "kode_skpd",
                        "NAMA SKPD": "nama_skpd",
                        "KODE SUB UNIT": "kode_sub_unit",
                        "NAMA SUB UNIT": "nama_sub_unit",
                        "KODE BIDANG URUSAN": "kode_bidang_urusan",
                        "NAMA BIDANG URUSAN": "nama_bidang_urusan",
                        "KODE PROGRAM": "kode_program",
                        "NAMA PROGRAM": "nama_program",
                        "KODE KEGIATAN": "kode_kegiatan",
                        "NAMA KEGIATAN": "nama_kegiatan",
                        "KODE SUB KEGIATAN": "kode_sub_kegiatan",
                        "NAMA SUB KEGIATAN": "nama_sub_kegiatan",
                        "KODE SUMBER DANA": "kode_sumber_dana",
                        "NAMA SUMBER DANA": "nama_sumber_dana",
                        "KODE REKENING": "kode_rekening",
                        "NAMA REKENING": "nama_rekening",
                        "PAKET/KELOMPOK": "paket_kelompok",
                        "NAMA PAKET/KELOMPOK": "nama_paket_kelompok",
                        "PAGU": "pagu",
                        "TAHAPAN": "tahapan"
                    }
                    df_sipd.rename(columns=pemetaan_kolom, inplace=True)
                    df_sipd = df_sipd.astype(object).where(pd.notnull(df_sipd), None)
                    
                    data_siap_kirim = df_sipd.to_dict(orient='records')
                    jumlah_data = len(data_siap_kirim)
                    ukuran_cicilan = 1000
                    
                    for i in range(0, jumlah_data, ukuran_cicilan):
                        potongan_data = data_siap_kirim[i : i + ukuran_cicilan]
                        supabase.table("rekap_sipd").insert(potongan_data).execute()
                    
                    st.success(f"✅ LUAR BIASA! {jumlah_data} baris data '{nama_tahapan}' berhasil mendarat dengan selamat di Database Supabase!")
                    
                except Exception as e:
                    st.error(f"❌ Gagal mengirim ke database: {e}")
                    
    elif file_sipd and not nama_tahapan:
        st.warning("⚠️ Silakan isi kotak **Nama Tahapan** terlebih dahulu untuk memunculkan tombol upload.")

# --- MODUL 3: REKAP SIPD ---
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Sistem Rekapitulasi SIPD Terpadu")
    st.write("Buat laporan perbandingan Pagu antar tahapan dengan format berjenjang (SKPD hingga Sub Kegiatan).")
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def tarik_data_database():
        semua_data = []
        offset = 0
        limit = 1000
        while True:
            res = supabase.table("rekap_sipd").select("*").range(offset, offset + limit - 1).execute()
            data_tarikan = res.data
            if not data_tarikan:
                break
            semua_data.extend(data_tarikan)
            if len(data_tarikan) < limit:
                break
            offset += limit
        return pd.DataFrame(semua_data)

    with st.spinner("⏳ Menyiapkan data..."):
        try:
            df = tarik_data_database()
        except Exception as e:
            st.error(f"❌ Gagal menarik data dari database: {e}")
            df = pd.DataFrame() 

    if st.button("🔄 Refresh Data Database"):
        tarik_data_database.clear()
        st.rerun()

    if df.empty:
        st.info("💡 Database masih kosong. Silakan Import SIPD terlebih dahulu.")
    else:
        st.success(f"✅ Berhasil memuat {len(df)} baris data!")
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        if 'tahun' not in df.columns:
            st.error("⚠️ Sistem mendeteksi kolom 'tahun' tidak ada di database.")
            st.stop()

        st.markdown("### ⚙️ Pengaturan Filter & Rekap")
        
        # 1. FILTER TAHUN
        list_tahun = sorted(df['tahun'].dropna().unique().tolist(), reverse=True)
        tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", options=list_tahun)
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        # Ambil daftar tahapan
        list_tahapan_tahun = df_tahun['tahapan'].unique().tolist()
        
        col_skpd, col_tahapan = st.columns(2)
        
        # 2. FILTER SKPD
        list_skpd_murni = df_tahun['nama_skpd'].dropna().unique().tolist()
        list_skpd_murni = [str(x).strip() for x in list_skpd_murni if str(x).strip() != ""]
        list_skpd = ["SEMUA SKPD"] + sorted(list_skpd_murni)
        
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Filter SKPD:", options=list_skpd)

        if skpd_pilihan != "SEMUA SKPD":
            df_skpd_valid = df_tahun[df_tahun['nama_skpd'] == skpd_pilihan].copy()
        else:
            df_skpd_valid = df_tahun.copy()

        # 3. FILTER TAHAPAN ACUAN 
        list_tahapan_skpd = df_skpd_valid['tahapan'].unique().tolist()
        with col_tahapan:
            tahapan_acuan = st.selectbox("📍 Acuan Nama & Sumber Dana:", options=list_tahapan_skpd)

        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("🧠 Menghitung dengan Algoritma Master VBA (Akurasi 100%)..."):
                
                df_proses = df_skpd_valid.copy()
                
                if df_proses.empty:
                    st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di database.")
                    st.stop()

                # Bersihkan kolom teks dari nilai kosong (NaN) agar aman dibaca
                kolom_teks = ['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                              'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan', 'nama_sumber_dana', 'tahapan']
                for col in kolom_teks:
                    if col in df_proses.columns:
                        df_proses[col] = df_proses[col].fillna("").astype(str).str.strip()

                # ======================================================================
                # 🛠️ SISTEM DICTIONARY (100% KLONING DARI VBA MACRO ANDA)
                # ======================================================================
                dict_skpd = {}
                dict_urusan = {}
                dict_prog = {}
                dict_keg = {}
                dict_sub = {}

                dict_nama = {}
                dict_pagu = {}
                dict_sd = {}

                # Looping persis seperti "For i = 1 To UBound(vData, 1)" di VBA
                for row in df_proses.itertuples(index=False):
                    kSKPD = row.kode_skpd
                    nSKPD = row.nama_skpd
                    kUrusan = row.kode_urusan
                    nUrusan = row.nama_urusan
                    kProg = row.kode_program
                    nProg = row.nama_program
                    kKeg = row.kode_kegiatan
                    nKeg = row.nama_kegiatan
                    kSub = row.kode_sub_kegiatan
                    nSub = row.nama_sub_kegiatan
                    sd = row.nama_sumber_dana
                    pagu = row.pagu
                    tahapan = row.tahapan

                    # --- SIMPAN NAMA (dictNama) ---
                    if kSKPD not in dict_nama: dict_nama[kSKPD] = nSKPD
                    if kUrusan not in dict_nama: dict_nama[kUrusan] = nUrusan
                    if kProg not in dict_nama: dict_nama[kProg] = nProg
                    if kKeg not in dict_nama: dict_nama[kKeg] = nKeg
                    if kSub not in dict_nama: dict_nama[kSub] = nSub

                    # Paksa nama dari tahapan acuan agar seragam
                    if tahapan == tahapan_acuan:
                        dict_nama[kSKPD] = nSKPD
                        dict_nama[kUrusan] = nUrusan
                        dict_nama[kProg] = nProg
                        dict_nama[kKeg] = nKeg
                        dict_nama[kSub] = nSub

                    # --- BANGUN HIERARKI BERSARANG (dictUrusan, dictProg, dll) ---
                    if kSKPD not in dict_skpd: dict_skpd[kSKPD] = 1
                    
                    if kSKPD not in dict_urusan: dict_urusan[kSKPD] = {}
                    dict_urusan[kSKPD][kUrusan] = 1

                    if kUrusan not in dict_prog: dict_prog[kUrusan] = {}
                    dict_prog[kUrusan][kProg] = 1

                    if kProg not in dict_keg: dict_keg[kProg] = {}
                    dict_keg[kProg][kKeg] = 1

                    if kKeg not in dict_sub: dict_sub[kKeg] = {}
                    dict_sub[kKeg][kSub] = 1

                    # --- TOTAL PAGU (dictPagu) ---
                    # Format: dictPagu(Kode | Tahapan) = Total
                    dict_pagu[f"{kSKPD}|{tahapan}"] = dict_pagu.get(f"{kSKPD}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kUrusan}|{tahapan}"] = dict_pagu.get(f"{kUrusan}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kProg}|{tahapan}"] = dict_pagu.get(f"{kProg}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kKeg}|{tahapan}"] = dict_pagu.get(f"{kKeg}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kSub}|{tahapan}"] = dict_pagu.get(f"{kSub}|{tahapan}", 0) + pagu

                    # --- SUMBER DANA (dictSD) ---
                    if kSub not in dict_sd: dict_sd[kSub] = {}
                    if tahapan not in dict_sd[kSub]: dict_sd[kSub][tahapan] = {}
                    dict_sd[kSub][tahapan][sd] = dict_sd[kSub][tahapan].get(sd, 0) + pagu

                # ======================================================================
                # 📝 MERAKIT BARIS REKAP (Sama persis dengan urutan cetak VBA)
                # ======================================================================
                data_rekap = []

                for kSKPD in dict_skpd:
                    # Cetak SKPD
                    row_skpd = {"Kode": kSKPD, "Uraian": dict_nama.get(kSKPD, ""), "Level": 1, "Sumber Dana (Acuan)": ""}
                    for t in list_tahapan_tahun: row_skpd[t] = dict_pagu.get(f"{kSKPD}|{t}", 0)
                    data_rekap.append(row_skpd)

                    for kUrusan in dict_urusan.get(kSKPD, {}):
                        # Cetak Urusan
                        row_urs = {"Kode": kUrusan, "Uraian": dict_nama.get(kUrusan, ""), "Level": 2, "Sumber Dana (Acuan)": ""}
                        for t in list_tahapan_tahun: row_urs[t] = dict_pagu.get(f"{kUrusan}|{t}", 0)
                        data_rekap.append(row_urs)

                        for kProg in dict_prog.get(kUrusan, {}):
                            # Cetak Program
                            row_prog = {"Kode": kProg, "Uraian": dict_nama.get(kProg, ""), "Level": 3, "Sumber Dana (Acuan)": ""}
                            for t in list_tahapan_tahun: row_prog[t] = dict_pagu.get(f"{kProg}|{t}", 0)
                            data_rekap.append(row_prog)

                            for kKeg in dict_keg.get(kProg, {}):
                                # Cetak Kegiatan
                                row_keg = {"Kode": kKeg, "Uraian": dict_nama.get(kKeg, ""), "Level": 4, "Sumber Dana (Acuan)": ""}
                                for t in list_tahapan_tahun: row_keg[t] = dict_pagu.get(f"{kKeg}|{t}", 0)
                                data_rekap.append(row_keg)

                                for kSub in dict_sub.get(kKeg, {}):
                                    # Rakit Teks Sumber Dana Sub Kegiatan
                                    str_sd = ""
                                    if kSub in dict_sd and tahapan_acuan in dict_sd[kSub]:
                                        sds = []
                                        for sd_name, sd_val in dict_sd[kSub][tahapan_acuan].items():
                                            if sd_val > 0 and sd_name:
                                                sds.append(f"{sd_name} = {sd_val:,.0f}")
                                        str_sd = " \n ".join(sds)

                                    # Cetak Sub Kegiatan
                                    row_sub = {"Kode": kSub, "Uraian": dict_nama.get(kSub, ""), "Level": 5, "Sumber Dana (Acuan)": str_sd}
                                    for t in list_tahapan_tahun: row_sub[t] = dict_pagu.get(f"{kSub}|{t}", 0)
                                    data_rekap.append(row_sub)

                # ======================================================================
                # 🖥️ FINALISASI TAMPILAN
                # ======================================================================
                df_rekap = pd.DataFrame(data_rekap)
                
                # Menghitung Selisih (Tahap Akhir - Tahap Awal)
                if len(list_tahapan_tahun) >= 2:
                    col_awal = list_tahapan_tahun[0]
                    col_akhir = list_tahapan_tahun[-1]
                    df_rekap['Selisih (Akhir - Awal)'] = df_rekap[col_akhir] - df_rekap[col_awal]
                else:
                    df_rekap['Selisih (Akhir - Awal)'] = 0

                kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)'] + list_tahapan_tahun + ['Selisih (Akhir - Awal)']
                df_web = df_rekap[kolom_final].copy()

                # Render di Web
                pesan_sukses = "Semua SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan
                st.success(f"🎉 Rekap Akurat untuk {pesan_sukses} Berhasil Dibuat!")
                st.dataframe(df_web, use_container_width=True)

                # Export Excel Berwarna
                def highlight_excel(row):
                    idx = row.name
                    lvl = df_rekap.loc[idx, 'Level']
                    if lvl == 1:   return ['background-color: #DDEBF7; font-weight: bold;'] * len(row)
                    elif lvl == 2: return ['background-color: #FFF2CC; font-weight: bold;'] * len(row)
                    elif lvl == 3: return ['background-color: #FCE4D6; font-weight: bold;'] * len(row)
                    elif lvl == 4: return ['background-color: #E2EFDA; font-weight: bold;'] * len(row)
                    return [''] * len(row) 

                kolom_angka = list_tahapan_tahun + ['Selisih (Akhir - Awal)']
                styled_excel = df_web.style.apply(highlight_excel, axis=1).format({col: "{:,.0f}" for col in kolom_angka})

                import io
                output_excel = io.BytesIO()
                styled_excel.to_excel(output_excel, index=False, engine='openpyxl')
                output_excel.seek(0)
                
                nama_file_skpd = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan.replace(" ", "_").replace("/", "_")
                
                st.download_button(
                    label="📥 Download Excel Rekap (Format Warna)",
                    data=output_excel,
                    file_name=f"Rekap_{nama_file_skpd}_{tahapan_acuan.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
