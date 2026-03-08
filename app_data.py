import streamlit as st
import openpyxl
import io
import re

# 1. Judul Halaman Khusus Data
st.set_page_config(page_title="Olah Data & SIPD", layout="wide")

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

# 3. KONTEN APLIKASI UTAMA
if st.session_state.authenticated:
    st.title("📊 Mamayo Data Center")
    st.write("Pusat Pengolahan Data Excel dan SIPD")
    
    st.markdown("---")
    st.write("### 🛠️ Alat Excel: Manipulasi Petik & Pembersih Karakter")
    st.write("Gunakan alat ini untuk merapikan data Dapodik/SIPD dalam satu kali jalan.")
    
    file_excel = st.file_uploader("📥 Unggah File Excel (.xlsx)", type=["xlsx"], key="excel_upload")
    
    if file_excel:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 1️⃣ Pengaturan Tanda Petik")
            kolom_petik = st.text_input("🔠 Kolom untuk Tanda Petik (Cth: C, D):", help="Kosongkan jika tidak butuh").upper()
            mode_excel = st.radio("⚙️ Aksi:", ["+ Tambah Petik Tersembunyi", "- Hapus Semua Petik"], horizontal=True)
            
        with col2:
            st.markdown("#### 2️⃣ Pengaturan Pembersih Karakter")
            kolom_bersih = st.text_input("🧹 Kolom Ekstrak Angka (Cth: F, G):", help="Kosongkan jika tidak butuh. Akan menghapus semua huruf/simbol/spasi, murni sisa angka.").upper()
            
        st.info("💡 **Tips:** Anda bisa mengisi kedua kotak di atas sekaligus. Jika ada kolom yang butuh dibersihkan sekaligus diberi petik, ketik hurufnya di kedua kotak.")
            
        if st.button("🚀 PROSES FILE EXCEL", type="primary", use_container_width=True):
            # Cek apakah minimal ada satu kotak yang diisi
            if not kolom_petik and not kolom_bersih:
                st.error("⚠️ Mohon isi minimal salah satu kolom (Petik atau Pembersih)!")
            else:
                with st.spinner("Memproses data Excel Anda..."):
                    try:
                        # Pecah teks input menjadi list
                        list_petik = [k.strip() for k in kolom_petik.split(",") if k.strip()]
                        list_bersih = [k.strip() for k in kolom_bersih.split(",") if k.strip()]
                        
                        wb = openpyxl.load_workbook(file_excel)
                        ws = wb.active
                        
                        # TAHAP 1: EKSTRAK ANGKA (Pembersih Karakter Hantu)
                        if list_bersih:
                            for col in list_bersih:
                                for row in range(2, ws.max_row + 1):
                                    cell = ws[f"{col}{row}"]
                                    if cell.value is not None:
                                        val_str = str(cell.value).strip()
                                        # Libas semua yang bukan angka
                                        val_str = re.sub(r'\D', '', val_str)
                                        cell.value = val_str
                                        
                        # TAHAP 2: MANIPULASI TANDA PETIK
                        if list_petik:
                            for col in list_petik:
                                for row in range(2, ws.max_row + 1):
                                    cell = ws[f"{col}{row}"]
                                    if cell.value is not None:
                                        val_str = str(cell.value).strip()
                                        
                                        if mode_excel == "+ Tambah Petik Tersembunyi":
                                            if val_str.startswith("'"):
                                                val_str = val_str[1:]
                                            cell.value = val_str
                                            cell.quotePrefix = True
                                        else:
                                            val_str = val_str.replace("'", "")
                                            cell.value = val_str
                                            cell.quotePrefix = False 
                                            cell.number_format = '@'

                        # Simpan dan Siapkan Download
                        output_excel = io.BytesIO()
                        wb.save(output_excel)
                        output_excel.seek(0)
                        
                        st.success("✅ File berhasil diproses sesuai pengaturan Anda!")
                        
                        st.download_button(
                            label="📥 Download Hasil Excel",
                            data=output_excel,
                            file_name=f"Selesai_{file_excel.name}",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")
