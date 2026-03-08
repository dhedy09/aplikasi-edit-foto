import streamlit as st
import openpyxl
import io
import re
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
from supabase import create_client, Client # <--- Library Supabase
from collections import defaultdict

# 1. Judul Halaman
st.set_page_config(page_title="Olah Data & SIPD", layout="wide", page_icon="📊")

# ==========================================
# KONEKSI KE DATABASE SUPABASE
# ==========================================
# Mengambil kunci dari brankas Rahasia Streamlit
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("⚠️ Gagal terhubung ke Database. Pastikan SUPABASE_URL dan SUPABASE_KEY sudah ada di Streamlit Secrets!")
    st.stop()

# 2. Sistem Login
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
# 3. MENU NAVIGASI MODERN (SIDEBAR)
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
# KONTEN BERDASARKAN MENU YANG DIPILIH
# ==========================================

# --- MODUL 1: ALAT EXCEL ---
if menu_pilihan == "Alat Excel":
    st.title("🛠️ Manipulasi Petik & Pembersih Karakter")
    st.write("Gunakan alat ini untuk merapikan data Dapodik/SIPD dalam satu kali jalan.")
    
    # ... (KODE ALAT EXCEL TETAP SAMA SEPERTI SEBELUMNYA) ...
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

# --- MODUL 2: IMPORT SIPD KE DATABASE ---
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
            with st.spinner("🚀 Sedang menyedot dan mengirim data ke cloud... (Mohon tunggu, bisa memakan waktu beberapa detik untuk data besar)"):
                try:
                    # 1. Baca Excel
                    df_sipd = pd.read_excel(file_sipd)
                    
                    # 2. Tambahkan kolom TAHAPAN
                    df_sipd['TAHAPAN'] = nama_tahapan
                    
                    # 3. MENGGANTI NAMA KOLOM EXCEL AGAR COCOK DENGAN SQL (Database)
                    # Di SQL kita buat huruf kecil dan pakai garis bawah (_), jadi kita harus samakan!
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
                    # Terapkan pergantian nama kolom
                    df_sipd.rename(columns=pemetaan_kolom, inplace=True)
                    
                    # 4. Ubah nilai kosong (NaN) dengan aman (Ubah tipe ke Object dulu agar Pandas tidak keras kepala)
                    df_sipd = df_sipd.astype(object).where(pd.notnull(df_sipd), None)
                    
                    # 5. Ubah data menjadi format Kamus (Dictionary) siap kirim
                    data_siap_kirim = df_sipd.to_dict(orient='records')
                    
                    # 6. KIRIM KE SUPABASE SECARA DICICIL (1000 Baris Sekali Kirim)
                    # Ini mencegah server down / timeout jika barisnya puluhan ribu
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

import io # Pastikan import io ada di atas (bisa ditaruh di paling atas file app_data.py)

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

        # Ambil SEMUA tahapan di tahun tersebut (sebagai master kolom agar tabel tidak error)
        list_tahapan_tahun = df_tahun['tahapan'].unique().tolist()
        
        col_skpd, col_tahapan = st.columns(2)
        
        # 2. FILTER SKPD
        list_skpd_murni = df_tahun['nama_skpd'].dropna().unique().tolist()
        list_skpd_murni = [str(x).strip() for x in list_skpd_murni if str(x).strip() != ""]
        list_skpd = ["SEMUA SKPD"] + sorted(list_skpd_murni)
        
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Filter SKPD:", options=list_skpd)

        # Siapkan data khusus SKPD yang dipilih (atau Semua)
        if skpd_pilihan != "SEMUA SKPD":
            df_skpd_valid = df_tahun[df_tahun['nama_skpd'] == skpd_pilihan].copy()
        else:
            df_skpd_valid = df_tahun.copy()

        # 3. FILTER TAHAPAN ACUAN (Dinamic: Hanya tahapan yang dimiliki oleh SKPD pilihan)
        list_tahapan_skpd = df_skpd_valid['tahapan'].unique().tolist()
        with col_tahapan:
            tahapan_acuan = st.selectbox("📍 Acuan Nama & Sumber Dana:", options=list_tahapan_skpd)

        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("🧠 Meracik data hierarki berbasis Kode Murni (Anti Bocor)..."):
                
                df_proses = df_skpd_valid.copy()
                
                if df_proses.empty:
                    st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di database.")
                    st.stop()

                # Pembersihan kolom teks dari nilai kosong (NaN) agar aman saat digabungkan jadi string
                kolom_teks = ['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                              'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan', 'nama_sumber_dana']
                for col in kolom_teks:
                    if col in df_proses.columns:
                        df_proses[col] = df_proses[col].fillna("").astype(str).str.strip()

                # ======================================================================
                # 1. BUAT KAMUS NAMA/URAIAN (VLOOKUP DATA)
                # Mengambil nama nomenklatur terakhir yang ada di database agar tidak ganda
                # ======================================================================
                dict_skpd = df_proses.drop_duplicates('kode_skpd', keep='last').set_index('kode_skpd')['nama_skpd'].to_dict()
                dict_urusan = df_proses.drop_duplicates('kode_urusan', keep='last').set_index('kode_urusan')['nama_urusan'].to_dict()
                dict_prog = df_proses.drop_duplicates('kode_program', keep='last').set_index('kode_program')['nama_program'].to_dict()
                dict_keg = df_proses.drop_duplicates('kode_kegiatan', keep='last').set_index('kode_kegiatan')['nama_kegiatan'].to_dict()
                dict_subkeg = df_proses.drop_duplicates('kode_sub_kegiatan', keep='last').set_index('kode_sub_kegiatan')['nama_sub_kegiatan'].to_dict()

                # ======================================================================
                # 2. SISTEM PIVOT UTAMA (HANYA MENGGUNAKAN KODE)
                # ======================================================================
                df_pivot = df_proses.pivot_table(
                    index=['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan'],
                    columns='tahapan', values='pagu', aggfunc='sum'
                ).reset_index().fillna(0)

                # ======================================================================
                # 🛡️ ANTI KEY-ERROR: Paksakan semua kolom tahapan tahun ini ada di pivot
                # ======================================================================
                for t in list_tahapan_tahun:
                    if t not in df_pivot.columns:
                        df_pivot[t] = 0

                # ======================================================================
                # 3. TARIK TEKS SUMBER DANA (Berdasarkan Tahapan Acuan)
                # ======================================================================
                df_sd = df_proses[df_proses['tahapan'] == tahapan_acuan].copy()
                if not df_sd.empty:
                    sd_grouped = df_sd.groupby(['kode_skpd', 'kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                    sd_grouped = sd_grouped[sd_grouped['pagu'] > 0] # Filter pagu nol
                    sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = " + sd_grouped['pagu'].apply(lambda x: f"{x:,.0f}")
                    sd_final = sd_grouped.groupby(['kode_skpd', 'kode_sub_kegiatan'])['teks_sd'].apply(lambda x: ' \n '.join(x)).reset_index()
                    sd_final.rename(columns={'teks_sd': 'Sumber Dana (Acuan)'}, inplace=True)
                else:
                    sd_final = pd.DataFrame(columns=['kode_skpd', 'kode_sub_kegiatan', 'Sumber Dana (Acuan)'])

                # ======================================================================
                # 4. MEMBANGUN HIERARKI (LEVEL 1 SAMPAI 5)
                # ======================================================================
                kumpulan_level = []
                
                # Level 1 - SKPD
                l1 = df_pivot.groupby(['kode_skpd'])[list_tahapan_tahun].sum().reset_index()
                l1['Level'], l1['Sort_Key'] = 1, l1['kode_skpd']
                l1['Kode'], l1['Uraian'] = l1['kode_skpd'], l1['kode_skpd'].map(dict_skpd)
                kumpulan_level.append(l1)

                # Level 2 - Urusan
                l2 = df_pivot.groupby(['kode_skpd', 'kode_urusan'])[list_tahapan_tahun].sum().reset_index()
                l2['Level'], l2['Sort_Key'] = 2, l2['kode_skpd'] + "|" + l2['kode_urusan']
                l2['Kode'], l2['Uraian'] = l2['kode_urusan'], l2['kode_urusan'].map(dict_urusan)
                kumpulan_level.append(l2)

                # Level 3 - Program
                l3 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program'])[list_tahapan_tahun].sum().reset_index()
                l3['Level'], l3['Sort_Key'] = 3, l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                l3['Kode'], l3['Uraian'] = l3['kode_program'], l3['kode_program'].map(dict_prog)
                kumpulan_level.append(l3)

                # Level 4 - Kegiatan
                l4 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan'])[list_tahapan_tahun].sum().reset_index()
                l4['Level'], l4['Sort_Key'] = 4, l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                l4['Kode'], l4['Uraian'] = l4['kode_kegiatan'], l4['kode_kegiatan'].map(dict_keg)
                kumpulan_level.append(l4)

                # Level 5 - Sub Kegiatan
                l5 = df_pivot.copy()
                l5['Level'], l5['Sort_Key'] = 5, l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']
                l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['kode_sub_kegiatan'].map(dict_subkeg)
                l5 = pd.merge(l5, sd_final, on=['kode_skpd', 'kode_sub_kegiatan'], how='left') 
                kumpulan_level.append(l5)

                # ======================================================================
                # 5. GABUNGKAN, URUTKAN, & HITUNG SELISIH
                # ======================================================================
                df_rekap = pd.concat(kumpulan_level, ignore_index=True).sort_values('Sort_Key').reset_index(drop=True)
                
                # Menghitung Selisih dari Tahap Awal vs Tahap Akhir (berdasarkan urutan tahun)
                if len(list_tahapan_tahun) >= 2:
                    col_awal = list_tahapan_tahun[0]
                    col_akhir = list_tahapan_tahun[-1]
                    df_rekap['Selisih (Akhir - Awal)'] = df_rekap[col_akhir] - df_rekap[col_awal]
                else:
                    df_rekap['Selisih (Akhir - Awal)'] = 0

                # Pastikan kolom Sumber Dana ada (walaupun datanya kosong)
                if 'Sumber Dana (Acuan)' not in df_rekap.columns:
                    df_rekap['Sumber Dana (Acuan)'] = ""

                kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)'] + list_tahapan_tahun + ['Selisih (Akhir - Awal)']
                df_web = df_rekap[kolom_final].copy()
                df_web['Sumber Dana (Acuan)'] = df_web['Sumber Dana (Acuan)'].fillna("")
                df_web['Uraian'] = df_web['Uraian'].fillna("-")

                # ======================================================================
                # 6. TAMPILKAN DI WEB
                # ======================================================================
                pesan_sukses = "Semua SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan
                st.success(f"🎉 Rekap Akurat untuk {pesan_sukses} Berhasil Dibuat!")
                st.dataframe(df_web, use_container_width=True)

                # ======================================================================
                # 7. DOWNLOAD EXCEL
                # ======================================================================
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















