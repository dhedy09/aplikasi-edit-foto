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
# --- MODUL 3: REKAP SIPD (MURNI SUMIFS & URUTAN TAHAPAN FLEKSIBEL) ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Rekapitulasi Perbandingan Tahapan")
    st.write("Tabel rekapitulasi hierarki anggaran dengan perbandingan antar tahapan.")
    
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
            df = tarik_data_database()
        except Exception as e:
            st.error(f"❌ Gagal menarik data dari database: {e}")
            df = pd.DataFrame() 

    if st.button("🔄 Refresh Data Database"):
        tarik_data_database.clear()
        st.rerun()

    if df.empty:
        st.info("💡 Database masih kosong. Silakan Import SIPD terlebih dahulu.")
        st.stop()
    else:
        st.success(f"✅ Berhasil memuat total {len(df)} baris data!")
        
        # Bersihkan Data Dasar
        df['pagu'] = pd.to_numeric(df['pagu'], errors='coerce').fillna(0)
        
        kolom_teks = ['kode_skpd', 'nama_skpd', 'kode_urusan', 'nama_urusan', 'kode_program', 'nama_program', 
                      'kode_kegiatan', 'nama_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan', 'tahun', 'tahapan']
        for col in kolom_teks:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        if 'tahun' not in df.columns:
            st.error("⚠️ Sistem mendeteksi kolom 'tahun' tidak ada di database.")
            st.stop()
            
        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Filter & Rekap")

        # FILTER TAHUN
        list_tahun = sorted(df['tahun'].dropna().unique().tolist(), reverse=True)
        if not list_tahun:
            st.error("⚠️ Data tahun kosong.")
            st.stop()
            
        col_thn, col_skpd = st.columns(2)
        with col_thn:
            tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", list_tahun)
        
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        # FILTER SKPD
        list_skpd = sorted(df_tahun['nama_skpd'].dropna().unique().tolist())
        list_skpd = [x for x in list_skpd if x != ""]
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

        # MENDAPATKAN TAHAPAN YANG TERSEDIA
        tahapan_tersedia = df_proses['tahapan'].dropna().unique().tolist()
        
        if not tahapan_tersedia:
            st.warning(f"⚠️ Belum ada data tahapan.")
            st.stop()

        st.markdown("#### 📋 Urutan Kolom & Parameter Selisih")
        
        # FITUR BARU: User bisa menyusun urutan tahapan secara manual (Kiri ke Kanan)
        list_tahapan = st.multiselect(
            "Susun urutan kolom tahapan dari Kiri ke Kanan (Hapus/Tambah sesuai kebutuhan):", 
            options=tahapan_tersedia, 
            default=tahapan_tersedia
        )
        
        if not list_tahapan:
            st.error("⚠️ Anda harus memilih minimal 1 tahapan untuk ditampilkan.")
            st.stop()
            
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            tahapan_acuan = st.selectbox("🎯 Tahapan Acuan (Sumber Dana):", list_tahapan, index=len(list_tahapan)-1)
        with col_t2:
            tahap_awal = st.selectbox("📉 Tahapan Awal (Selisih):", list_tahapan, index=0)
        with col_t3:
            tahap_akhir = st.selectbox("📈 Tahapan Akhir (Selisih):", list_tahapan, index=len(list_tahapan)-1)

        if st.button(f"🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("Menghitung ulang menggunakan logika murni database..."):
                
                # FITUR DROP DUPLICATES DIHAPUS SEPENUHNYA AGAR TOTAL AKURAT 100% DENGAN SQL
                # Hanya memastikan baris tanpa kode sub kegiatan (seperti baris subtotal Excel) dibuang
                df_proses = df_proses[df_proses['kode_sub_kegiatan'] != ""]
                df_proses = df_proses[~df_proses['kode_sub_kegiatan'].str.lower().isin(['none', 'nan'])]

                # 1. BUAT KAMUS NAMA (VLOOKUP)
                dict_nama = {}
                for c_kode, c_nama in [('kode_skpd','nama_skpd'), ('kode_urusan','nama_urusan'), 
                                       ('kode_program','nama_program'), ('kode_kegiatan','nama_kegiatan'), 
                                       ('kode_sub_kegiatan','nama_sub_kegiatan')]:
                    temp = df_proses.drop_duplicates(c_kode).set_index(c_kode)[c_nama].to_dict()
                    dict_nama.update(temp)

                # 2. MESIN SUMIFS (MENGGUNAKAN PANDAS GROUPBY UNSTACK)
                kumpulan_level = []
                
                l1 = df_proses.groupby(['kode_skpd', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                l1['Level'], l1['Sort_Key'], l1['Kode'] = 1, l1['kode_skpd'], l1['kode_skpd']
                kumpulan_level.append(l1)

                l2 = df_proses.groupby(['kode_skpd', 'kode_urusan', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                l2['Level'], l2['Sort_Key'], l2['Kode'] = 2, l2['kode_skpd'] + "|" + l2['kode_urusan'], l2['kode_urusan']
                kumpulan_level.append(l2)

                l3 = df_proses.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                l3['Level'], l3['Sort_Key'], l3['Kode'] = 3, l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program'], l3['kode_program']
                kumpulan_level.append(l3)

                l4 = df_proses.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                l4['Level'], l4['Sort_Key'], l4['Kode'] = 4, l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan'], l4['kode_kegiatan']
                kumpulan_level.append(l4)

                l5 = df_proses.groupby(['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'tahapan'])['pagu'].sum().unstack(fill_value=0).reset_index()
                l5['Level'], l5['Sort_Key'], l5['Kode'] = 5, l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan'], l5['kode_sub_kegiatan']
                
                df_sd = df_proses[df_proses['tahapan'] == tahapan_acuan]
                sd_grouped = df_sd[df_sd['pagu'] > 0].groupby(['kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                
                if not sd_grouped.empty:
                    sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = Rp. " + sd_grouped['pagu'].apply(lambda x: f"{int(x):,}").str.replace(',', '.') + " \n"
                    sd_final = sd_grouped.groupby('kode_sub_kegiatan')['teks_sd'].apply(lambda x: ''.join(x).strip()).reset_index()
                    sd_final.rename(columns={'teks_sd': 'Sumber Dana (Acuan)'}, inplace=True)
                    l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')

                kumpulan_level.append(l5)

                # 3. GABUNGKAN & RAPIKAN TABEL
                df_rekap = pd.concat(kumpulan_level, ignore_index=True)
                
                for t in list_tahapan:
                    if t not in df_rekap.columns:
                        df_rekap[t] = 0

                df_rekap['Uraian'] = df_rekap['Kode'].map(dict_nama).fillna("-")
                df_rekap['Selisih (Akhir - Awal)'] = df_rekap[tahap_akhir] - df_rekap[tahap_awal]
                
                if 'Sumber Dana (Acuan)' not in df_rekap.columns:
                    df_rekap['Sumber Dana (Acuan)'] = ""
                df_rekap['Sumber Dana (Acuan)'] = df_rekap['Sumber Dana (Acuan)'].fillna("")

                df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
                
                # Memaksa kolom tahapan sesuai dengan urutan pilihan pengguna
                kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)', 'Level'] + list_tahapan + ['Selisih (Akhir - Awal)']
                df_hasil = df_rekap[kolom_final]

                # 4. RENDER TAMPILAN WEB (POLOS / NORMAL)
                df_tampil = df_hasil.drop(columns=['Level'])
                
                kolom_angka = list_tahapan + ['Selisih (Akhir - Awal)']
                format_dict = {col: "{:,.0f}" for col in kolom_angka}
                
                styled_df_web = df_tampil.style.format(format_dict).set_properties(subset=['Sumber Dana (Acuan)'], **{'white-space': 'pre-wrap'})
                
                st.success(f"✅ Rekapitulasi berhasil disusun! Angka dijamin 100% sama dengan Database.")
                st.dataframe(styled_df_web, use_container_width=True, height=600)

                # 5. FITUR EXPORT EXCEL
                def warna_baris_excel(row):
                    lvl = df_hasil.loc[row.name, 'Level']
                    if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                    if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                    if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                    if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                    return [''] * len(row)

                styled_df_excel = df_tampil.style.apply(warna_baris_excel, axis=1).format(format_dict)

                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    styled_df_excel.to_excel(writer, index=False, sheet_name=f'Rekap_{tahun_pilihan}')
                output_excel.seek(0)
                
                nama_file = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan.replace(" ", "_").replace("/", "_")
                
                st.download_button(
                    label=f"📥 Download Hasil Rekap (Excel)",
                    data=output_excel,
                    file_name=f"Rekap_SIPD_{nama_file}_{tahun_pilihan}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )





