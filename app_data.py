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
# --- MODUL 3: REKAP SIPD (GABUNGAN PAGINATION & HIERARKI AKURAT) ---
# -------------------------------------------------------------------------
elif menu_pilihan == "Rekap SIPD":
    st.title("📊 Rekapitulasi Perbandingan Tahapan")
    st.write("Tabel rekapitulasi hierarki anggaran dengan perbandingan antar tahapan.")
    
    # 1. AMBIL SEMUA DATA DENGAN PAGINATION (Tanpa Limit 1000 baris)
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
        df['kode_skpd'] = df['kode_skpd'].astype(str).str.strip()
        df['nama_skpd'] = df['nama_skpd'].astype(str).str.strip()
        df['tahun'] = df['tahun'].astype(str).str.strip()
        
        if 'tahun' not in df.columns:
            st.error("⚠️ Sistem mendeteksi kolom 'tahun' tidak ada di database.")
            st.stop()
            
        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Filter & Rekap")

        # 2. FILTER TAHUN
        list_tahun = sorted(df['tahun'].dropna().unique().tolist(), reverse=True)
        if not list_tahun:
            st.error("⚠️ Data tahun kosong.")
            st.stop()
            
        col_thn, col_skpd = st.columns(2)
        with col_thn:
            tahun_pilihan = st.selectbox("📅 Pilih Tahun Anggaran:", list_tahun)
        
        df_tahun = df[df['tahun'] == tahun_pilihan].copy()

        # 3. FILTER SKPD (Khusus Tahun Terpilih)
        # Menyatukan SOTK Lama & Baru untuk Dinas Pendidikan jika ada
        MAP_SKPD = {"1.01.2.22.0.00.16.0000": "1.01.0.00.0.00.16.0000"}
        df_tahun['kode_skpd'] = df_tahun['kode_skpd'].replace(MAP_SKPD)
        df_tahun.loc[df_tahun['kode_skpd'] == "1.01.0.00.0.00.16.0000", 'nama_skpd'] = "Dinas Pendidikan"

        list_skpd = sorted(df_tahun['nama_skpd'].dropna().unique().tolist())
        list_skpd = [x for x in list_skpd if x != ""]
        list_skpd.insert(0, "SEMUA SKPD")
        
        with col_skpd:
            skpd_pilihan = st.selectbox("🏢 Pilih SKPD:", list_skpd)

        # Isolasi DataFrame berdasarkan SKPD
        if skpd_pilihan != "SEMUA SKPD":
            df_proses = df_tahun[df_tahun['nama_skpd'] == skpd_pilihan].copy()
        else:
            df_proses = df_tahun.copy()

        if df_proses.empty:
            st.warning(f"⚠️ Tidak ada data untuk {skpd_pilihan} di tahun {tahun_pilihan}.")
            st.stop()

        # 4. FILTER TAHAPAN ACUAN (Berdasarkan SKPD & Tahun Terpilih)
        list_tahapan = df_proses['tahapan'].dropna().unique().tolist()
        
        if not list_tahapan:
            st.warning(f"⚠️ Belum ada data tahapan.")
            st.stop()
            
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            tahapan_acuan = st.selectbox("🎯 Tahapan Acuan (Sumber Dana):", list_tahapan, index=len(list_tahapan)-1)
        with col_t2:
            tahap_awal = st.selectbox("📉 Tahapan Awal (Selisih):", list_tahapan, index=0)
        with col_t3:
            tahap_akhir = st.selectbox("📈 Tahapan Akhir (Selisih):", list_tahapan, index=len(list_tahapan)-1)

        if st.button(f"🚀 PROSES & BUAT REKAP", type="primary", use_container_width=True):
            with st.spinner("Menyusun hierarki dan menghitung ulang pagu secara presisi..."):
                
                # PERTAHANAN: Buang Baris Subtotal dari Excel (Hanya hitung yang punya sub kegiatan)
                df_proses = df_proses[df_proses['kode_sub_kegiatan'].astype(str).str.strip() != ""]
                df_proses = df_proses[~df_proses['kode_sub_kegiatan'].astype(str).str.lower().isin(['none', 'nan'])]

                # 5. MEMBANGUN MEMORI KALKULASI (Mesin Hierarki yang Akurat)
                dict_pagu = defaultdict(float)
                dict_nama = {}
                dict_sd = defaultdict(lambda: defaultdict(float))

                tree_skpd = set()
                tree_urusan = defaultdict(set)
                tree_prog = defaultdict(set)
                tree_keg = defaultdict(set)
                tree_sub = defaultdict(set)

                for _, row in df_proses.iterrows():
                    k_skpd, n_skpd = str(row['kode_skpd']).strip(), str(row['nama_skpd']).strip()
                    k_urus, n_urus = str(row['kode_urusan']).strip(), str(row['nama_urusan']).strip()
                    k_prog, n_prog = str(row['kode_program']).strip(), str(row['nama_program']).strip()
                    k_keg, n_keg = str(row['kode_kegiatan']).strip(), str(row['nama_kegiatan']).strip()
                    k_sub, n_sub = str(row['kode_sub_kegiatan']).strip(), str(row['nama_sub_kegiatan']).strip()
                    sd = str(row['nama_sumber_dana']).strip()
                    pagu = float(row['pagu'] or 0)
                    thp = str(row['tahapan']).strip()

                    dict_nama[k_skpd] = n_skpd
                    dict_nama[k_urus] = n_urus
                    dict_nama[k_prog] = n_prog
                    dict_nama[k_keg] = n_keg
                    dict_nama[k_sub] = n_sub

                    tree_skpd.add(k_skpd)
                    tree_urusan[k_skpd].add(k_urus)
                    tree_prog[k_urus].add(k_prog)
                    tree_keg[k_prog].add(k_keg)
                    tree_sub[k_keg].add(k_sub)

                    # Akumulasi Pagu ke atas (Hierarki)
                    dict_pagu[f"{k_skpd}|{thp}"] += pagu
                    dict_pagu[f"{k_urus}|{thp}"] += pagu
                    dict_pagu[f"{k_prog}|{thp}"] += pagu
                    dict_pagu[f"{k_keg}|{thp}"] += pagu
                    dict_pagu[f"{k_sub}|{thp}"] += pagu

                    if thp == tahapan_acuan:
                        dict_sd[k_sub][sd] += pagu

                # 6. MENYUSUN BARIS DATA (FLAT TABLE)
                baris_rekap = []

                def format_rupiah(angka):
                    return f"Rp. {int(angka):,} \n".replace(',', '.')

                for sk_key in sorted(tree_skpd):
                    row_data = {"Kode": sk_key, "Uraian": dict_nama.get(sk_key, "-"), "Sumber Dana (Acuan)": "", "Level": 1}
                    for thp in list_tahapan:
                        row_data[thp] = dict_pagu[f"{sk_key}|{thp}"]
                    row_data["Selisih (Akhir - Awal)"] = dict_pagu[f"{sk_key}|{tahap_akhir}"] - dict_pagu[f"{sk_key}|{tahap_awal}"]
                    baris_rekap.append(row_data)

                    for u_key in sorted(tree_urusan[sk_key]):
                        row_data = {"Kode": u_key, "Uraian": dict_nama.get(u_key, "-"), "Sumber Dana (Acuan)": "", "Level": 2}
                        for thp in list_tahapan:
                            row_data[thp] = dict_pagu[f"{u_key}|{thp}"]
                        row_data["Selisih (Akhir - Awal)"] = dict_pagu[f"{u_key}|{tahap_akhir}"] - dict_pagu[f"{u_key}|{tahap_awal}"]
                        baris_rekap.append(row_data)

                        for p_key in sorted(tree_prog[u_key]):
                            row_data = {"Kode": p_key, "Uraian": dict_nama.get(p_key, "-"), "Sumber Dana (Acuan)": "", "Level": 3}
                            for thp in list_tahapan:
                                row_data[thp] = dict_pagu[f"{p_key}|{thp}"]
                            row_data["Selisih (Akhir - Awal)"] = dict_pagu[f"{p_key}|{tahap_akhir}"] - dict_pagu[f"{p_key}|{tahap_awal}"]
                            baris_rekap.append(row_data)

                            for k_key in sorted(tree_keg[p_key]):
                                row_data = {"Kode": k_key, "Uraian": dict_nama.get(k_key, "-"), "Sumber Dana (Acuan)": "", "Level": 4}
                                for thp in list_tahapan:
                                    row_data[thp] = dict_pagu[f"{k_key}|{thp}"]
                                row_data["Selisih (Akhir - Awal)"] = dict_pagu[f"{k_key}|{tahap_akhir}"] - dict_pagu[f"{k_key}|{tahap_awal}"]
                                baris_rekap.append(row_data)

                                for s_key in sorted(tree_sub[k_key]):
                                    str_sd = ""
                                    for sd_name, sd_val in dict_sd[s_key].items():
                                        if sd_val > 0:
                                            str_sd += f"{sd_name} = {format_rupiah(sd_val)}"
                                    str_sd = str_sd.strip()

                                    row_data = {"Kode": s_key, "Uraian": dict_nama.get(s_key, "-"), "Sumber Dana (Acuan)": str_sd, "Level": 5}
                                    for thp in list_tahapan:
                                        row_data[thp] = dict_pagu[f"{s_key}|{thp}"]
                                    row_data["Selisih (Akhir - Awal)"] = dict_pagu[f"{s_key}|{tahap_akhir}"] - dict_pagu[f"{s_key}|{tahap_awal}"]
                                    baris_rekap.append(row_data)

                # 7. RENDER KE DATAFRAME DAN STYLING
                df_hasil = pd.DataFrame(baris_rekap)
                
                def warna_baris(row):
                    lvl = row['Level']
                    if lvl == 1: return ['background-color: #ddebf7; font-weight: bold'] * len(row)
                    if lvl == 2: return ['background-color: #fff2cc; font-weight: bold'] * len(row)
                    if lvl == 3: return ['background-color: #fce4d6; font-weight: bold'] * len(row)
                    if lvl == 4: return ['background-color: #e2efda; font-weight: bold'] * len(row)
                    return ['background-color: white'] * len(row)

                df_tampil = df_hasil.drop(columns=['Level'])
                kolom_angka = list_tahapan + ['Selisih (Akhir - Awal)']
                format_dict = {col: "{:,.0f}" for col in kolom_angka}
                
                styled_df = df_tampil.style.apply(warna_baris, axis=1).format(format_dict).set_properties(subset=['Sumber Dana (Acuan)'], **{'white-space': 'pre-wrap'})
                
                st.success(f"✅ Rekapitulasi {skpd_pilihan} Tahun {tahun_pilihan} berhasil disusun!")
                st.dataframe(styled_df, use_container_width=True, height=600)

                # 8. FITUR EXPORT EXCEL
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_tampil.to_excel(writer, index=False, sheet_name=f'Rekap_{tahun_pilihan}')
                output_excel.seek(0)
                
                nama_file = "SEMUA_SKPD" if skpd_pilihan == "SEMUA SKPD" else "Dinas_Pendidikan"
                
                st.download_button(
                    label=f"📥 Download Hasil Rekap (Excel)",
                    data=output_excel,
                    file_name=f"Rekap_SIPD_{nama_file}_{tahun_pilihan}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )




