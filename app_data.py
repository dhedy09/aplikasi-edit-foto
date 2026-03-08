import streamlit as st
import openpyxl
import io
import re
from datetime import datetime
import pandas as pd
from streamlit_option_menu import option_menu
from supabase import create_client, Client # <--- Library Supabase

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

# --- MODUL 3: REKAP SIPD ---
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Sistem Rekapitulasi SIPD Terpadu")
    st.write("Buat laporan perbandingan Pagu antar tahapan dengan format berjenjang (SKPD hingga Sub Kegiatan).")
    
    # --- FUNGSI CACHING: TARIK DATA SEKALI SAJA ---
    @st.cache_data(ttl=3600, show_spinner=False) # Data disimpan di memori selama 1 jam
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

    # 1. AMBIL SELURUH DATA DARI DATABASE (Atau dari Memori)
    with st.spinner("⏳ Menyiapkan data... (Jika baru pertama buka, ini butuh waktu. Selanjutnya akan instan)"):
        try:
            df = tarik_data_database()
        except Exception as e:
            st.error(f"❌ Gagal menarik data dari database: {e}")
            df = pd.DataFrame() 

    # Tombol untuk Refresh / Kosongkan Memori jika ada data baru diupload
    if st.button("🔄 Refresh Data Database"):
        tarik_data_database.clear()
        st.rerun()

    if df.empty:
        st.info("💡 Database masih kosong atau tidak ada data. Silakan Import SIPD terlebih dahulu.")
    else:
        st.success(f"✅ Berhasil memuat {len(df)} baris data!")
        
        # Rapikan data Pagu agar pasti menjadi angka
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        # --- PERINGATAN JIKA KOLOM TAHUN BELUM ADA ---
        if 'tahun' not in df.columns:
            st.error("⚠️ Sistem mendeteksi kolom 'tahun' tidak ada di database Anda. Pastikan data yang di-upload memiliki kolom tahun.")
            st.stop()

        st.markdown("### ⚙️ Pengaturan Filter & Rekap")
        
        # 1. FILTER TAHUN (Sebagai Induk Filter)
        list_tahun = sorted(df['tahun'].dropna().unique().tolist(), reverse=True)
        tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", options=list_tahun)
        
        # Saring data khusus untuk tahun yang dipilih
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        # =====================================================================
        # TRANSLASI SOTK & PENYERAGAMAN NAMA SKPD (DINAMIS SEPERTI VBA)
        # =====================================================================
        # 1. Ubah paksa kode SKPD lama menjadi kode SKPD baru
        df_tahun['kode_skpd'] = df_tahun['kode_skpd'].replace({"1.01.2.22.0.00.16.0000": "1.01.0.00.0.00.16.0000"})
        
        # 2. Seragamkan Nama SKPD menggunakan nama dari entri terakhir (Tahap Akhir)
        # Ini memastikan tahun 2025 tetap "Dinas Pendidikan dan Kebudayaan", sedangkan 2024 jadi "Dinas Pendidikan"
        dict_skpd = df_tahun.drop_duplicates('kode_skpd', keep='last').set_index('kode_skpd')['nama_skpd'].to_dict()
        df_tahun['nama_skpd'] = df_tahun['kode_skpd'].map(dict_skpd).fillna(df_tahun['nama_skpd'])
        # =====================================================================

        # 2. AMBIL DAFTAR TAHAPAN & SKPD
        list_tahapan = df_tahun['tahapan'].unique().tolist()
        list_skpd = ["SEMUA SKPD"] + sorted([str(x) for x in df_tahun['nama_skpd'].dropna().unique().tolist()])
        
        # 3. KOLOM FILTER SKPD & TAHAPAN
        col_skpd, col_tahapan = st.columns(2)
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Filter SKPD:", options=list_skpd)
        with col_tahapan:
            tahapan_acuan = st.selectbox("📍 Acuan Sumber Dana:", options=list_tahapan)
            
        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("🧠 Sedang meracik Pivot berjenjang..."):
                
                # --- FILTER DATA BERDASARKAN SKPD PILIHAN ---
                df_proses = df_tahun.copy()
                if skpd_pilihan != "SEMUA SKPD":
                    df_proses = df_proses[df_proses['nama_skpd'] == skpd_pilihan]
                    
                # Jika kebetulan SKPD yang dipilih tidak punya data
                if df_proses.empty:
                    st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di database.")
                    st.stop()

                # =====================================================================
                # PENYERAGAMAN NAMA URUSAN s.d SUB KEGIATAN (MENCEGAH PECAH BARIS/0)
                # =====================================================================
                dict_urusan = df_proses.drop_duplicates('kode_urusan', keep='last').set_index('kode_urusan')['nama_urusan'].to_dict()
                dict_program = df_proses.drop_duplicates('kode_program', keep='last').set_index('kode_program')['nama_program'].to_dict()
                dict_kegiatan = df_proses.drop_duplicates('kode_kegiatan', keep='last').set_index('kode_kegiatan')['nama_kegiatan'].to_dict()
                dict_sub = df_proses.drop_duplicates('kode_sub_kegiatan', keep='last').set_index('kode_sub_kegiatan')['nama_sub_kegiatan'].to_dict()

                df_proses['nama_urusan'] = df_proses['kode_urusan'].map(dict_urusan).fillna(df_proses['nama_urusan'])
                df_proses['nama_program'] = df_proses['kode_program'].map(dict_program).fillna(df_proses['nama_program'])
                df_proses['nama_kegiatan'] = df_proses['kode_kegiatan'].map(dict_kegiatan).fillna(df_proses['nama_kegiatan'])
                df_proses['nama_sub_kegiatan'] = df_proses['kode_sub_kegiatan'].map(dict_sub).fillna(df_proses['nama_sub_kegiatan'])
                # =====================================================================

                # Isi nilai kosong pada kode agar tidak error saat diurutkan
                kolom_teks = ['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                              'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan', 'nama_sumber_dana']
                for col in kolom_teks:
                    df_proses[col] = df_proses[col].fillna("")

                # LANGKAH A: PIVOT PAGU PER TAHAPAN
                df_pivot = df_proses.pivot_table(
                    index=['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                           'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'],
                    columns='tahapan',
                    values='pagu',
                    aggfunc='sum'
                ).reset_index().fillna(0)
                
                # --- FIX ERROR KEYERROR ---
                # Memastikan SEMUA tahapan ada di kolom Pivot, meskipun nilainya 0 semua
                for t in list_tahapan:
                    if t not in df_pivot.columns:
                        df_pivot[t] = 0
                # --------------------------
                
                # LANGKAH B: MERACIK TEKS SUMBER DANA
                df_sd = df_proses[df_proses['tahapan'] == tahapan_acuan].copy()
                df_sd['nama_sumber_dana'] = df_sd['nama_sumber_dana'].astype(str).str.strip()
                
                sd_grouped = df_sd.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                
                # Fungsi pembuat format Rupiah Indonesia
                def format_rupiah(angka):
                    return f"Rp {angka:,.0f}".replace(",", ".")
                
                sd_grouped['teks_sd'] = sd_grouped.apply(lambda row: f"{row['nama_sumber_dana']} = {format_rupiah(row['pagu'])}", axis=1)
                
                sd_final = sd_grouped.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan'])['teks_sd'].apply(lambda x: '\n'.join(x)).reset_index()
                sd_final.rename(columns={'teks_sd': 'Sumber Dana'}, inplace=True)

                # LANGKAH C: MEMBUAT HIERARKI BERJENJANG (SKPD -> Sub Kegiatan)
                kumpulan_level = []
                
                # 1. Level SKPD
                l1 = df_pivot.groupby(['kode_skpd', 'nama_skpd'])[list_tahapan].sum().reset_index()
                l1['Kode'], l1['Uraian'] = l1['kode_skpd'], l1['nama_skpd']
                l1['Sort_Key'] = l1['kode_skpd']
                l1['Level'] = 1
                kumpulan_level.append(l1)
                
                # 2. Level Urusan
                l2 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'nama_urusan'])[list_tahapan].sum().reset_index()
                l2['Kode'], l2['Uraian'] = l2['kode_urusan'], l2['nama_urusan']
                l2['Sort_Key'] = l2['kode_skpd'] + "|" + l2['kode_urusan']
                l2['Level'] = 2
                kumpulan_level.append(l2)
                
                # 3. Level Program
                l3 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'])[list_tahapan].sum().reset_index()
                l3['Kode'], l3['Uraian'] = l3['kode_program'], l3['nama_program']
                l3['Sort_Key'] = l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                l3['Level'] = 3
                kumpulan_level.append(l3)
                
                # 4. Level Kegiatan
                l4 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'])[list_tahapan].sum().reset_index()
                l4['Kode'], l4['Uraian'] = l4['kode_kegiatan'], l4['nama_kegiatan']
                l4['Sort_Key'] = l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                l4['Level'] = 4
                kumpulan_level.append(l4)
                
                # 5. Level Sub Kegiatan
                l5 = df_pivot.copy() 
                l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
                l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']
                l5['Level'] = 5
                
                # Gabungkan teks Sumber Dana
                l5 = pd.merge(l5, sd_final, on=['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan'], how='left')
                kumpulan_level.append(l5)
                
                # LANGKAH D: TUMPUK SEMUA LEVEL DAN URUTKAN
                df_rekap = pd.concat(kumpulan_level, ignore_index=True)
                df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
                
                # --- PERBAIKAN LOGIKA SUMBER DANA ---
                df_rekap.loc[(df_rekap['Level'] == 5) & (df_rekap['Sumber Dana'].isna()), 'Sumber Dana'] = "Sumber Dana Tidak Ditemukan"
                df_rekap['Sumber Dana'] = df_rekap['Sumber Dana'].fillna("")
                
                # Susun ulang kolom hasil akhir
                kolom_final = ['Kode', 'Uraian', 'Sumber Dana'] + list_tahapan
                df_tampil = df_rekap[kolom_final].copy()
                
                # LANGKAH E: PROSES WARNA (HANYA UNTUK EXCEL DOWNLOAD)
                def beri_warna_dan_bold(df_t):
                    style_df = pd.DataFrame('', index=df_t.index, columns=df_t.columns)
                    for idx, baris in df_rekap.iterrows():
                        lvl = baris['Level']
                        if lvl == 1:   # SKPD = Biru Tegas
                            style_df.loc[idx, :] = 'background-color: #8EA9DB; font-weight: bold;'
                        elif lvl == 2: # Urusan = Hijau Daun
                            style_df.loc[idx, :] = 'background-color: #A9D08E; font-weight: bold;'
                        elif lvl == 3: # Program = Kuning Emas
                            style_df.loc[idx, :] = 'background-color: #FFD966; font-weight: bold;'
                        elif lvl == 4: # Kegiatan = Oranye Terang
                            style_df.loc[idx, :] = 'background-color: #F4B183; font-weight: bold;'
                    return style_df

                styled_df = df_tampil.style.apply(beri_warna_dan_bold, axis=None)
                
                # TAMPILKAN HASILNYA DI LAYAR
                pesan_sukses = "Semua SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan
                st.success(f"🎉 Rekap untuk {pesan_sukses} Berhasil Dibuat!")
                st.dataframe(df_tampil, use_container_width=True)
                
                # SIAPKAN TOMBOL DOWNLOAD EXCEL
                output_excel = io.BytesIO()
                styled_df.to_excel(output_excel, index=False, engine='openpyxl')
                output_excel.seek(0)
                
                nama_file_skpd = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan.replace(" ", "_").replace("/", "_")
                
                st.download_button(
                    label="📥 Download Excel Rekap (Format Warna & Rupiah)",
                    data=output_excel,
                    file_name=f"Rekap_{nama_file_skpd}_{tahapan_acuan.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )











