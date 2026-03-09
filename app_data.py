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
# --- MODUL 3: REKAP SIPD (VERSI FINAL - MERGER DPA & REALISASI) ---
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
        # 2.5 JANGKAR MERGER KODE & NOMENKLATUR
        # ==========================================
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

        # ==========================================
        # 3. PEMBUATAN TAB MENU (DITAMBAH TAB 4)
        # ==========================================
        tab1, tab2, tab3, tab4 = st.tabs(["📑 Rekap Hierarki", "💰 Rekap Sumber Dana", "🔗 Integrasi Link DPA", "📈 Evaluasi Realisasi"])

        # -------------------------------------------------------------------
        # TAB 1: REKAP HIERARKI TAHAPAN
        # -------------------------------------------------------------------
        with tab1:
            if st.button(f"🚀 PROSES LAPORAN HIERARKI", type="primary", use_container_width=True, key="btn_tab1"):
                with st.spinner("Memproses Laporan Hierarki..."):
                    kumpulan_level = []
                    def hitung_level(df_input, list_group, level_num):
                        grouped = df_input.groupby(list_group + ['tahapan'])['pagu'].sum().reset_index()
                        pivot = grouped.pivot_table(index=list_group, columns='tahapan', values='pagu', aggfunc='sum', fill_value=0).reset_index()
                        pivot['Level'] = level_num
                        return pivot

                    l1 = hitung_level(df_proses, ['kode_skpd', 'nama_skpd'], 1)
                    l1['Kode'], l1['Uraian'], l1['Sort_Key'] = l1['kode_skpd'], l1['nama_skpd'], l1['kode_skpd']
                    kumpulan_level.append(l1)

                    df_l2 = df_proses[df_proses['kode_urusan'] != ""]
                    if not df_l2.empty:
                        l2 = hitung_level(df_l2, ['kode_skpd', 'kode_urusan', 'nama_urusan'], 2)
                        l2['Kode'], l2['Uraian'], l2['Sort_Key'] = l2['kode_urusan'], l2['nama_urusan'], l2['kode_skpd'] + "|" + l2['kode_urusan']
                        kumpulan_level.append(l2)

                    df_l3 = df_proses[df_proses['kode_program'] != ""]
                    if not df_l3.empty:
                        l3 = hitung_level(df_l3, ['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'], 3)
                        l3['Kode'], l3['Uraian'], l3['Sort_Key'] = l3['kode_program'], l3['nama_program'], l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                        kumpulan_level.append(l3)

                    df_l4 = df_proses[df_proses['kode_kegiatan'] != ""]
                    if not df_l4.empty:
                        l4 = hitung_level(df_l4, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'], 4)
                        l4['Kode'], l4['Uraian'], l4['Sort_Key'] = l4['kode_kegiatan'], l4['nama_kegiatan'], l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                        kumpulan_level.append(l4)

                    df_l5 = df_proses[df_proses['kode_sub_kegiatan'] != ""]
                    if not df_l5.empty:
                        l5 = hitung_level(df_l5, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'], 5)
                        l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
                        l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']

                        df_sd = df_proses[df_proses['tahapan'] == tahapan_acuan]
                        sd_grouped = df_sd[df_sd['pagu'] > 0].groupby(['kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                        if not sd_grouped.empty:
                            sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = Rp " + sd_grouped['pagu'].apply(lambda x: f"{int(x):,}").str.replace(',', '.') + " \n"
                            sd_final = sd_grouped.groupby('kode_sub_kegiatan')['teks_sd'].apply(lambda x: ''.join(x).strip()).reset_index()
                            sd_final.rename(columns={'teks_sd': 'Sumber Dana (Acuan)'}, inplace=True)
                            l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')
                        kumpulan_level.append(l5)

                    df_rekap = pd.concat(kumpulan_level, ignore_index=True)
                    for t in list_tahapan:
                        if t not in df_rekap.columns:
                            df_rekap[t] = 0

                    df_rekap['Selisih (Akhir - Awal)'] = df_rekap[tahap_akhir] - df_rekap[tahap_awal]
                    if 'Sumber Dana (Acuan)' not in df_rekap.columns:
                        df_rekap['Sumber Dana (Acuan)'] = ""
                    df_rekap['Sumber Dana (Acuan)'] = df_rekap['Sumber Dana (Acuan)'].fillna("")

                    df_rekap = df_rekap.sort_values('Sort_Key').reset_index(drop=True)
                    kolom_final = ['Kode', 'Uraian', 'Sumber Dana (Acuan)', 'Level'] + list_tahapan + ['Selisih (Akhir - Awal)']
                    df_hasil = df_rekap[kolom_final]

                    df_tampil = df_hasil.drop(columns=['Level'])
                    kolom_angka = list_tahapan + ['Selisih (Akhir - Awal)']
                    format_dict = {col: "{:,.0f}" for col in kolom_angka}
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

                    import io
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

                    import io
                    output_excel_sd = io.BytesIO()
                    with pd.ExcelWriter(output_excel_sd, engine='openpyxl') as writer:
                        df_hasil_sd.style.apply(highlight_total_excel, axis=1).format(format_dict_sd).to_excel(writer, index=False, sheet_name=f'SumberDana')
                    output_excel_sd.seek(0)
                    
                    st.download_button("📥 Download Excel (Sumber Dana)", output_excel_sd, f"SumberDana_{nama_file_export}_{tahun_pilihan}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_t2")

        # -------------------------------------------------------------------
        # TAB 3: INTEGRASI LINK DPA
        # -------------------------------------------------------------------
        with tab3:
            st.info(f"💡 Menampilkan perbandingan: **{tahap_awal}** vs **{tahap_akhir}**")
            file_link = st.file_uploader("📂 Upload File Excel Link DPA (Pastikan ada kolom 'kode sub' dan 'url')", type=["xlsx", "xls", "csv"], key="up_link")
            
            if st.button(f"🚀 PROSES & GABUNGKAN LINK DPA", type="primary", use_container_width=True, key="btn_tab3"):
                if file_link is None:
                    st.error("⚠️ Mohon upload file Excel/CSV Link DPA terlebih dahulu!")
                else:
                    with st.spinner("Menjahit Link DPA dengan Data Anggaran..."):
                        if file_link.name.endswith('.csv'):
                            df_link = pd.read_csv(file_link)
                        else:
                            df_link = pd.read_excel(file_link)
                        
                        df_link.columns = df_link.columns.str.lower().str.strip()
                        if 'kode sub' not in df_link.columns or 'url' not in df_link.columns:
                            st.error("❌ Gagal! File upload tidak memiliki kolom bernama 'kode sub' atau 'url'.")
                        else:
                            df_link = df_link[['kode sub', 'url']].rename(columns={'kode sub': 'kode_sub_kegiatan'})
                            df_link['kode_sub_kegiatan'] = df_link['kode_sub_kegiatan'].astype(str).str.strip()
                            df_link['url'] = df_link['url'].fillna("")

                            kumpulan_dpa = []
                            def hitung_dpa(df_input, list_group, level_num):
                                df_filter = df_input[df_input['tahapan'].isin([tahap_awal, tahap_akhir])]
                                grouped = df_filter.groupby(list_group + ['tahapan'])['pagu'].sum().reset_index()
                                pivot = grouped.pivot_table(index=list_group, columns='tahapan', values='pagu', aggfunc='sum', fill_value=0).reset_index()
                                pivot['Level'] = level_num
                                for t in [tahap_awal, tahap_akhir]:
                                    if t not in pivot.columns:
                                        pivot[t] = 0
                                return pivot

                            # ... (Proses hierarki DPA disingkat karena sama dengan sebelumnya, langsung lompat ke eksekusi l5) ...
                            l1 = hitung_dpa(df_proses, ['kode_skpd', 'nama_skpd'], 1)
                            l1['Kode'], l1['Uraian'], l1['Sort_Key'] = l1['kode_skpd'], l1['nama_skpd'], l1['kode_skpd']
                            kumpulan_dpa.append(l1)

                            df_l2 = df_proses[df_proses['kode_urusan'] != ""]
                            if not df_l2.empty:
                                l2 = hitung_dpa(df_l2, ['kode_skpd', 'kode_urusan', 'nama_urusan'], 2)
                                l2['Kode'], l2['Uraian'], l2['Sort_Key'] = l2['kode_urusan'], l2['nama_urusan'], l2['kode_skpd'] + "|" + l2['kode_urusan']
                                kumpulan_dpa.append(l2)

                            df_l3 = df_proses[df_proses['kode_program'] != ""]
                            if not df_l3.empty:
                                l3 = hitung_dpa(df_l3, ['kode_skpd', 'kode_urusan', 'kode_program', 'nama_program'], 3)
                                l3['Kode'], l3['Uraian'], l3['Sort_Key'] = l3['kode_program'], l3['nama_program'], l3['kode_skpd'] + "|" + l3['kode_urusan'] + "|" + l3['kode_program']
                                kumpulan_dpa.append(l3)

                            df_l4 = df_proses[df_proses['kode_kegiatan'] != ""]
                            if not df_l4.empty:
                                l4 = hitung_dpa(df_l4, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'nama_kegiatan'], 4)
                                l4['Kode'], l4['Uraian'], l4['Sort_Key'] = l4['kode_kegiatan'], l4['nama_kegiatan'], l4['kode_skpd'] + "|" + l4['kode_urusan'] + "|" + l4['kode_program'] + "|" + l4['kode_kegiatan']
                                kumpulan_dpa.append(l4)

                            df_l5 = df_proses[df_proses['kode_sub_kegiatan'] != ""]
                            if not df_l5.empty:
                                l5 = hitung_dpa(df_l5, ['kode_skpd', 'kode_urusan', 'kode_program', 'kode_kegiatan', 'kode_sub_kegiatan', 'nama_sub_kegiatan'], 5)
                                l5['Kode'], l5['Uraian'] = l5['kode_sub_kegiatan'], l5['nama_sub_kegiatan']
                                l5['Sort_Key'] = l5['kode_skpd'] + "|" + l5['kode_urusan'] + "|" + l5['kode_program'] + "|" + l5['kode_kegiatan'] + "|" + l5['kode_sub_kegiatan']

                                df_sd = df_proses[df_proses['tahapan'] == tahap_akhir]
                                sd_grouped = df_sd[df_sd['pagu'] > 0].groupby(['kode_sub_kegiatan', 'nama_sumber_dana'])['pagu'].sum().reset_index()
                                if not sd_grouped.empty:
                                    sd_grouped['teks_sd'] = sd_grouped['nama_sumber_dana'] + " = Rp " + sd_grouped['pagu'].apply(lambda x: f"{int(x):,}").str.replace(',', '.') + " \n"
                                    sd_final = sd_grouped.groupby('kode_sub_kegiatan')['teks_sd'].apply(lambda x: ''.join(x).strip()).reset_index()
                                    sd_final.rename(columns={'teks_sd': 'Rincian Sumber Dana'}, inplace=True)
                                    l5 = pd.merge(l5, sd_final, on='kode_sub_kegiatan', how='left')
                                
                                l5 = pd.merge(l5, df_link, on='kode_sub_kegiatan', how='left')
                                l5.rename(columns={'url': 'Link DPA'}, inplace=True)
                                kumpulan_dpa.append(l5)

                            df_rekap_dpa = pd.concat(kumpulan_dpa, ignore_index=True)
                            
                            df_rekap_dpa['Anggaran Sebelum'] = df_rekap_dpa[tahap_awal] if tahap_awal in df_rekap_dpa.columns else 0
                            df_rekap_dpa['Anggaran Sesudah'] = df_rekap_dpa[tahap_akhir] if tahap_akhir in df_rekap_dpa.columns else 0
                            df_rekap_dpa['Selisih'] = df_rekap_dpa['Anggaran Sesudah'] - df_rekap_dpa['Anggaran Sebelum']
                            
                            for col in ['Rincian Sumber Dana', 'Link DPA']:
                                if col not in df_rekap_dpa.columns:
                                    df_rekap_dpa[col] = ""
                                df_rekap_dpa[col] = df_rekap_dpa[col].fillna("")

                            df_rekap_dpa = df_rekap_dpa.sort_values('Sort_Key').reset_index(drop=True)

                            kolom_final_dpa = ['Link DPA', 'Kode', 'Uraian', 'Rincian Sumber Dana', 'Anggaran Sebelum', 'Anggaran Sesudah', 'Selisih', 'Level']
                            df_hasil_dpa = df_rekap_dpa[kolom_final_dpa].copy()

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

                            # ... (Warna Excel DPA sama) ...
                            def warna_baris_dpa(row):
                                lvl = df_excel_dpa.loc[row.name, 'Level']
                                if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                                if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                                if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                                if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                                return [''] * len(row)

                            import io
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

        # -------------------------------------------------------------------
        # TAB 4: EVALUASI KINERJA & REALISASI (HYBRID: LOKAL & CLOUD)
        # -------------------------------------------------------------------
        with tab4:
            st.info(f"💡 Patokan Pagu Anggaran menggunakan Tahapan: **{tahap_akhir}**. Anda bisa mengosongkan salah satu input jika tidak tersedia.")
            
            # Pilihan Mode Input (Hybrid)
            sumber_data = st.radio("Pilih Mode Input Data:", ["📂 Upload File Lokal (Excel/CSV)", "🌐 Link Google Sheet (Public)"], horizontal=True)
            
            file_realisasi = None
            file_pptk = None
            link_realisasi = ""
            link_pptk = ""
            
            col_up1, col_up2 = st.columns(2)
            
            # Tampilan Form Berdasarkan Mode Pilihan
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

            # Fungsi Gaib Pengubah Link Google Sheet -> CSV
            def konversi_link_gsheet(url):
                if pd.isna(url) or str(url).strip() == "": return None
                url = str(url).strip()
                if "docs.google.com/spreadsheets" in url:
                    import re
                    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
                    if match:
                        return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"
                return None

            if st.button("🚀 PROSES EVALUASI REALISASI", type="primary", use_container_width=True, key="btn_tab4"):
                with st.spinner("Menyedot data dan menjahit dengan pembersih karakter..."):
                    
                    df_eval = df_proses[df_proses['tahapan'] == tahap_akhir].copy()
                    
                    if df_eval.empty:
                        st.error(f"⚠️ Tidak ada data anggaran untuk tahapan {tahap_akhir}.")
                    else:
                        # 1. Tarik Data Dasar
                        df_base = df_eval.groupby(['kode_sub_kegiatan', 'nama_sub_kegiatan'])['pagu'].sum().reset_index()
                        df_base.rename(columns={'kode_sub_kegiatan': 'Kode Sub', 'nama_sub_kegiatan': 'Uraian Sub Kegiatan', 'pagu': 'Pagu Anggaran'}, inplace=True)
                        
                        # Kolom rahasia pembersih karakter gaib
                        df_base['key_merge'] = df_base['Kode Sub'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
                        
                        # 2. Proses File/Link Realisasi
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
                                df_real['Realisasi'] = pd.to_numeric(df_real['realisasi'], errors='coerce').fillna(0)
                                df_real = df_real.groupby('key_merge')['Realisasi'].sum().reset_index()
                                df_base = pd.merge(df_base, df_real, on='key_merge', how='left')
                                df_base['Realisasi'] = df_base['Realisasi'].fillna(0)
                            else:
                                st.warning("⚠️ Kolom 'kode sub' atau 'realisasi' tidak ditemukan di data Realisasi.")
                                df_base['Realisasi'] = 0
                        else:
                            df_base['Realisasi'] = 0

                        # 3. Proses File/Link Master Bidang / PPTK
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

                        # 4. Kalkulasi Sisa Anggaran & Persentase
                        df_base['Sisa Anggaran'] = df_base['Pagu Anggaran'] - df_base['Realisasi']
                        df_base['% Capaian'] = (df_base['Realisasi'] / df_base['Pagu Anggaran'].replace(0, pd.NA)).fillna(0) * 100

                        # 5. Pengurutan & Penyusunan Kolom
                        df_base = df_base.sort_values(by=['Penanggung Jawab', 'Kode Sub']).reset_index(drop=True)
                        kolom_urut = ['Kode Sub', 'Uraian Sub Kegiatan', 'Pagu Anggaran', 'Realisasi', 'Sisa Anggaran', '% Capaian', 'Penanggung Jawab']
                        df_final_eval = df_base[kolom_urut]

                        # 6. Tampilkan ke Layar
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

                        # 7. Download Excel
                        import io
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














