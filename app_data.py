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

        st.markdown("### ⚙️ Pengaturan Filter & Rekap")

        list_tahun = sorted(df['tahun'].dropna().unique().tolist(), reverse=True)
        tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", options=list_tahun)
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        list_tahapan_tahun = sorted(df_tahun['tahapan'].unique().tolist())

        col_skpd, col_tahapan = st.columns(2)

        list_skpd_murni = df_tahun['nama_skpd'].dropna().unique().tolist()
        list_skpd_murni = [str(x).strip() for x in list_skpd_murni if str(x).strip() != ""]
        list_skpd = ["SEMUA SKPD"] + sorted(list_skpd_murni)

        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Filter SKPD:", options=list_skpd)

        if skpd_pilihan != "SEMUA SKPD":
            df_skpd_valid = df_tahun[df_tahun['nama_skpd'] == skpd_pilihan]
        else:
            df_skpd_valid = df_tahun

        list_tahapan_skpd = sorted(df_skpd_valid['tahapan'].unique().tolist())

        with col_tahapan:
            tahapan_acuan = st.selectbox("📍 Acuan Nama & Sumber Dana:", options=list_tahapan_skpd)

        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):

            with st.spinner("🧠 Memproses data..."):

                df_proses = df_skpd_valid.copy()

                kolom_teks = ['kode_skpd','nama_skpd','kode_urusan','nama_urusan',
                              'kode_program','nama_program','kode_kegiatan','nama_kegiatan',
                              'kode_sub_kegiatan','nama_sub_kegiatan','nama_sumber_dana']

                for col in kolom_teks:
                    df_proses[col] = df_proses[col].fillna("").astype(str).str.strip()

                # ======================================================
                # PERHITUNGAN PAGU (ALGORITMA VBA)
                # ======================================================

                from collections import defaultdict

                dict_skpd={}
                dict_urusan=defaultdict(dict)
                dict_prog=defaultdict(dict)
                dict_keg=defaultdict(dict)
                dict_sub=defaultdict(dict)

                dict_nama={}
                dict_pagu=defaultdict(float)
                dict_sd=defaultdict(lambda: defaultdict(lambda: defaultdict(float)))

                tahap_akhir=list_tahapan_tahun[-1]

                for _,row in df_proses.iterrows():

                    k_skpd=row['kode_skpd']
                    n_skpd=row['nama_skpd']

                    k_urusan=row['kode_urusan']
                    n_urusan=row['nama_urusan']

                    k_prog=row['kode_program']
                    n_prog=row['nama_program']

                    k_keg=row['kode_kegiatan']
                    n_keg=row['nama_kegiatan']

                    k_sub=row['kode_sub_kegiatan']
                    n_sub=row['nama_sub_kegiatan']

                    sd=row['nama_sumber_dana']
                    tahapan=row['tahapan']
                    pagu=row['pagu']

                    dict_skpd[k_skpd]=1
                    dict_urusan[k_skpd][k_urusan]=1
                    dict_prog[k_urusan][k_prog]=1
                    dict_keg[k_prog][k_keg]=1
                    dict_sub[k_keg][k_sub]=1

                    dict_nama[k_skpd]=n_skpd
                    dict_nama[k_urusan]=n_urusan
                    dict_nama[k_prog]=n_prog
                    dict_nama[k_keg]=n_keg
                    dict_nama[k_sub]=n_sub

                    dict_pagu[(k_skpd,tahapan)]+=pagu
                    dict_pagu[(k_urusan,tahapan)]+=pagu
                    dict_pagu[(k_prog,tahapan)]+=pagu
                    dict_pagu[(k_keg,tahapan)]+=pagu
                    dict_pagu[(k_sub,tahapan)]+=pagu

                    dict_sd[k_sub][tahapan][sd]+=pagu

                # ======================================================
                # MEMBANGUN HIERARKI
                # ======================================================

                rows=[]

                for sk in dict_skpd.keys():

                    row={"Kode":sk,"Uraian":dict_nama.get(sk,""),"Level":1}
                    for t in list_tahapan_tahun:
                        row[t]=dict_pagu[(sk,t)]
                    row["Sumber Dana (Acuan)"]=""
                    rows.append(row)

                    for ur in dict_urusan[sk].keys():

                        row={"Kode":ur,"Uraian":dict_nama.get(ur,""),"Level":2}
                        for t in list_tahapan_tahun:
                            row[t]=dict_pagu[(ur,t)]
                        row["Sumber Dana (Acuan)"]=""
                        rows.append(row)

                        for pr in dict_prog[ur].keys():

                            row={"Kode":pr,"Uraian":dict_nama.get(pr,""),"Level":3}
                            for t in list_tahapan_tahun:
                                row[t]=dict_pagu[(pr,t)]
                            row["Sumber Dana (Acuan)"]=""
                            rows.append(row)

                            for kg in dict_keg[pr].keys():

                                row={"Kode":kg,"Uraian":dict_nama.get(kg,""),"Level":4}
                                for t in list_tahapan_tahun:
                                    row[t]=dict_pagu[(kg,t)]
                                row["Sumber Dana (Acuan)"]=""
                                rows.append(row)

                                for sb in dict_sub[kg].keys():

                                    teks_sd=""

                                    if tahapan_acuan in dict_sd[sb]:
                                        for sdKey in dict_sd[sb][tahapan_acuan]:
                                            nilai=dict_sd[sb][tahapan_acuan][sdKey]
                                            if nilai>0:
                                                teks_sd+=f"{sdKey} = {nilai:,.0f}\n"

                                    row={"Kode":sb,"Uraian":dict_nama.get(sb,""),"Level":5}

                                    for t in list_tahapan_tahun:
                                        row[t]=dict_pagu[(sb,t)]

                                    row["Sumber Dana (Acuan)"]=teks_sd.strip()

                                    rows.append(row)

                df_rekap=pd.DataFrame(rows)

                col_awal=list_tahapan_tahun[0]
                col_akhir=list_tahapan_tahun[-1]

                df_rekap['Selisih (Akhir - Awal)']=df_rekap[col_akhir]-df_rekap[col_awal]

                kolom_final=['Kode','Uraian','Sumber Dana (Acuan)']+list_tahapan_tahun+['Selisih (Akhir - Awal)']
                df_web=df_rekap[kolom_final].copy()

                st.success("🎉 Rekap Berhasil Dibuat!")
                st.dataframe(df_web,use_container_width=True)

                output_excel=io.BytesIO()
                df_web.to_excel(output_excel,index=False,engine='openpyxl')
                output_excel.seek(0)

                st.download_button(
                    label="📥 Download Excel Rekap",
                    data=output_excel,
                    file_name="Rekap_SIPD.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )














