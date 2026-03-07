import streamlit as st
import requests
from PIL import Image, ImageOps
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio Foto AI Ultra", layout="centered")

# --- SISTEM LOGIN (KATA SANDI) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terbatas")
    st.write("Aplikasi ini bersifat privat. Silakan masukkan kata sandi untuk melanjutkan.")
    
    password_input = st.text_input("Kata Sandi:", type="password")
    if st.button("Masuk"):
        # Cek kata sandi. Gunakan st.secrets["APP_PASSWORD"] jika di cloud, 
        # atau ganti langsung dengan string "sandi_anda" jika di lokal.
        if password_input == st.secrets["APP_PASSWORD"]: 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Kata sandi salah!")
    st.stop()

# ==========================================
# JIKA BERHASIL LOGIN, APLIKASI UTAMA JALAN
# ==========================================

# Ambil API Key dari Streamlit Secrets
REMOVE_BG_API_KEY = st.secrets["REMOVE_BG_API_KEY"]

# --- INISIALISASI SESSION STATE ---
if 'fg_image' not in st.session_state:
    st.session_state.fg_image = None
if 'last_uploaded_id' not in st.session_state:
    st.session_state.last_uploaded_id = None

def bersihkan_memori():
    st.session_state.fg_image = None
    st.session_state.last_uploaded_id = None

# --- FUNGSI FORMAT UKURAN FILE ---
def format_size(size_in_bytes):
    """Mengubah ukuran bytes menjadi KB atau MB agar mudah dibaca"""
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

# --- MENU NAVIGASI (SIDEBAR) ---
with st.sidebar:
    st.title("🧰 Menu Studio")
    pilihan_menu = st.radio("Pilih Fitur:", ["✂️ Hapus Latar (AI)", "🗜️ Kompresor Foto"])
    
    st.markdown("---")
    st.header("⚙️ Sistem & Memori")
    if st.button("🗑️ Bersihkan Memori", use_container_width=True, type="secondary"):
        bersihkan_memori()
        st.success("Memori RAM bersih! 🚀")
        
    if st.button("🚪 Keluar (Logout)", use_container_width=True):
        st.session_state.authenticated = False
        bersihkan_memori()
        st.rerun()

# ==========================================
# HALAMAN 1: HAPUS LATAR (AI)
# ==========================================
if pilihan_menu == "✂️ Hapus Latar (AI)":
    st.title("🚀 Hapus Latar Belakang AI")
    st.write("Powered by Remove.bg. Hasil potongan super bersih!")

    def remove_bg_api(image_file):
        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': image_file},
            data={'size': 'auto'},
            headers={'X-Api-Key': REMOVE_BG_API_KEY},
        )
        if response.status_code == requests.codes.ok:
            return response.content
        else:
            st.error(f"Terjadi kesalahan API: {response.status_code} - {response.text}")
            return None

    uploaded_file = st.file_uploader("Unggah foto utama...", type=["jpg", "png", "jpeg"], key="upload_bg")

    if uploaded_file:
        if st.session_state.last_uploaded_id != uploaded_file.file_id:
            bersihkan_memori()
            st.session_state.last_uploaded_id = uploaded_file.file_id

        img_original = Image.open(uploaded_file).convert("RGBA")
        st.image(img_original, caption="Foto Asli", use_container_width=True)
        
        bg_type = st.radio("Pilih Latar Belakang Baru:", ["Transparan", "Ganti Warna", "Gambar Pemandangan"], horizontal=True)
        selected_color = "#FFFFFF"
        bg_image_file = None
        
        if bg_type == "Ganti Warna":
            selected_color = st.color_picker("Pilih Warna Latar:", "#0071C5")
        elif bg_type == "Gambar Pemandangan":
            bg_image_file = st.file_uploader("Unggah Gambar Pemandangan...", type=["jpg", "png", "jpeg"])
            
        if st.button("🪄 Proses Foto Kualitas Ultra", type="primary"):
            if bg_type == "Gambar Pemandangan" and not bg_image_file:
                st.warning("⚠️ Harap unggah gambar pemandangan terlebih dahulu!")
            else:
                if st.session_state.fg_image is None:
                    with st.spinner("AI sedang memotong foto..."):
                        uploaded_file.seek(0)
                        result_bytes = remove_bg_api(uploaded_file)
                        if result_bytes:
                            st.session_state.fg_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                
                if st.session_state.fg_image:
                    fg = st.session_state.fg_image
                    final_img = fg.copy()
                    
                    with st.spinner("Menerapkan latar belakang..."):
                        if bg_type == "Ganti Warna":
                            bg = Image.new("RGBA", fg.size, selected_color)
                            bg.paste(fg, (0, 0), fg)
                            final_img = bg
                        elif bg_type == "Gambar Pemandangan" and bg_image_file:
                            bg_img = Image.open(bg_image_file).convert("RGBA")
                            bg_img = ImageOps.fit(bg_img, fg.size, method=Image.Resampling.LANCZOS)
                            bg_img.paste(fg, (0, 0), fg)
                            final_img = bg_img
                            
                    st.success("Selesai! Hasil editan siap diunduh.")
                    st.image(final_img, caption="Hasil Akhir", use_container_width=True)
                    
                    buf = io.BytesIO()
                    final_img.save(buf, format="PNG")
                    st.download_button("📥 Download Hasil HD", data=buf.getvalue(), file_name="hasil_edit_ultra.png", mime="image/png")

# ==========================================
# HALAMAN 2: KOMPRESOR FOTO
# ==========================================
elif pilihan_menu == "🗜️ Kompresor Foto":
    st.title("🗜️ Kompresor Foto Cerdas")
    st.write("Kecilkan ukuran file MB menjadi KB tanpa internet (100% Gratis Tanpa API).")

    compress_file = st.file_uploader("Unggah foto yang ingin dikecilkan ukurannya...", type=["jpg", "png", "jpeg"], key="upload_compress")

    if compress_file:
        # Hitung ukuran asli
        original_size = len(compress_file.getvalue())
        
        st.write(f"**Ukuran Asli:** {format_size(original_size)}")
        
        # Slider Kualitas
        st.write("---")
        kualitas = st.slider("Pilih Tingkat Kualitas (1-100):", min_value=1, max_value=100, value=70, step=1, 
                             help="Semakin kecil angkanya, ukuran file makin kecil tapi gambar mungkin sedikit buram.")
        
        if st.button("🗜️ Mulai Kompresi", type="primary"):
            with st.spinner("Mengecilkan ukuran..."):
                img = Image.open(compress_file)
                
                # Ubah ke RGB (wajib untuk format JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Proses Kompresi
                buf_compress = io.BytesIO()
                # Simpan sebagai JPEG untuk kompresi terbaik
                img.save(buf_compress, format="JPEG", quality=kualitas, optimize=True)
                compressed_size = len(buf_compress.getvalue())
                
                st.success("Kompresi Berhasil! 🎉")
                
                # Tampilkan perbandingan ukuran
                col1, col2 = st.columns(2)
                col1.metric("Ukuran Asli", format_size(original_size))
                col2.metric("Ukuran Baru", format_size(compressed_size), delta=f"-{format_size(original_size - compressed_size)}", delta_color="inverse")
                
                st.download_button(
                    label="📥 Download Foto Terkompresi",
                    data=buf_compress.getvalue(),
                    file_name="hasil_kompres.jpg",
                    mime="image/jpeg"
                )
