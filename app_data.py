import streamlit as st
import openpyxl
import io
import re
import time
import requests
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
from supabase import create_client, Client
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go

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
        key="menu_utama",
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
# FUNGSI-FUNGSI UTILITAS REUSABLE
# ==========================================

def terapkan_translasi_sotk(df, mapping_sotk):
    """
    Mesin Translasi SOTK: Mengganti kode_skpd lama → baru
    agar data dari 2 OPD yang berbeda nama tergabung jadi satu.
    Terinspirasi dari dictMapSKPD di VBA.
    """
    if not mapping_sotk:
        return df
    
    df = df.copy()
    df['kode_skpd'] = df['kode_skpd'].replace(mapping_sotk)
    return df


def bangun_hierarki(df_input, list_tahapan_kolom, tahap_awal, tahap_akhir, 
                     tahapan_acuan=None, df_link=None, mode='hierarki'):
    """
    Fungsi universal pembangun hierarki 5 level.
    Menggantikan duplikasi kode di Tab 1, Tab 3.
    
    Parameters:
    - df_input: DataFrame yang sudah difilter & ditranslasi SOTK
    - list_tahapan_kolom: list tahapan untuk kolom pivot
    - tahap_awal: tahapan pengurang
    - tahap_akhir: tahapan yang dikurangi
    - tahapan_acuan: untuk sumber dana (Tab 1)
    - df_link: DataFrame link DPA (Tab 3)
    - mode: 'hierarki' (Tab 1, semua tahapan) atau 'dpa' (Tab 3, hanya awal & akhir)
    
    Returns:
    - DataFrame rekap hierarki yang sudah di-sort
    """
    
    def hitung_level(df_src, list_group, level_num):
        if mode == 'dpa':
            df_filter = df_src[df_src['tahapan'].isin([tahap_awal, tahap_akhir])]
        else:
            df_filter = df_src.copy()
        grouped = df_filter.groupby(list_group + ['tahapan'])['pagu'].sum().reset_index()
        pivot = grouped.pivot_table(index=list_group, columns='tahapan', values='pagu', aggfunc='sum', fill_value=0).reset_index()
        pivot['Level'] = level_num
        return pivot

    kumpulan_level = []

    # Level 1: SKPD
    l1 = hitung_level(df_input, ['kode_skpd', 'nama_skpd'], 1)
    l1['Kode'], l1['Uraian'], l1['Sort_Key'] = l1['kode_skpd'], l1['nama_skpd'], l1['kode_skpd']
    kumpulan_level.append(l1)

    # Level 2: Urusan
    df_l2 = df_input[df_input['kode_urusan'] != ""]
    if not df_l2.empty:
        l2 = hitung_level(df_l2, ['kode_skpd', 'kode_urusan', 'nama_urusan'], 2)
        l2['Kode'], l2['Uraian'] = l2['kode_urusan'], l2['nama_urusan']
        l2['Sort_Key'] = l2['kode_skpd'] + "|" + l2['kode_urusan']
        kumpulan_level.append(l2)

    # Level 3: Program
    df_l3 = df_input[df_input['kode_program'] != ""]
    if not df_l3.empty:
        l3 = hitung_level(df_l3, ['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'], 3)
        l3['Kode'], l3['Uraian'] = l3['kode_program'], l3['nama_program']
        l3['Sort_Key'] = l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
        kumpulan_level.append(l3)

    # Level 4: Kegiatan
    df_l4 = df_input[df_input['kode_kegiatan'] != ""]
    if not df_l4.empty:
        l4 = hitung_level(df_l4, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'], 4)
        l4['Kode'], l4['Uraian'] = l4['kode_kegiatan'], l4['nama_kegiatan']
        l4['Sort_Key'] = l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
        kumpulan_level.append(l4)

    # Level 5: Sub Kegiatan
    df_l5 = df_input[df_input['kode_sub_kegiatan'] != ""]
    if not df_l5.empty:
        l5 = hitung_level(df_l5, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'], 5)
        l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
        l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']

        # Sumber Dana
        acuan_sd = tahapan_acuan if tahapan_acuan else tahap_akhir
        df_sd = df_input[df_input['tahapan'] == acuan_sd]
        sd_grouped = df_sd[df_sd['pagu'] > 0].groupby(['kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
        if not sd_grouped.empty:
            sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = Rp " + sd_grouped['pagu'].apply(lambda x: f"{int(x):,}").str.replace(',', '.') + " \n"
            sd_final = sd_grouped.groupby('kode_sub_kegiatan')['teks_sd'].apply(lambda x: ''.join(x).strip()).reset_index()
            
            if mode == 'dpa':
                sd_final.rename(columns={'teks_sd': 'Rincian Sumber Dana'}, inplace=True)
                l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')
            else:
                sd_final.rename(columns={'teks_sd': 'Sumber Dana (Acuan)'}, inplace=True)
                l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')

        # Link DPA (khusus Tab 3)
        if df_link is not None and not df_link.empty:
            l5 = pd.merge(l5, df_link, on='kode_sub_kegiatan', how='left')
            l5.rename(columns={'url': 'Link DPA'}, inplace=True)

        kumpulan_level.append(l5)

    # Gabungkan semua level
    df_rekap = pd.concat(kumpulan_level, ignore_index=True)
    
    # Pastikan semua kolom tahapan ada
    if mode == 'dpa':
        for t in [tahap_awal, tahap_akhir]:
            if t not in df_rekap.columns:
                df_rekap[t] = 0
    else:
        for t in list_tahapan_kolom:
            if t not in df_rekap.columns:
                df_rekap[t] = 0

    # Hitung selisih
    df_rekap['Selisih (Akhir - Awal)'] = df_rekap[tahap_akhir] - df_rekap[tahap_awal]

    # Pastikan kolom opsional ada
    for col_opsional in ['Sumber Dana (Acuan)', 'Rincian Sumber Dana', 'Link DPA']:
        if col_opsional in df_rekap.columns:
            df_rekap[col_opsional] = df_rekap[col_opsional].fillna("")

    # Sorting berdasarkan Sort_Key
    df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
    
    return df_rekap


# ==========================================
# 5. KONTEN BERDASARKAN MENU YANG DIPILIH
# ==========================================

# -------------------------------------------------------------------------
# --- MODUL 1: ALAT EXCEL ---
# -------------------------------------------------------------------------
if menu_pilihan == "Alat Excel":
    st.title("🛠️ Alat Excel")
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
# --- MODUL 2: IMPORT DATA SIPD & MANAJEMEN DATABASE (VERSI ULTIMATE) ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Import SIPD":
    st.title("📥 Import & Manajemen Data SIPD")
    st.write("Unggah file DPA/RKA (Excel/CSV) atau file Backup Anda ke dalam database.")

    # --- BAGIAN A: IMPORT DATA ---
    st.markdown("### ➕ Tambah Data Baru")
    with st.form("form_import"):
        st.info("💡 Tahun anggaran ditarik otomatis dari file. Anda cukup mengetik Nama Tahapan.")
        
        tahapan_input = st.text_input("🏷️ Nama Tahapan", placeholder="Ketik Tahapan... (Contoh: Pergeseran 3, Murni, dll)")
        file_upload = st.file_uploader("📂 Pilih File Excel / CSV (Termasuk file Backup)", type=["xlsx", "xls", "csv"])
        
        submit_import = st.form_submit_button("🚀 Upload & Simpan ke Database")

    if submit_import:
        if not tahapan_input:
            st.error("❌ Nama Tahapan WAJIB diisi!")
        elif file_upload is None:
            st.error("❌ File Excel/CSV belum dimasukkan!")
        else:
            with st.spinner("Membaca file dan menyinkronkan dengan database..."):
                try:
                    # 1. Baca file
                    if file_upload.name.endswith('.csv'):
                        df = pd.read_csv(file_upload)
                    else:
                        df = pd.read_excel(file_upload)
                    
                    # Bersihkan spasi di nama header agar pemetaan tidak meleset
                    df.columns = df.columns.astype(str).str.strip()

                    # 2. PEMETAAN KOLOM (Menggunakan racikan asli Anda)
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
                        "PAGU": "pagu"
                    }
                    # Lakukan rename sesuai kamus pemetaan (hanya ngefek kalau header asli Excel/SIPD)
                    df.rename(columns=pemetaan_kolom, inplace=True)
                    
                    # Pastikan semua header jadi huruf kecil (buat jaga-jaga kalau file backup)
                    df.columns = df.columns.str.lower()

                    # 3. Validasi keberadaan kolom 'tahun'
                    if 'tahun' not in df.columns:
                        st.error("❌ Gagal: Kolom 'TAHUN' tidak ditemukan di dalam file. Pastikan format file dari SIPD sudah benar.")
                    else:
                        # Jika ini file Backup, amankan bentrok ID
                        if 'id' in df.columns:
                            df = df.drop(columns=['id'])
                        if 'created_at' in df.columns:
                            df = df.drop(columns=['created_at'])
                        
                        # Tambahkan kolom tahapan dari inputan user
                        df['tahapan'] = tahapan_input
                        
                        # 4. PEMBERSIH NaN TINGKAT DEWA (Dari kode lama Anda)
                        df = df.astype(object).where(pd.notnull(df), None)
                        
                        # 5. Insert Batch ke Supabase
                        data_insert = df.to_dict(orient='records')
                        batch_size = 1000
                        for i in range(0, len(data_insert), batch_size):
                            batch = data_insert[i:i+batch_size]
                            supabase.table("rekap_sipd").insert(batch).execute()
                            
                        st.success(f"✅ LUAR BIASA! {len(df)} baris data '{tahapan_input}' berhasil mendarat dengan selamat di Database Supabase!")
                        time.sleep(1)
                        st.rerun() # Refresh agar dropdown hapus di bawah otomatis terupdate
                
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan saat memproses file: {e}")

    st.markdown("---")

    # --- BAGIAN B: ZONA MANAJEMEN DATABASE ---
    st.markdown("### ⚙️ Manajemen Database")
    with st.expander("⚠️ Buka Panel Zona Berbahaya (Backup & Hapus Data)"):
        
        # 1. FITUR BACKUP
        st.markdown("#### 1. 📥 Backup Seluruh Database")
        if st.button("📦 Buat File Backup CSV", type="primary"):
            with st.spinner("Menarik seluruh data dari server..."):
                semua_data = []
                offset = 0
                limit = 1000
                while True:
                    res = supabase.table("rekap_sipd").select("*").range(offset, offset + limit - 1).execute()
                    if not res.data: break
                    semua_data.extend(res.data)
                    if len(res.data) < limit: break
                    offset += limit
                
                if len(semua_data) > 0:
                    df_backup = pd.DataFrame(semua_data)
                    csv_data = df_backup.to_csv(index=False).encode('utf-8')
                    st.success(f"✅ Backup siap! Total: {len(df_backup)} baris data.")
                    st.download_button(label="⬇️ Download Backup.csv", data=csv_data, file_name="Backup_Database_SIPD.csv", mime="text/csv")
                else:
                    st.warning("Database masih kosong. Tidak ada yang bisa di-backup.")
        
        st.markdown("<hr style='border: 1px dashed #ccc;'>", unsafe_allow_html=True)
        
        # 2. FITUR HAPUS PARSIAL (DROPDOWN DINAMIS BERJENJANG)
        st.markdown("#### 2. 🗑️ Hapus Data Parsial (Sesuai Database)")
        
        try:
            # Tarik sampel tahun dan tahapan dari database
            semua_opsi = []
            offset = 0
            limit = 1000
            while True:
                res_opsi = supabase.table("rekap_sipd").select("tahun, tahapan").range(offset, offset + limit - 1).execute()
                if not res_opsi.data: break
                semua_opsi.extend(res_opsi.data)
                if len(res_opsi.data) < limit: break
                offset += limit
            
            if semua_opsi:
                df_opsi = pd.DataFrame(semua_opsi)
                unique_years = sorted(df_opsi['tahun'].dropna().unique().tolist())
            else:
                unique_years = []
        except Exception as e:
            unique_years = []
            df_opsi = pd.DataFrame()

        if not unique_years:
            st.info("Database masih kosong, belum ada data yang bisa dihapus.")
        else:
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                del_tahun = st.selectbox("Pilih Tahun:", unique_years, key="del_thn")
            
            with col_del2:
                # LOGIKA CERDAS: Filter Tahapan hanya untuk Tahun yang dipilih di atas!
                tahapan_tersedia = sorted(df_opsi[df_opsi['tahun'] == del_tahun]['tahapan'].dropna().unique().tolist())
                
                del_tahapan = st.selectbox(f"Pilih Tahapan di {del_tahun}:", tahapan_tersedia, key="del_thp")
            
            if del_tahapan: # Pastikan tahapan ada isinya sebelum memunculkan tombol
                if st.button(f"🗑️ Hapus Data {del_tahapan} {del_tahun}"):
                    with st.spinner("Menghapus data..."):
                        res_del = supabase.table("rekap_sipd").delete().eq("tahun", del_tahun).eq("tahapan", del_tahapan).execute()
                        st.success(f"✅ Data {del_tahapan} Tahun {del_tahun} berhasil dihapus dari database!")
                        time.sleep(1) 
                        st.rerun() 
        
        st.markdown("<hr style='border: 1px dashed #ccc;'>", unsafe_allow_html=True)
        
        # 3. FITUR KIAMAT
        st.markdown("#### 3. 🔥 Factory Reset (Kosongkan Database)")
        konfirmasi_kiamat = st.text_input("Ketik 'HAPUS TOTAL' untuk membuka kunci eksekusi:")
        
        if konfirmasi_kiamat == "HAPUS TOTAL":
            if st.button("🚨 EKSEKUSI TRUNCATE & RESET ID", type="primary"):
                with st.spinner("Menghancurkan seluruh data..."):
                    try:
                        supabase.rpc('truncate_rekap_sipd').execute()
                        st.success("💥 BAAAM! Database berhasil dikosongkan total.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal: {e}. Pastikan Fungsi RPC sudah dibuat di Supabase.")

# -------------------------------------------------------------------------
# --- MODUL 3: REKAP SIPD (VERSI FINAL - DENGAN TRANSLASI SOTK) ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Rekapitulasi SIPD")
    st.write("Analisis perbandingan postur anggaran antar tahapan & Integrasi DPA.")
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def tarik_data_database():
        semua_data = []
        offset = 0
        limit = 1000
        while True:
            res = supabase.table("rekap_sipd").select("*").order("id").range(offset, offset + limit - 1).execute()
            data_tarikan = res.data
            if not data_tarikan:
                break
            semua_data.extend(data_tarikan)
            if len(data_tarikan) < limit:
                break
            offset += limit
        return pd.DataFrame(semua_data)

    with st.spinner("⏳ Menarik seluruh data dari database..."):
        try:
            df_mentah = tarik_data_database()
        except Exception as e:
            st.error(f"❌ Gagal menarik data: {e}")
            df_mentah = pd.DataFrame() 

    if st.button("🔄 Refresh Data Database"):
        tarik_data_database.clear()
        st.rerun()

    if df_mentah.empty:
        st.info("💡 Database masih kosong. Silakan Import SIPD terlebih dahulu.")
        st.stop()
    else:
        # ==========================================
        # 1. PERSIAPAN DATA DASAR
        # ==========================================
        df = df_mentah.copy()
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        if 'tahun' in df.columns:
            df['tahun'] = df['tahun'].astype(str).str.replace('.0', '', regex=False)
        else:
            st.error("⚠️ Kolom 'tahun' tidak ditemukan!")
            st.stop()

        df = df.fillna("")

        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Filter & Parameter")

        # ==========================================
        # 2. SISTEM FILTER GLOBAL (MULTI SELECT)
        # ==========================================
        list_tahun = sorted([t for t in df['tahun'].unique() if t != ""], reverse=True)
        col_thn, col_skpd = st.columns(2)
        with col_thn:
            tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", list_tahun)
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        list_skpd = sorted([s for s in df_tahun['nama_skpd'].unique() if s != ""])
        list_skpd.insert(0, "SEMUA SKPD")
        
        with col_skpd:
            skpd_pilihan = st.multiselect("🏢 Pilih SKPD (Bisa pilih >1 untuk dimerger):", list_skpd, default=["SEMUA SKPD"])

        if "SEMUA SKPD" in skpd_pilihan:
            df_proses = df_tahun.copy()
            nama_file_export = "SEMUA_SKPD"
        else:
            df_proses = df_tahun[df_tahun['nama_skpd'].isin(skpd_pilihan)].copy()
            nama_file_export = "MERGER_" + "_".join([s.replace(" ", "")[:10] for s in skpd_pilihan])

        if df_proses.empty:
            st.warning(f"⚠️ Tidak ada data untuk pilihan SKPD tersebut di tahun {tahun_pilihan}.")
            st.stop()

        tahapan_tersedia = [t for t in df_proses['tahapan'].unique() if t != ""]
        
        st.markdown("#### 📋 Urutan Tahapan & Acuan Selisih")
        list_tahapan = st.multiselect("Susun urutan tahapan (Kiri ke Kanan):", options=tahapan_tersedia, default=tahapan_tersedia)
        
        if not list_tahapan:
            st.error("⚠️ Pilih minimal 1 tahapan.")
            st.stop()
            
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            tahapan_acuan = st.selectbox("🎯 Acuan Sumber Dana (Khusus Tab 1):", list_tahapan, index=len(list_tahapan)-1)
        with col_t2:
            tahap_awal = st.selectbox("📉 Tahapan Awal (Pengurang):", list_tahapan, index=0)
        with col_t3:
            tahap_akhir = st.selectbox("📈 Tahapan Akhir (Dikurangi):", list_tahapan, index=len(list_tahapan)-1)

        # ==========================================
        # 2.5 MAPPING PERUBAHAN SOTK (FITUR BARU!)
        # ==========================================
        
        # Inisialisasi session state untuk mapping
        if 'mapping_sotk' not in st.session_state:
            st.session_state.mapping_sotk = {}  # {kode_lama: kode_baru}
        
        with st.expander("🔄 Mapping Perubahan SOTK / Perubahan Nama OPD (Opsional)", expanded=False):
            st.caption(
                "Jika ada OPD yang berubah nama/kode antar tahapan (contoh: Dinas Pendidikan dan Kebudayaan → Dinas Pendidikan), "
                "tambahkan mapping di sini agar data dari kedua OPD digabung menjadi satu dalam rekap hierarki."
            )
            
            # Ambil daftar unik SKPD dari data (kode + nama)
            df_skpd_unik = df_proses[['kode_skpd', 'nama_skpd']].drop_duplicates().sort_values('kode_skpd')
            daftar_opsi_skpd = [f"{row['kode_skpd']}  |  {row['nama_skpd']}" for _, row in df_skpd_unik.iterrows()]
            
            if len(daftar_opsi_skpd) < 2:
                st.info("Hanya ada 1 SKPD dalam data. Mapping SOTK tidak diperlukan.")
            else:
                st.markdown("##### ➕ Tambah Mapping Baru")
                col_lama, col_baru, col_btn = st.columns([4, 4, 2])
                with col_lama:
                    opd_lama_pilihan = st.selectbox("OPD LAMA (akan diganti):", daftar_opsi_skpd, key="opd_lama_sel")
                with col_baru:
                    opd_baru_pilihan = st.selectbox("OPD BARU (pengganti):", daftar_opsi_skpd, key="opd_baru_sel")
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("➕ Tambah", type="primary", key="btn_tambah_sotk", use_container_width=True):
                        kode_lama = opd_lama_pilihan.split("  |  ")[0].strip()
                        kode_baru = opd_baru_pilihan.split("  |  ")[0].strip()
                        if kode_lama == kode_baru:
                            st.error("❌ OPD Lama dan Baru tidak boleh sama!")
                        else:
                            st.session_state.mapping_sotk[kode_lama] = kode_baru
                            st.success(f"✅ Mapping ditambahkan: {opd_lama_pilihan} → {opd_baru_pilihan}")
                            time.sleep(0.5)
                            st.rerun()
                
                # Tampilkan mapping aktif
                if st.session_state.mapping_sotk:
                    st.markdown("##### 📋 Mapping SOTK Aktif:")
                    
                    # Buat dictionary nama untuk display
                    dict_nama_skpd = dict(zip(df_skpd_unik['kode_skpd'], df_skpd_unik['nama_skpd']))
                    
                    for idx, (k_lama, k_baru) in enumerate(st.session_state.mapping_sotk.items()):
                        nama_lama = dict_nama_skpd.get(k_lama, "???")
                        nama_baru = dict_nama_skpd.get(k_baru, "???")
                        
                        col_info, col_hapus = st.columns([8, 2])
                        with col_info:
                            st.markdown(f"🔸 `{k_lama}` ({nama_lama}) **→** `{k_baru}` ({nama_baru})")
                        with col_hapus:
                            if st.button("🗑️ Hapus", key=f"hapus_sotk_{idx}"):
                                del st.session_state.mapping_sotk[k_lama]
                                st.rerun()
                    
                    if st.button("🧹 Hapus Semua Mapping", key="hapus_semua_sotk"):
                        st.session_state.mapping_sotk = {}
                        st.rerun()
                else:
                    st.info("Belum ada mapping. Sistem akan bekerja seperti biasa (tanpa penggabungan OPD).")

        # ==========================================
        # 2.6 TERAPKAN TRANSLASI SOTK & JANGKAR NOMENKLATUR
        # ==========================================
        
        # Terapkan mapping SOTK ke df_proses
        df_proses = terapkan_translasi_sotk(df_proses, st.session_state.mapping_sotk)
        
        # Jangkar nomenklatur dari tahap akhir (diperkuat setelah translasi)
        df_akhir = df_proses[df_proses['tahapan'] == tahap_akhir]
        
        if not df_akhir.empty:
            kolom_hierarki = [
                'kode_skpd', 'nama_skpd', 
                'kode_urusan', 'nama_urusan', 
                'kode_program', 'nama_program', 
                'kode_kegiatan', 'nama_kegiatan', 
                'nama_sub_kegiatan'
            ]
            
            df_ref = df_akhir[['kode_sub_kegiatan'] + kolom_hierarki].drop_duplicates('kode_sub_kegiatan').set_index('kode_sub_kegiatan')
            
            for col in kolom_hierarki:
                dict_map = df_ref[col].to_dict()
                df_proses[col] = df_proses['kode_sub_kegiatan'].map(dict_map).fillna(df_proses[col])
            
            # TAMBAHAN: Jangkar nama_skpd berdasarkan kode_skpd dari tahap akhir
            # Ini memastikan setelah translasi SOTK, nama SKPD selalu pakai nama terbaru
            df_ref_skpd = df_akhir[['kode_skpd', 'nama_skpd']].drop_duplicates('kode_skpd').set_index('kode_skpd')
            dict_nama_skpd_akhir = df_ref_skpd['nama_skpd'].to_dict()
            df_proses['nama_skpd'] = df_proses['kode_skpd'].map(dict_nama_skpd_akhir).fillna(df_proses['nama_skpd'])

        # ==========================================
        # 3. PEMBUATAN TAB MENU
        # ==========================================
        tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📑 Rekap Hierarki", "💰 Rekap Sumber Dana", "🔗 Integrasi Link DPA", "📈 Evaluasi Realisasi", "🏢 Rekap Per Bidang"])

        # -------------------------------------------------------------------
        # TAB 1: REKAP HIERARKI TAHAPAN (MENGGUNAKAN FUNGSI REUSABLE)
        # -------------------------------------------------------------------
        with tab1:
            if st.button(f"🚀 PROSES LAPORAN HIERARKI", type="primary", use_container_width=True, key="btn_tab1"):
                with st.spinner("Memproses Laporan Hierarki..."):
                    
                    df_rekap = bangun_hierarki(
                        df_input=df_proses, 
                        list_tahapan_kolom=list_tahapan,
                        tahap_awal=tahap_awal,
                        tahap_akhir=tahap_akhir,
                        tahapan_acuan=tahapan_acuan,
                        mode='hierarki'
                    )

                    if 'Sumber Dana (Acuan)' not in df_rekap.columns:
                        df_rekap['Sumber Dana (Acuan)'] = ""

                    kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)', 'Level'] + list_tahapan + ['Selisih (Akhir - Awal)']
                    df_hasil = df_rekap[[c for c in kolom_final if c in df_rekap.columns]]

                    df_tampil = df_hasil.drop(columns=['Level'])
                    kolom_angka = list_tahapan + ['Selisih (Akhir - Awal)']
                    format_dict = {col: "{:,.0f}" for col in kolom_angka if col in df_tampil.columns}
                    styled_df_web = df_tampil.style.format(format_dict).set_properties(subset=['Sumber Dana (Acuan)'], **{'white-space': 'pre-wrap'})
                    
                    st.success(f"✅ Laporan Hierarki Berhasil Dibuat!")
                    st.dataframe(styled_df_web, use_container_width=True, height=500)

                    def warna_baris_excel(row):
                        lvl = df_hasil.loc[row.name, 'Level']
                        if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                        if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                        if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                        if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                        return [''] * len(row)

                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        df_tampil.style.apply(warna_baris_excel, axis=1).format(format_dict).to_excel(writer, index=False, sheet_name=f'Hierarki')
                    output_excel.seek(0)
                    
                    st.download_button("📥 Download Excel (Hierarki)", output_excel, f"Hierarki_{nama_file_export}_{tahun_pilihan}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_t1")

        # -------------------------------------------------------------------
        # TAB 2: REKAP SUMBER DANA + TOTAL KESELURUHAN
        # -------------------------------------------------------------------
        with tab2:
            if st.button(f"🚀 PROSES REKAP SUMBER DANA", type="primary", use_container_width=True, key="btn_tab2"):
                with st.spinner("Menghitung Pagu per Sumber Dana..."):
                    df_sd = df_proses.copy()
                    df_sd['nama_sumber_dana'] = df_sd['nama_sumber_dana'].replace("", "TIDAK DIKETAHUI / KOSONG")
                    rekap_sd = df_sd.groupby(['nama_sumber_dana', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                    for t in list_tahapan:
                        if t not in rekap_sd.columns:
                            rekap_sd[t] = 0
                    rekap_sd['Selisih (Akhir - Awal)'] = rekap_sd[tahap_akhir] - rekap_sd[tahap_awal]
                    rekap_sd = rekap_sd.sort_values(by=tahap_akhir, ascending=False).reset_index(drop=True)

                    kolom_angka_sd = list_tahapan + ['Selisih (Akhir - Awal)']
                    kolom_final_sd = ['nama_sumber_dana'] + kolom_angka_sd
                    df_hasil_sd = rekap_sd[kolom_final_sd].copy()

                    baris_total = pd.DataFrame([df_hasil_sd[kolom_angka_sd].sum()])
                    baris_total['nama_sumber_dana'] = "=== TOTAL KESELURUHAN ==="
                    df_hasil_sd = pd.concat([df_hasil_sd, baris_total], ignore_index=True)

                    format_dict_sd = {col: "{:,.0f}" for col in kolom_angka_sd}
                    st.success(f"✅ Rekap Sumber Dana Berhasil Dibuat!")
                    st.dataframe(df_hasil_sd.style.format(format_dict_sd), use_container_width=True, height=500)

                    def highlight_total_excel(row):
                        if row['nama_sumber_dana'] == "=== TOTAL KESELURUHAN ===":
                            return ['background-color: #ffe699; font-weight: bold'] * len(row)
                        return [''] * len(row)

                    output_excel_sd = io.BytesIO()
                    with pd.ExcelWriter(output_excel_sd, engine='openpyxl') as writer:
                        df_hasil_sd.style.apply(highlight_total_excel, axis=1).format(format_dict_sd).to_excel(writer, index=False, sheet_name=f'SumberDana')
                    output_excel_sd.seek(0)
                    
                    st.download_button("📥 Download Excel (Sumber Dana)", output_excel_sd, f"SumberDana_{nama_file_export}_{tahun_pilihan}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_t2")

        # -------------------------------------------------------------------
        # TAB 3: INTEGRASI LINK DPA (MENGGUNAKAN FUNGSI REUSABLE)
        # -------------------------------------------------------------------
        with tab3:
            st.info(f"💡 Menampilkan perbandingan: **{tahap_awal}** vs **{tahap_akhir}**")
            
            sumber_data_dpa = st.radio("Pilih Mode Input Link DPA:", ["📂 Upload File Lokal (Excel/CSV)", "🌐 Link Google Sheet (Otomatis Baca Sheet)"], horizontal=True, key="radio_dpa")
            
            file_link = None
            link_dpa_input = ""
            df_link_gsheet = pd.DataFrame()
            
            if sumber_data_dpa == "📂 Upload File Lokal (Excel/CSV)":
                file_link = st.file_uploader("📂 Upload File Excel Link DPA (Pastikan ada kolom 'kode sub' dan 'url')", type=["xlsx", "xls", "csv"], key="up_link")
            else:
                link_dpa_input = st.text_input("🔗 Paste Link Google Sheet DPA:", placeholder="https://docs.google.com/spreadsheets/d/...")
                st.caption("Gunakan link Share biasa dari HP atau PC. Pastikan akses diatur ke: *Anyone with the link*")
                
                # --- LOGIKA AJAIB PENDETEKSI SHEET ---
                if link_dpa_input:
                    match = re.search(r'/d/([a-zA-Z0-9-_]+)', link_dpa_input)
                    if match:
                        doc_id = match.group(1)
                        url_xlsx = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                        
                        try:
                            @st.cache_data(show_spinner=False, ttl=600)
                            def tarik_excel_google(url):
                                resp = requests.get(url)
                                resp.raise_for_status()
                                return resp.content
                            
                            with st.spinner("🔍 Sedang membongkar Google Sheet untuk mencari daftar Tahapan..."):
                                excel_bytes = tarik_excel_google(url_xlsx)
                                xls = pd.ExcelFile(io.BytesIO(excel_bytes))
                                daftar_sheet = xls.sheet_names
                                
                            if daftar_sheet:
                                sheet_pilihan = st.selectbox("📑 Pilih Tahapan (Sheet) yang ingin ditarik:", daftar_sheet)
                                
                                if sheet_pilihan:
                                    df_link_gsheet = pd.read_excel(xls, sheet_name=sheet_pilihan)
                            else:
                                st.error("❌ Tidak ada sheet yang ditemukan di dalam file tersebut.")
                                
                        except Exception as e:
                            st.error(f"❌ Gagal membaca Google Sheet. Pastikan link tidak dikunci. Error: {e}")
                    else:
                        st.warning("⚠️ Link tidak valid. Coba paste ulang link Google Sheet yang benar.")

            # --- TOMBOL EKSEKUSI ---
            if st.button(f"🚀 PROSES & GABUNGKAN LINK DPA", type="primary", use_container_width=True, key="btn_tab3"):
                
                if sumber_data_dpa == "📂 Upload File Lokal (Excel/CSV)" and file_link is None:
                    st.error("⚠️ Mohon upload file Excel/CSV Link DPA terlebih dahulu!")
                elif sumber_data_dpa == "🌐 Link Google Sheet (Otomatis Baca Sheet)" and link_dpa_input == "":
                    st.error("⚠️ Mohon paste Link Google Sheet terlebih dahulu!")
                elif sumber_data_dpa == "🌐 Link Google Sheet (Otomatis Baca Sheet)" and df_link_gsheet.empty:
                    st.error("⚠️ Menunggu data dari Google Sheet. Silakan pilih Tahapan (Sheet) yang benar.")
                else:
                    with st.spinner("Menjahit Link DPA dengan Data Anggaran..."):
                        
                        try:
                            if sumber_data_dpa == "📂 Upload File Lokal (Excel/CSV)":
                                if file_link.name.endswith('.csv'):
                                    df_link = pd.read_csv(file_link)
                                else:
                                    df_link = pd.read_excel(file_link)
                            else:
                                df_link = df_link_gsheet.copy()

                            df_link.columns = df_link.columns.astype(str).str.lower().str.strip()
                            
                            if 'kode sub' not in df_link.columns or 'url' not in df_link.columns:
                                st.error(f"❌ Gagal! File/Sheet upload tidak memiliki kolom bernama 'kode sub' atau 'url'. Kolom yang terdeteksi: {list(df_link.columns)}")
                            else:
                                df_link = df_link[['kode sub', 'url']].rename(columns={'kode sub': 'kode_sub_kegiatan'})
                                df_link['kode_sub_kegiatan'] = df_link['kode_sub_kegiatan'].astype(str).str.strip()
                                df_link['url'] = df_link['url'].fillna("")

                                # Gunakan fungsi reusable!
                                df_rekap_dpa = bangun_hierarki(
                                    df_input=df_proses,
                                    list_tahapan_kolom=[tahap_awal, tahap_akhir],
                                    tahap_awal=tahap_awal,
                                    tahap_akhir=tahap_akhir,
                                    tahapan_acuan=tahap_akhir,
                                    df_link=df_link,
                                    mode='dpa'
                                )
                                
                                df_rekap_dpa['Anggaran Sebelum'] = df_rekap_dpa[tahap_awal] if tahap_awal in df_rekap_dpa.columns else 0
                                df_rekap_dpa['Anggaran Sesudah'] = df_rekap_dpa[tahap_akhir] if tahap_akhir in df_rekap_dpa.columns else 0
                                df_rekap_dpa['Selisih'] = df_rekap_dpa['Anggaran Sesudah'] - df_rekap_dpa['Anggaran Sebelum']
                                
                                for col_opt in ['Rincian Sumber Dana', 'Link DPA']:
                                    if col_opt not in df_rekap_dpa.columns:
                                        df_rekap_dpa[col_opt] = ""
                                    df_rekap_dpa[col_opt] = df_rekap_dpa[col_opt].fillna("")

                                kolom_final_dpa = ['Link DPA', 'Kode', 'Uraian', 'Rincian Sumber Dana', 'Anggaran Sebelum', 'Anggaran Sesudah', 'Selisih', 'Level']
                                df_hasil_dpa = df_rekap_dpa[[c for c in kolom_final_dpa if c in df_rekap_dpa.columns]].copy()

                                df_tampil_dpa = df_hasil_dpa.drop(columns=['Level'])
                                
                                st.success(f"✅ Integrasi Link DPA Berhasil!")
                                st.dataframe(
                                    df_tampil_dpa, 
                                    use_container_width=True, 
                                    height=500,
                                    column_config={
                                        "Link DPA": st.column_config.LinkColumn("Link DPA", display_text="🔗 Buka DPA"),
                                        "Anggaran Sebelum": st.column_config.NumberColumn(format="%.0f"),
                                        "Anggaran Sesudah": st.column_config.NumberColumn(format="%.0f"),
                                        "Selisih": st.column_config.NumberColumn(format="%.0f")
                                    }
                                )

                                def format_excel_dpa(row):
                                    if pd.notna(row['Link DPA']) and str(row['Link DPA']).startswith("http"):
                                        row['Link DPA'] = f'=HYPERLINK("{row["Link DPA"]}", "🔗 Buka DPA")'
                                    else:
                                        row['Link DPA'] = ""
                                    return row

                                df_excel_dpa = df_hasil_dpa.apply(format_excel_dpa, axis=1)

                                def warna_baris_dpa(row):
                                    lvl = df_excel_dpa.loc[row.name, 'Level']
                                    if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                                    if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                                    if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                                    if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                                    return [''] * len(row)

                                output_dpa = io.BytesIO()
                                with pd.ExcelWriter(output_dpa, engine='openpyxl') as writer:
                                    df_excel_dpa.drop(columns=['Level']).style.apply(warna_baris_dpa, axis=1).to_excel(writer, index=False, sheet_name=f'Integrasi_DPA')
                                output_dpa.seek(0)
                                
                                st.download_button(
                                    label="📥 Download Excel (Link DPA)", 
                                    data=output_dpa, 
                                    file_name=f"Integrasi_DPA_{nama_file_export}_{tahun_pilihan}.xlsx", 
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                    type="primary",
                                    key="dl_t3"
                                )
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat memproses data: {e}")
                            
        # -------------------------------------------------------------------
        # TAB 4: EVALUASI KINERJA & REALISASI (HYBRID DENGAN PEMBERSIH ANGKA)
        # -------------------------------------------------------------------
        with tab4:
            st.info(f"💡 Patokan Pagu Anggaran menggunakan Tahapan: **{tahap_akhir}**. Anda bisa mengosongkan salah satu input jika tidak tersedia.")
            
            sumber_data = st.radio("Pilih Mode Input Data:", ["📂 Upload File Lokal (Excel/CSV)", "🌐 Link Google Sheet (Public)"], horizontal=True)
            
            file_realisasi = None
            file_pptk = None
            link_realisasi = ""
            link_pptk = ""
            
            col_up1, col_up2 = st.columns(2)
            
            if sumber_data == "📂 Upload File Lokal (Excel/CSV)":
                with col_up1:
                    st.markdown("**1️⃣ Data Realisasi Keuangan**")
                    file_realisasi = st.file_uploader("Upload Excel (Kolom wajib: 'kode sub', 'realisasi')", type=["xlsx", "xls", "csv"], key="up_realisasi")
                with col_up2:
                    st.markdown("**2️⃣ Master Bidang / PPTK**")
                    file_pptk = st.file_uploader("Upload Excel (Kolom wajib: 'kode sub', 'penanggung jawab')", type=["xlsx", "xls", "csv"], key="up_pptk")
            else:
                with col_up1:
                    st.markdown("**1️⃣ Data Realisasi Keuangan**")
                    link_realisasi = st.text_input("🔗 Paste Link Google Sheet Realisasi:", placeholder="https://docs.google.com/spreadsheets/d/...")
                    st.caption("Pastikan akses link diatur ke: *Anyone with the link / Siapa saja yang memiliki link*")
                with col_up2:
                    st.markdown("**2️⃣ Master Bidang / PPTK**")
                    link_pptk = st.text_input("🔗 Paste Link Google Sheet Master Bidang:", placeholder="https://docs.google.com/spreadsheets/d/...")
                    st.caption("Pastikan akses link diatur ke: *Anyone with the link / Siapa saja yang memiliki link*")

            def konversi_link_gsheet(url):
                if pd.isna(url) or str(url).strip() == "": return None
                url = str(url).strip()
                if "docs.google.com/spreadsheets" in url:
                    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
                    if match:
                        return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"
                return None

            if st.button("🚀 PROSES EVALUASI REALISASI", type="primary", use_container_width=True, key="btn_tab4"):
                with st.spinner("Menyedot data dan menjahit dengan pembersih karakter..."):
                    
                    df_eval = df_proses[df_proses['tahapan'] == tahap_akhir].copy()
                    
                    if df_eval.empty:
                        st.error(f"⚠�� Tidak ada data anggaran untuk tahapan {tahap_akhir}.")
                    else:
                        df_base = df_eval.groupby(['kode_sub_kegiatan', 'nama_sub_kegiatan'])['pagu'].sum().reset_index()
                        df_base.rename(columns={'kode_sub_kegiatan': 'Kode Sub', 'nama_sub_kegiatan': 'Uraian Sub Kegiatan', 'pagu': 'Pagu Anggaran'}, inplace=True)
                        
                        df_base['key_merge'] = df_base['Kode Sub'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                        
                        # Proses File/Link Realisasi
                        df_real = pd.DataFrame()
                        try:
                            if sumber_data == "📂 Upload File Lokal (Excel/CSV)" and file_realisasi is not None:
                                df_real = pd.read_csv(file_realisasi) if file_realisasi.name.endswith('.csv') else pd.read_excel(file_realisasi)
                            elif sumber_data == "🌐 Link Google Sheet (Public)" and link_realisasi != "":
                                url_csv = konversi_link_gsheet(link_realisasi)
                                if url_csv: df_real = pd.read_csv(url_csv)
                        except Exception as e:
                            st.error(f"❌ Gagal menarik data Realisasi: {e}")

                        if not df_real.empty:
                            df_real.columns = df_real.columns.astype(str).str.lower().str.strip()
                            if 'kode sub' in df_real.columns and 'realisasi' in df_real.columns:
                                df_real['key_merge'] = df_real['kode sub'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                                
                                angka_bersih = df_real['realisasi'].astype(str).str.replace(r'[Rp\s\.]', '', regex=True).str.replace(',', '.')
                                df_real['Realisasi'] = pd.to_numeric(angka_bersih, errors='coerce').fillna(0)

                                df_real = df_real.groupby('key_merge')['Realisasi'].sum().reset_index()
                                df_base = pd.merge(df_base, df_real, on='key_merge', how='left')
                                df_base['Realisasi'] = df_base['Realisasi'].fillna(0)
                            else:
                                st.warning("⚠️ Kolom 'kode sub' atau 'realisasi' tidak ditemukan di data Realisasi.")
                                df_base['Realisasi'] = 0
                        else:
                            df_base['Realisasi'] = 0

                        # Proses File/Link Master Bidang / PPTK
                        df_pj = pd.DataFrame()
                        try:
                            if sumber_data == "📂 Upload File Lokal (Excel/CSV)" and file_pptk is not None:
                                df_pj = pd.read_csv(file_pptk) if file_pptk.name.endswith('.csv') else pd.read_excel(file_pptk)
                            elif sumber_data == "🌐 Link Google Sheet (Public)" and link_pptk != "":
                                url_csv = konversi_link_gsheet(link_pptk)
                                if url_csv: df_pj = pd.read_csv(url_csv)
                        except Exception as e:
                            st.error(f"❌ Gagal menarik data Master Bidang: {e}")

                        if not df_pj.empty:
                            df_pj.columns = df_pj.columns.astype(str).str.lower().str.strip()
                            if 'kode sub' in df_pj.columns and 'penanggung jawab' in df_pj.columns:
                                df_pj['key_merge'] = df_pj['kode sub'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                                df_pj['Penanggung Jawab'] = df_pj['penanggung jawab'].astype(str).replace(['nan', 'NaN', 'None', ''], 'BELUM DIPETAKAN')
                                df_pj = df_pj.drop_duplicates(subset=['key_merge'])
                                df_pj = df_pj[['key_merge', 'Penanggung Jawab']]
                                df_base = pd.merge(df_base, df_pj, on='key_merge', how='left')
                                df_base['Penanggung Jawab'] = df_base['Penanggung Jawab'].fillna("BELUM DIPETAKAN")
                            else:
                                st.warning("⚠️ Kolom 'kode sub' atau 'penanggung jawab' tidak ditemukan di Master Bidang.")
                                df_base['Penanggung Jawab'] = "BELUM DIPETAKAN"
                        else:
                            df_base['Penanggung Jawab'] = "BELUM DIPETAKAN"

                        df_base['Sisa Anggaran'] = df_base['Pagu Anggaran'] - df_base['Realisasi']
                        df_base['% Capaian'] = (df_base['Realisasi'] / df_base['Pagu Anggaran'].replace(0, pd.NA)).fillna(0) * 100

                        df_base = df_base.sort_values(by=['Penanggung Jawab', 'Kode Sub']).reset_index(drop=True)
                        kolom_urut = ['Kode Sub', 'Uraian Sub Kegiatan', 'Pagu Anggaran', 'Realisasi', 'Sisa Anggaran', '% Capaian', 'Penanggung Jawab']
                        df_final_eval = df_base[kolom_urut]

                        st.success("✅ Evaluasi Realisasi Berhasil Ditarik dan Dibuat!")
                        st.dataframe(
                            df_final_eval,
                            use_container_width=True,
                            height=500,
                            column_config={
                                "Pagu Anggaran": st.column_config.NumberColumn(format="%.0f"),
                                "Realisasi": st.column_config.NumberColumn(format="%.0f"),
                                "Sisa Anggaran": st.column_config.NumberColumn(format="%.0f"),
                                "% Capaian": st.column_config.NumberColumn(format="%.2f %%"),
                            }
                        )

                        output_eval = io.BytesIO()
                        with pd.ExcelWriter(output_eval, engine='openpyxl') as writer:
                            format_eval = {
                                'Pagu Anggaran': '{:,.0f}',
                                'Realisasi': '{:,.0f}',
                                'Sisa Anggaran': '{:,.0f}',
                                '% Capaian': '{:.2f}'
                            }
                            df_final_eval.style.format(format_eval).to_excel(writer, index=False, sheet_name=f'Evaluasi_Realisasi')
                        output_eval.seek(0)
                        
                        st.download_button(
                            label="📥 Download Excel (Evaluasi Realisasi)", 
                            data=output_eval, 
                            file_name=f"Evaluasi_Realisasi_{nama_file_export}_{tahun_pilihan}.xlsx", 
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                            type="primary",
                            key="dl_t4"
                        )


        # -------------------------------------------------------------------
        # TAB 5: REKAPITULASI PER BIDANG/PPTK (HYBRID - LOKAL & GOOGLE SHEET)
        # -------------------------------------------------------------------
        with tab5:
            st.info(f"💡 Menampilkan total pagu per Bidang/PPTK (berdasarkan file pemetaan): **{tahap_awal}** vs **{tahap_akhir}**")
            
            sumber_data_bidang = st.radio("Pilih Mode Input File Pemetaan PPTK/Bidang:", ["📂 Upload File Lokal (Excel/CSV)", "🌐 Link Google Sheet (Otomatis Baca Sheet)"], horizontal=True, key="radio_bidang_t5")
            
            file_mapping_bidang = None
            link_bidang_input = ""
            df_map_gsheet = pd.DataFrame()
            
            if sumber_data_bidang == "📂 Upload File Lokal (Excel/CSV)":
                file_mapping_bidang = st.file_uploader("📂 Upload File Excel Pemetaan (Pastikan ada kolom 'kode sub' dan 'penanggung jawab')", type=["xlsx", "xls", "csv"], key="up_bidang_t5")
            else:
                link_bidang_input = st.text_input("🔗 Paste Link Google Sheet Pemetaan:", placeholder="https://docs.google.com/spreadsheets/d/...", key="link_bidang_t5")
                st.caption("Gunakan link Share biasa. Pastikan akses diatur ke: *Anyone with the link*")
                
                if link_bidang_input:
                    match = re.search(r'/d/([a-zA-Z0-9-_]+)', link_bidang_input)
                    if match:
                        doc_id = match.group(1)
                        url_xlsx = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx"
                        
                        try:
                            @st.cache_data(show_spinner=False, ttl=600)
                            def tarik_excel_bidang(url):
                                resp = requests.get(url)
                                resp.raise_for_status()
                                return resp.content
                            
                            with st.spinner("🔍 Sedang membongkar Google Sheet untuk mencari daftar Sheet..."):
                                excel_bytes = tarik_excel_bidang(url_xlsx)
                                xls = pd.ExcelFile(io.BytesIO(excel_bytes))
                                daftar_sheet = xls.sheet_names
                                
                            if daftar_sheet:
                                sheet_pilihan = st.selectbox("📑 Pilih Tab (Sheet) yang berisi data PPTK/Bidang:", daftar_sheet, key="sheet_bidang_t5")
                                if sheet_pilihan:
                                    df_map_gsheet = pd.read_excel(xls, sheet_name=sheet_pilihan)
                            else:
                                st.error("❌ Tidak ada sheet yang ditemukan di dalam file tersebut.")
                        except Exception as e:
                            st.error(f"❌ Gagal membaca Google Sheet. Pastikan link tidak dikunci. Error: {e}")
                    else:
                        st.warning("⚠️ Link tidak valid. Coba paste ulang link Google Sheet yang benar.")

            if st.button("📊 PROSES REKAP BIDANG", type="primary", use_container_width=True, key="btn_tab5"):
                
                if sumber_data_bidang == "📂 Upload File Lokal (Excel/CSV)" and file_mapping_bidang is None:
                    st.error("⚠️ Mohon upload file Excel/CSV terlebih dahulu!")
                elif sumber_data_bidang == "🌐 Link Google Sheet (Otomatis Baca Sheet)" and link_bidang_input == "":
                    st.error("⚠️ Mohon paste Link Google Sheet terlebih dahulu!")
                elif sumber_data_bidang == "🌐 Link Google Sheet (Otomatis Baca Sheet)" and df_map_gsheet.empty:
                    st.error("⚠️ Menunggu data dari Google Sheet. Silakan pilih Tahapan (Sheet) yang benar.")
                else:
                    with st.spinner("Menyatukan data SIPD dengan pemetaan PPTK/Bidang..."):
                        try:
                            if sumber_data_bidang == "📂 Upload File Lokal (Excel/CSV)":
                                if file_mapping_bidang.name.endswith('.csv'):
                                    df_map = pd.read_csv(file_mapping_bidang)
                                else:
                                    df_map = pd.read_excel(file_mapping_bidang)
                            else:
                                df_map = df_map_gsheet.copy()

                            df_map.columns = df_map.columns.astype(str).str.lower().str.strip()
                            
                            if 'code' in df_map.columns:
                                df_map.rename(columns={'code': 'kode sub'}, inplace=True)
                            if 'bidang' in df_map.columns:
                                df_map.rename(columns={'bidang': 'penanggung jawab'}, inplace=True)
                            
                            if 'kode sub' not in df_map.columns or 'penanggung jawab' not in df_map.columns:
                                st.error(f"❌ Ralat! File pemetaan harus memiliki kolom 'kode sub' dan 'penanggung jawab'. Kolom yang terdeteksi: {list(df_map.columns)}")
                            else:
                                df_map = df_map[['kode sub', 'penanggung jawab']].rename(columns={'kode sub': 'kode_sub_kegiatan'})
                                df_map['kode_sub_kegiatan'] = df_map['kode_sub_kegiatan'].astype(str).str.strip()
                                df_map['penanggung jawab'] = df_map['penanggung jawab'].fillna("TIDAK ADA DATA")
                                
                                df_map = df_map.drop_duplicates(subset=['kode_sub_kegiatan'])
                                
                                df_sipd_filter = df_proses[df_proses['tahapan'].isin([tahap_awal, tahap_akhir])].copy()
                                
                                df_gabung = pd.merge(df_sipd_filter, df_map, on='kode_sub_kegiatan', how='left')
                                
                                df_gabung['penanggung jawab'] = df_gabung['penanggung jawab'].fillna("TIDAK DIPETAKAN")
                                
                                rekap_bidang = df_gabung.groupby(['penanggung jawab', 'tahapan'])['pagu'].sum().reset_index()
                                
                                pivot_bidang = rekap_bidang.pivot_table(
                                    index='penanggung jawab', 
                                    columns='tahapan', 
                                    values='pagu', 
                                    aggfunc='sum', 
                                    fill_value=0
                                ).reset_index()
                                
                                for t in [tahap_awal, tahap_akhir]:
                                    if t not in pivot_bidang.columns:
                                        pivot_bidang[t] = 0
                                        
                                pivot_bidang['Selisih'] = pivot_bidang[tahap_akhir] - pivot_bidang[tahap_awal]
                                
                                pivot_bidang.rename(columns={
                                    'penanggung jawab': 'Penanggung Jawab / Bidang',
                                    tahap_awal: f'Pagu {tahap_awal}',
                                    tahap_akhir: f'Pagu {tahap_akhir}'
                                }, inplace=True)
                                
                                baris_total = pd.DataFrame([{
                                    'Penanggung Jawab / Bidang': 'TOTAL KESELURUHAN',
                                    f'Pagu {tahap_awal}': pivot_bidang[f'Pagu {tahap_awal}'].sum(),
                                    f'Pagu {tahap_akhir}': pivot_bidang[f'Pagu {tahap_akhir}'].sum(),
                                    'Selisih': pivot_bidang['Selisih'].sum()
                                }])
                                pivot_bidang = pd.concat([pivot_bidang, baris_total], ignore_index=True)
                                
                                st.success("✅ Rekapitulasi Per Bidang Selesai!")
                                st.dataframe(
                                    pivot_bidang, 
                                    use_container_width=True,
                                    column_config={
                                        f'Pagu {tahap_awal}': st.column_config.NumberColumn(format="Rp %.0f"),
                                        f'Pagu {tahap_akhir}': st.column_config.NumberColumn(format="Rp %.0f"),
                                        "Selisih": st.column_config.NumberColumn(format="Rp %.0f")
                                    }
                                )
                                
                                output_bidang = io.BytesIO()
                                with pd.ExcelWriter(output_bidang, engine='openpyxl') as writer:
                                    pivot_bidang.to_excel(writer, index=False, sheet_name='Rekap_Bidang_Internal')
                                output_bidang.seek(0)
                                
                                st.download_button(
                                    label="📥 Download Excel (Rekap Bidang)", 
                                    data=output_bidang, 
                                    file_name=f"Rekap_Bidang_Internal_{nama_file_export}_{tahun_pilihan}.xlsx", 
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                    type="primary",
                                    key="dl_tab5_excel"
                                )
                                
                        except Exception as e:
                            st.error(f"❌ Terjadi kesalahan saat memproses data: {e}")

