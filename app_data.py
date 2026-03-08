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

        # =====================================================================
        # SOLUSI: GANTI KODE SKPD LAMA KE BARU (Tanpa merusak total)
        # =====================================================================
        df_tahun['kode_skpd'] = df_tahun['kode_skpd'].replace({"1.01.2.22.0.00.16.0000": "1.01.0.00.0.00.16.0000"})
        
        list_tahapan = df_tahun['tahapan'].unique().tolist()
        
        # 2. FILTER TAHAPAN ACUAN (Sebagai "Source of Truth" untuk Nama & Sumber Dana)
        col_skpd, col_tahapan = st.columns(2)
        with col_tahapan:
            tahapan_acuan = st.selectbox("📍 Acuan Nama & Sumber Dana:", options=list_tahapan)
            
        # Perbaiki list SKPD di dropdown agar sesuai dengan nama di Tahapan Acuan
        df_acuan_dropdown = df_tahun[df_tahun['tahapan'] == tahapan_acuan]
        dict_nama_skpd = dict(zip(df_acuan_dropdown['kode_skpd'], df_acuan_dropdown['nama_skpd']))
        dict_nama_skpd_fallback = dict(zip(df_tahun['kode_skpd'], df_tahun['nama_skpd'])) # Jaga-jaga jika kosong di tahapan acuan
        
        df_tahun['nama_skpd_dropdown'] = df_tahun['kode_skpd'].map(dict_nama_skpd).fillna(df_tahun['kode_skpd'].map(dict_nama_skpd_fallback))
        list_skpd = ["SEMUA SKPD"] + sorted([str(x) for x in df_tahun['nama_skpd_dropdown'].dropna().unique().tolist()])
        
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Filter SKPD:", options=list_skpd)

        if st.button("🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("🧠 Menghitung dengan Algoritma Dictionary (Adaptasi VBA)..."):
                
                # --- FILTER DATA BERDASARKAN SKPD PILIHAN ---
                df_proses = df.copy()
                if skpd_pilihan != "SEMUA SKPD":
                    df_proses = df_proses[df_proses['nama_skpd'] == skpd_pilihan]
                    
                if df_proses.empty:
                    st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di database.")
                    st.stop()

                # Isi nilai kosong agar tidak error
                for col in df_proses.columns:
                    if df_proses[col].dtype == object:
                        df_proses[col] = df_proses[col].fillna("").astype(str).str.strip()

                # ==========================================================
                # DAFTAR TRANSLASI SOTK (KODE LAMA -> KODE BARU)
                # ==========================================================
                df_proses['kode_skpd'] = df_proses['kode_skpd'].replace({"1.01.2.22.0.00.16.0000": "1.01.0.00.0.00.16.0000"})

                # ==========================================================
                # INISIALISASI DICTIONARY (MENGADOPSI LOGIKA VBA)
                # ==========================================================
                dict_skpd = {}
                dict_urusan = {}
                dict_prog = {}
                dict_keg = {}
                dict_sub = {}
                
                dict_nama = {}
                dict_pagu = {}
                dict_sd = {}
                
                # LANGKAH 1: Ambil List Tahapan dan Tahap Akhir (Acuan)
                # Kita gunakan list urutan tahapan yang unik, tahap akhirnya mengikuti input dropdown pengguna
                list_tahapan = df_proses['tahapan'].unique().tolist()
                tahap_akhir = tahapan_acuan 
                
                # LANGKAH 2: MEMBACA & MENGELOMPOKKAN DATABASE (Row by Row)
                for row in df_proses.itertuples(index=False):
                    # Menyesuaikan dengan nama kolom pandas
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
                    pagu = float(row.pagu) if str(row.pagu).replace('.','',1).isdigit() else 0.0
                    tahapan = row.tahapan
                    
                    # Simpan Nama (Update hanya jika ini Tahap Akhir atau nama belum ada)
                    if kSKPD not in dict_nama: dict_nama[kSKPD] = nSKPD
                    if kUrusan not in dict_nama: dict_nama[kUrusan] = nUrusan
                    if kProg not in dict_nama: dict_nama[kProg] = nProg
                    if kKeg not in dict_nama: dict_nama[kKeg] = nKeg
                    if kSub not in dict_nama: dict_nama[kSub] = nSub
                    
                    if tahapan == tahap_akhir:
                        dict_nama[kSKPD] = nSKPD
                        dict_nama[kUrusan] = nUrusan
                        dict_nama[kProg] = nProg
                        dict_nama[kKeg] = nKeg
                        dict_nama[kSub] = nSub

                    # Simpan Hierarki (Set/Dictionary bercabang)
                    dict_skpd[kSKPD] = 1
                    dict_urusan.setdefault(kSKPD, {})[kUrusan] = 1
                    dict_prog.setdefault(kUrusan, {})[kProg] = 1
                    dict_keg.setdefault(kProg, {})[kKeg] = 1
                    dict_sub.setdefault(kKeg, {})[kSub] = 1
                    
                    # Simpan Pagu per Kode & Tahapan
                    dict_pagu[f"{kSKPD}|{tahapan}"] = dict_pagu.get(f"{kSKPD}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kUrusan}|{tahapan}"] = dict_pagu.get(f"{kUrusan}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kProg}|{tahapan}"] = dict_pagu.get(f"{kProg}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kKeg}|{tahapan}"] = dict_pagu.get(f"{kKeg}|{tahapan}", 0) + pagu
                    dict_pagu[f"{kSub}|{tahapan}"] = dict_pagu.get(f"{kSub}|{tahapan}", 0) + pagu
                    
                    # Simpan Sumber Dana khusus untuk Sub Kegiatan
                    if sd and pagu > 0:
                        dict_sd.setdefault(kSub, {}).setdefault(tahapan, {})
                        dict_sd[kSub][tahapan][sd] = dict_sd[kSub][tahapan].get(sd, 0) + pagu

                # LANGKAH 3: MENYUSUN BARIS REKAP SESUAI HIERARKI
                data_rekap = []
                
                def get_sd_string(k_sub, thp):
                    if k_sub in dict_sd and thp in dict_sd[k_sub]:
                        arr_sd = []
                        for s_dana, val_pagu in dict_sd[k_sub][thp].items():
                            if val_pagu > 0:
                                arr_sd.append(f"{s_dana} = {val_pagu:,.0f}".replace(",", "."))
                        return " \n ".join(arr_sd)
                    return ""

                for k_skpd in dict_skpd.keys():
                    # Level 1: SKPD
                    row_data = {'Kode': k_skpd, 'Uraian': dict_nama.get(k_skpd, ''), 'Sumber Dana (Tahap Akhir)': '', 'Level': 1}
                    for thp in list_tahapan: row_data[f"Pagu {thp}"] = dict_pagu.get(f"{k_skpd}|{thp}", 0)
                    data_rekap.append(row_data)
                    
                    for k_urs in dict_urusan.get(k_skpd, {}).keys():
                        # Level 2: Urusan
                        row_data = {'Kode': k_urs, 'Uraian': dict_nama.get(k_urs, ''), 'Sumber Dana (Tahap Akhir)': '', 'Level': 2}
                        for thp in list_tahapan: row_data[f"Pagu {thp}"] = dict_pagu.get(f"{k_urs}|{thp}", 0)
                        data_rekap.append(row_data)
                        
                        for k_prg in dict_prog.get(k_urs, {}).keys():
                            # Level 3: Program
                            row_data = {'Kode': k_prg, 'Uraian': dict_nama.get(k_prg, ''), 'Sumber Dana (Tahap Akhir)': '', 'Level': 3}
                            for thp in list_tahapan: row_data[f"Pagu {thp}"] = dict_pagu.get(f"{k_prg}|{thp}", 0)
                            data_rekap.append(row_data)
                            
                            for k_keg in dict_keg.get(k_prg, {}).keys():
                                # Level 4: Kegiatan
                                row_data = {'Kode': k_keg, 'Uraian': dict_nama.get(k_keg, ''), 'Sumber Dana (Tahap Akhir)': '', 'Level': 4}
                                for thp in list_tahapan: row_data[f"Pagu {thp}"] = dict_pagu.get(f"{k_keg}|{thp}", 0)
                                data_rekap.append(row_data)
                                
                                for k_sub in dict_sub.get(k_keg, {}).keys():
                                    # Level 5: Sub Kegiatan
                                    str_sd = get_sd_string(k_sub, tahap_akhir)
                                    row_data = {'Kode': k_sub, 'Uraian': dict_nama.get(k_sub, ''), 'Sumber Dana (Tahap Akhir)': str_sd, 'Level': 5}
                                    for thp in list_tahapan: row_data[f"Pagu {thp}"] = dict_pagu.get(f"{k_sub}|{thp}", 0)
                                    data_rekap.append(row_data)

                # Convert ke DataFrame Pandas
                df_rekap = pd.DataFrame(data_rekap)

                # Menghitung Selisih (Tahap Terakhir - Tahap Pertama)
                if len(list_tahapan) >= 2:
                    col_awal = f"Pagu {list_tahapan[0]}"
                    col_akhir = f"Pagu {list_tahapan[-1]}"
                    df_rekap['Selisih (Akhir - Awal)'] = df_rekap[col_akhir] - df_rekap[col_awal]
                else:
                    df_rekap['Selisih (Akhir - Awal)'] = 0

                # LANGKAH 4: WARNA DAN TAMPILAN
                kolom_tampil = [c for c in df_rekap.columns if c != 'Level']
                df_tampil = df_rekap[kolom_tampil].copy()

                def beri_warna_dan_bold(df_t):
                    style_df = pd.DataFrame('', index=df_t.index, columns=df_t.columns)
                    for idx, baris in df_rekap.iterrows():
                        lvl = baris['Level']
                        if lvl == 1:   
                            style_df.loc[idx, :] = 'background-color: #DDEBF7; font-weight: bold;' # Warna SKPD
                        elif lvl == 2: 
                            style_df.loc[idx, :] = 'background-color: #FFF2CC; font-weight: bold;' # Warna Urusan
                        elif lvl == 3: 
                            style_df.loc[idx, :] = 'background-color: #FCE4D6; font-weight: bold;' # Warna Program
                        elif lvl == 4: 
                            style_df.loc[idx, :] = 'background-color: #E2EFDA; font-weight: bold;' # Warna Kegiatan
                    return style_df

                gaya_header = [{
                    'selector': 'th',
                    'props': [
                        ('background-color', 'black'),
                        ('color', 'white'),              
                        ('font-weight', 'bold'),
                        ('text-align', 'center'),
                        ('font-size', '15px')
                    ]
                }]

                # Format angka rupiah agar enak dilihat
                kolom_angka = [c for c in df_tampil.columns if "Pagu" in c or "Selisih" in c]
                format_dict = {col: "{:,.0f}" for col in kolom_angka}
                
                styled_df = df_tampil.style.apply(beri_warna_dan_bold, axis=None)\
                                           .set_table_styles(gaya_header)\
                                           .format(format_dict)
                
                # TAMPILKAN HASILNYA
                pesan_sukses = "Semua SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan
                st.success(f"🎉 Rekap untuk {pesan_sukses} Berhasil Dibuat!")
                st.dataframe(styled_df, use_container_width=True)
                
                # SIAPKAN TOMBOL DOWNLOAD EXCEL
                import io
                output_excel = io.BytesIO()
                styled_df.to_excel(output_excel, index=False, engine='openpyxl')
                output_excel.seek(0)
                
                nama_file_skpd = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else skpd_pilihan.replace(" ", "_").replace("/", "_")
                
                st.download_button(
                    label="📥 Download Excel Rekap (Format Warna)",
                    data=output_excel,
                    file_name=f"Rekap_{nama_file_skpd}_{tahapan_acuan.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )












