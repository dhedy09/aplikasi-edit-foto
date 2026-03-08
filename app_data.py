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
    
    # 1. AMBIL SELURUH DATA DARI DATABASE (Dengan teknik Pagination/Cicil agar aman)
    with st.spinner("⏳ Menghubungkan ke server dan mengunduh seluruh data..."):
        try:
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
                
            df = pd.DataFrame(semua_data)
        except Exception as e:
            st.error(f"❌ Gagal menarik data dari database: {e}")
            df = pd.DataFrame() # DataFrame kosong jika gagal

    if df.empty:
        st.info("💡 Database masih kosong atau tidak ada data. Silakan Import SIPD terlebih dahulu.")
    else:
        st.success(f"✅ Berhasil memuat {len(df)} baris data dari Database!")
        
        # Rapikan data Pagu agar pasti menjadi angka
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        # Ambil daftar tahapan yang tersedia di database
        list_tahapan = df['tahapan'].unique().tolist()
        
        # 2. PENGATURAN REKAP DI LAYAR
        st.markdown("### ⚙️ Pengaturan Rekap")
        tahapan_acuan = st.selectbox(
            "📍 Pilih Tahapan sebagai Acuan Sumber Dana:", 
            options=list_tahapan,
            help="Sumber dana akan diintip dan digabungkan berdasarkan tahapan yang Anda pilih di sini."
        )
        
        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("🧠 Sedang meracik Pivot berjenjang... (Memakan waktu beberapa detik)"):
                # Isi nilai kosong pada kode agar tidak error saat diurutkan
                kolom_teks = ['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                              'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan', 'nama_sumber_dana']
                for col in kolom_teks:
                    df[col] = df[col].fillna("")

                # LANGKAH A: PIVOT PAGU PER TAHAPAN (Dasar Data)
                df_pivot = df.pivot_table(
                    index=['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                           'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'],
                    columns='tahapan',
                    values='pagu',
                    aggfunc='sum'
                ).reset_index().fillna(0)
                
                # LANGKAH B: MERACIK TEKS SUMBER DANA KHUSUS TAHAPAN ACUAN
                df_sd = df[df['tahapan'] == tahapan_acuan].copy()
                # Kelompokkan sumber dana yang sama di 1 sub kegiatan, jumlahkan pagunya
                sd_grouped = df_sd.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                # Format angkanya jadi Rupiah agar enak dibaca di teks
                sd_grouped['teks_sd'] = sd_grouped.apply(lambda row: f"{row['nama_sumber_dana']} = {row['pagu']:,.0f}", axis=1)
                # Gabungkan dengan Enter (\n) jika ada lebih dari 1 sumber dana
                sd_final = sd_grouped.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan'])['teks_sd'].apply(lambda x: ' \n '.join(x)).reset_index()
                sd_final.rename(columns={'teks_sd': 'Sumber Dana'}, inplace=True)

                # LANGKAH C: MEMBUAT HIERARKI BERJENJANG (SKPD -> Sub Kegiatan)
                kumpulan_level = []
                
                # 1. Level SKPD
                l1 = df_pivot.groupby(['kode_skpd', 'nama_skpd'])[list_tahapan].sum().reset_index()
                l1['Kode'], l1['Uraian'] = l1['kode_skpd'], l1['nama_skpd']
                l1['Sort_Key'] = l1['kode_skpd']
                l1['Level'] = 1 # <-- Penanda Level
                kumpulan_level.append(l1)
                
                # 2. Level Urusan
                l2 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'nama_urusan'])[list_tahapan].sum().reset_index()
                l2['Kode'], l2['Uraian'] = l2['kode_urusan'], l2['nama_urusan']
                l2['Sort_Key'] = l2['kode_skpd'] + "|" + l2['kode_urusan']
                l2['Level'] = 2 # <-- Penanda Level
                kumpulan_level.append(l2)
                
                # 3. Level Program
                l3 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'])[list_tahapan].sum().reset_index()
                l3['Kode'], l3['Uraian'] = l3['kode_program'], l3['nama_program']
                l3['Sort_Key'] = l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                l3['Level'] = 3 # <-- Penanda Level
                kumpulan_level.append(l3)
                
                # 4. Level Kegiatan
                l4 = df_pivot.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'])[list_tahapan].sum().reset_index()
                l4['Kode'], l4['Uraian'] = l4['kode_kegiatan'], l4['nama_kegiatan']
                l4['Sort_Key'] = l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                l4['Level'] = 4 # <-- Penanda Level
                kumpulan_level.append(l4)
                
                # 5. Level Sub Kegiatan
                l5 = df_pivot.copy() 
                l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
                l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']
                l5['Level'] = 5 # <-- Penanda Level
                
                # Gabungkan teks Sumber Dana khusus ke Level 5 (Sub Kegiatan)
                l5 = pd.merge(l5, sd_final, on=['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan'], how='left')
                kumpulan_level.append(l5)
                
                # LANGKAH D: TUMPUK SEMUA LEVEL DAN URUTKAN
                df_rekap = pd.concat(kumpulan_level, ignore_index=True)
                df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
                
                # Susun ulang kolom hasil akhir (Tanpa kolom 'Level')
                kolom_final = ['Kode', 'Uraian', 'Sumber Dana'] + list_tahapan
                df_tampil = df_rekap[kolom_final].copy()
                df_tampil['Sumber Dana'] = df_tampil['Sumber Dana'].fillna("")
                
                # LANGKAH E: PROSES WARNA DAN BOLD BERDASARKAN LEVEL
                def beri_warna_dan_bold(df_t):
                    # Buat cetakan kosong dengan ukuran yang sama persis
                    style_df = pd.DataFrame('', index=df_t.index, columns=df_t.columns)
                    
                    # Looping mewarnai berdasarkan Level di belakang layar
                    for idx, baris in df_rekap.iterrows():
                        lvl = baris['Level']
                        if lvl == 1:   # SKPD = Biru Muda
                            style_df.loc[idx, :] = 'background-color: #CFE2F3; font-weight: bold;'
                        elif lvl == 2: # Urusan = Hijau Muda
                            style_df.loc[idx, :] = 'background-color: #D9EAD3; font-weight: bold;'
                        elif lvl == 3: # Program = Kuning Muda
                            style_df.loc[idx, :] = 'background-color: #FFF2CC; font-weight: bold;'
                        elif lvl == 4: # Kegiatan = Oranye Muda
                            style_df.loc[idx, :] = 'background-color: #FCE5CD; font-weight: bold;'
                        # Level 5 (Sub Kegiatan) tidak diisi apa-apa, akan mengikuti default (putih biasa)
                        
                    return style_df

                # Bungkus data dengan warna
                styled_df = df_tampil.style.apply(beri_warna_dan_bold, axis=None)
                
                # TAMPILKAN HASILNYA
                st.success("🎉 Rekap Berhasil Dibuat!")
                st.dataframe(styled_df, use_container_width=True)
                
                # SIAPKAN TOMBOL DOWNLOAD EXCEL
                output_excel = io.BytesIO()
                styled_df.to_excel(output_excel, index=False, engine='openpyxl') # Export membawa warnanya!
                output_excel.seek(0)
                
                st.download_button(
                    label="📥 Download Excel Rekap (Format Warna)",
                    data=output_excel,
                    file_name=f"Rekap_SIPD_Acuan_{tahapan_acuan.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )



