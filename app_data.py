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

# -------------------------------------------------------------------------
# --- MODUL 3: REKAP SIPD (VERSI FINAL - LOGIKA SQL MURNI) ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Rekapitulasi Perbandingan Tahapan")
    st.write("Tabel rekapitulasi hierarki anggaran berdasarkan kalkulasi SQL murni.")
    
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
        # 1. PERSIAPAN DATA DASAR (TANPA MENGUBAH TEKS ASLI)
        # ==========================================
        df = df_mentah.copy()
        
        # Amankan Pagu (Ubah ke angka, 437699000.0 akan terbaca sempurna)
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        # Amankan Tahun (Hanya menghilangkan .0 jika terbaca sebagai desimal)
        if 'tahun' in df.columns:
            df['tahun'] = df['tahun'].astype(str).str.replace('.0', '', regex=False)
        else:
            st.error("⚠️ Kolom 'tahun' tidak ditemukan!")
            st.stop()

        # Ubah semua data kosong (NaN) menjadi teks kosong agar filter dan Groupby tidak error
        df = df.fillna("")

        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Filter & Rekap")

        # ==========================================
        # 2. SISTEM FILTER
        # ==========================================
        list_tahun = sorted([t for t in df['tahun'].unique() if t != ""], reverse=True)
        col_thn, col_skpd = st.columns(2)
        
        with col_thn:
            tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", list_tahun)
        
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        list_skpd = sorted([s for s in df_tahun['nama_skpd'].unique() if s != ""])
        list_skpd.insert(0, "SEMUA SKPD")
        
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Pilih SKPD:", list_skpd)

        if skpd_pilihan != "SEMUA SKPD":
            df_proses = df_tahun[df_tahun['nama_skpd'] == skpd_pilihan].copy()
        else:
            df_proses = df_tahun.copy()

        if df_proses.empty:
            st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di tahun {tahun_pilihan}.")
            st.stop()

        # ==========================================
        # 3. PENGATURAN TAHAPAN
        # ==========================================
        tahapan_tersedia = [t for t in df_proses['tahapan'].unique() if t != ""]
        
        st.markdown("#### 📋 Urutan Kolom & Parameter Selisih")
        
        list_tahapan = st.multiselect(
            "Susun urutan tahapan (Kiri ke Kanan):", 
            options=tahapan_tersedia, 
            default=tahapan_tersedia
        )
        
        if not list_tahapan:
            st.error("⚠️ Pilih minimal 1 tahapan.")
            st.stop()
            
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            tahapan_acuan = st.selectbox("🎯 Acuan Sumber Dana:", list_tahapan, index=len(list_tahapan)-1)
        with col_t2:
            tahap_awal = st.selectbox("📉 Tahapan Awal (Pengurang):", list_tahapan, index=0)
        with col_t3:
            tahap_akhir = st.selectbox("📈 Tahapan Akhir (Dikurangi):", list_tahapan, index=len(list_tahapan)-1)

        # ==========================================
        # 4. PROSES KALKULASI SQL MURNI
        # ==========================================
        if st.button(f"🚀 PROSES & BUAT LAPORAN REKAP", type="primary", use_container_width=True):
            with st.spinner("Memproses Laporan..."):
                
                kumpulan_level = []

                # Fungsi bantuan agar Groupby & Pivot stabil
                def hitung_level(df_input, list_group, level_num):
                    # Groupby persis seperti SQL
                    grouped = df_input.groupby(list_group + ['tahapan'])['pagu'].sum().reset_index()
                    # Ubah tahapan jadi kolom
                    pivot = grouped.pivot_table(index=list_group, columns='tahapan', values='pagu', aggfunc='sum', fill_value=0).reset_index()
                    pivot['Level'] = level_num
                    return pivot

                # --- LEVEL 1: SKPD ---
                l1 = hitung_level(df_proses, ['kode_skpd', 'nama_skpd'], 1)
                l1['Kode'], l1['Uraian'], l1['Sort_Key'] = l1['kode_skpd'], l1['nama_skpd'], l1['kode_skpd']
                kumpulan_level.append(l1)

                # --- LEVEL 2: URUSAN ---
                df_l2 = df_proses[df_proses['kode_urusan'] != ""]
                if not df_l2.empty:
                    l2 = hitung_level(df_l2, ['kode_skpd', 'kode_urusan', 'nama_urusan'], 2)
                    l2['Kode'], l2['Uraian'], l2['Sort_Key'] = l2['kode_urusan'], l2['nama_urusan'], l2['kode_skpd'] + "|" + l2['kode_urusan']
                    kumpulan_level.append(l2)

                # --- LEVEL 3: PROGRAM ---
                df_l3 = df_proses[df_proses['kode_program'] != ""]
                if not df_l3.empty:
                    l3 = hitung_level(df_l3, ['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'], 3)
                    l3['Kode'], l3['Uraian'], l3['Sort_Key'] = l3['kode_program'], l3['nama_program'], l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                    kumpulan_level.append(l3)

                # --- LEVEL 4: KEGIATAN ---
                df_l4 = df_proses[df_proses['kode_kegiatan'] != ""]
                if not df_l4.empty:
                    l4 = hitung_level(df_l4, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'], 4)
                    l4['Kode'], l4['Uraian'], l4['Sort_Key'] = l4['kode_kegiatan'], l4['nama_kegiatan'], l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                    kumpulan_level.append(l4)

                # --- LEVEL 5: SUB KEGIATAN ---
                df_l5 = df_proses[df_proses['kode_sub_kegiatan'] != ""]
                if not df_l5.empty:
                    l5 = hitung_level(df_l5, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'], 5)
                    l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
                    l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']

                    # Sumber Dana (Acuan) Khusus Level 5
                    df_sd = df_proses[df_proses['tahapan'] == tahapan_acuan]
                    sd_grouped = df_sd[df_sd['pagu'] > 0].groupby(['kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                    if not sd_grouped.empty:
                        sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = Rp. " + sd_grouped['pagu'].apply(lambda x: f"{int(x):,}").str.replace(',', '.') + " \n"
                        sd_final = sd_grouped.groupby('kode_sub_kegiatan')['teks_sd'].apply(lambda x: ''.join(x).strip()).reset_index()
                        sd_final.rename(columns={'teks_sd': 'Sumber Dana (Acuan)'}, inplace=True)
                        l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')
                    kumpulan_level.append(l5)

                # ==========================================
                # 5. GABUNGKAN & RAPIKAN LAPORAN
                # ==========================================
                df_rekap = pd.concat(kumpulan_level, ignore_index=True)
                
                # Pastikan semua tahapan yang dipilih ada kolomnya
                for t in list_tahapan:
                    if t not in df_rekap.columns:
                        df_rekap[t] = 0

                # Hitung Selisih
                df_rekap['Selisih (Akhir - Awal)'] = df_rekap[tahap_akhir] - df_rekap[tahap_awal]
                
                if 'Sumber Dana (Acuan)' not in df_rekap.columns:
                    df_rekap['Sumber Dana (Acuan)'] = ""
                df_rekap['Sumber Dana (Acuan)'] = df_rekap['Sumber Dana (Acuan)'].fillna("")

                # Urutkan berdasarkan hierarki dan pilih kolom final
                df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
                kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)', 'Level'] + list_tahapan + ['Selisih (Akhir - Awal)']
                df_hasil = df_rekap[kolom_final]

                # ==========================================
                # 6. TAMPILAN WEB & EXPORT EXCEL
                # ==========================================
                df_tampil = df_hasil.drop(columns=['Level'])
                kolom_angka = list_tahapan + ['Selisih (Akhir - Awal)']
                format_dict = {col: "{:,.0f}" for col in kolom_angka}
                
                styled_df_web = df_tampil.style.format(format_dict).set_properties(subset=['Sumber Dana (Acuan)'], **{'white-space': 'pre-wrap'})
                
                st.success(f"✅ Laporan Berhasil Dibuat!")
                st.dataframe(styled_df_web, use_container_width=True, height=600)

                # Export Excel dengan Warna
                def warna_baris_excel(row):
                    lvl = df_hasil.loc[row.name, 'Level']
                    if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                    if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                    if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                    if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                    return [''] * len(row)

                styled_df_excel = df_tampil.style.apply(warna_baris_excel, axis=1).format(format_dict)

                import io
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    styled_df_excel.to_excel(writer, index=False, sheet_name=f'Laporan_{tahun_pilihan}')
                output_excel.seek(0)
                
                nama_file = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan.replace(" ", "_").replace("/", "_")
                st.download_button(
                    label=f"📥 Download Laporan Lengkap (Excel)",
                    data=output_excel,
                    file_name=f"Laporan_Rekap_SIPD_{nama_file}_{tahun_pilihan}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )







