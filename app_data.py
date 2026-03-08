import streamlit as st
import openpyxl
import io
import re  # <--- Tambahan library untuk Regex (Pembersih Karakter)

# 1. Judul Halaman Khusus Data
st.set_page_config(page_title="Olah Data & SIPD", layout="wide")

# 2. Sistem Login (Sama seperti sebelumnya)
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
    
    # ==========================================
    # ALAT EXCEL (TAMBAH PETIK & BERSIHKAN DATA)
    # ==========================================
    st.write("Alat super untuk memanipulasi tanda petik (') dan membersihkan karakter aneh pada data Excel. Sangat ampuh untuk NIK Dapodik, NIP, atau Rekening SIPD.")
    
    with st.expander("📖 Buka Panduan Penggunaan", expanded=False):
        st.markdown("""
        **Cara Penggunaan:**
        1. Unggah file Excel (`.xlsx`) Anda.
        2. Ketik huruf kolom target. **Bisa lebih dari 1 kolom!** Pisahkan dengan koma (Contoh: `C, E, G`).
        3. Pilih mode Aksi (Tambah/Hapus).
        4. Centang **Pembersih Karakter Hantu** jika data Anda berasal dari Dapodik/SIPD yang susah dibersihkan.
        5. Klik Proses!
        """)
        
    st.markdown("---")
    
    file_excel = st.file_uploader("📥 Unggah File Excel (.xlsx)", type=["xlsx"], key="excel_upload")
    
    if file_excel:
        col1, col2 = st.columns(2)
        
        with col1:
            kolom_target = st.text_input("🔠 Ketik Huruf Kolom (Pisahkan dgn koma. Cth: C, F, H):").upper()
            # Tombol sakti untuk membersihkan data
            bersihkan_angka = st.checkbox("🧹 Bersihkan Karakter Hantu (Ekstrak Angkanya Saja)", 
                                          help="Gunakan ini untuk NIK/NIP Dapodik. Semua huruf, spasi tersembunyi, dan simbol akan dihapus permanen, hanya menyisakan angka murni.")
            
        with col2:
            mode_excel = st.radio("⚙️ Pilih Aksi Tanda Petik:", ["+ Tambah Petik Tersembunyi", "- Hapus Semua Petik"], horizontal=True)
            
        if st.button("🚀 PROSES FILE EXCEL", type="primary", use_container_width=True):
            if not kolom_target:
                st.error("⚠️ Mohon isi minimal 1 huruf kolom terlebih dahulu!")
            else:
                with st.spinner("Memproses ribuan baris data Excel..."):
                    try:
                        # Pecah teks kolom (Misal "C, F, H" menjadi list ['C', 'F', 'H'])
                        list_kolom = [k.strip() for k in kolom_target.split(",") if k.strip()]
                        
                        wb = openpyxl.load_workbook(file_excel)
                        ws = wb.active
                        
                        # Loop melalui setiap kolom yang diinput user
                        for col_letter in list_kolom:
                            for row in range(2, ws.max_row + 1):
                                cell = ws[f"{col_letter}{row}"]
                                
                                if cell.value is not None:
                                    val_str = str(cell.value).strip()
                                    
                                    # --- FITUR PEMBERSIH KARAKTER HANTU (REGEX) ---
                                    if bersihkan_angka:
                                        # Hapus semua yang BUKAN angka (\D)
                                        val_str = re.sub(r'\D', '', val_str)
                                    
                                    # --- LOGIKA PETIK ---
                                    if mode_excel == "+ Tambah Petik Tersembunyi":
                                        if val_str.startswith("'"):
                                            val_str = val_str[1:]
                                        cell.value = val_str
                                        cell.quotePrefix = True
                                        
                                    else: # Mode Hapus Petik
                                        val_str = val_str.replace("'", "")
                                        cell.value = val_str
                                        cell.quotePrefix = False 
                                        cell.number_format = '@' 

                        # Simpan hasil
                        output_excel = io.BytesIO()
                        wb.save(output_excel)
                        output_excel.seek(0)
                        
                        st.success(f"✅ Mantap! Berhasil memproses kolom: {', '.join(list_kolom)}")
                        
                        nama_file_baru = f"Selesai_{file_excel.name}"
                        
                        st.download_button(
                            label="📥 Download Hasil Excel",
                            data=output_excel,
                            file_name=nama_file_baru,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Terjadi kesalahan: {e}")
