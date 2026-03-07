import streamlit as st
import requests
from PIL import Image, ImageOps
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio Foto AI Ultra", layout="centered")
st.title("🚀 Studio Foto AI Ultra")
st.write("Powered by Remove.bg. Kualitas industri, hasil potongan super bersih!")

# Ambil API Key dari Streamlit Secrets
REMOVE_BG_API_KEY = st.secrets["REMOVE_BG_API_KEY"]

# --- INISIALISASI SESSION STATE ---
# Ini penting untuk menyimpan gambar sementara agar tidak buang-buang kuota API
if 'fg_image' not in st.session_state:
    st.session_state.fg_image = None
if 'last_uploaded_id' not in st.session_state:
    st.session_state.last_uploaded_id = None

# --- FUNGSI INTI ---
def remove_bg_api(image_file):
    """Fungsi untuk memanggil API remove.bg"""
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

# --- UI APLIKASI ---
uploaded_file = st.file_uploader("Unggah foto utama...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Cek apakah pengguna mengunggah foto baru. Jika ya, reset memori AI.
    if st.session_state.last_uploaded_id != uploaded_file.file_id:
        st.session_state.fg_image = None
        st.session_state.last_uploaded_id = uploaded_file.file_id

    # Tampilkan Foto Asli
    img_original = Image.open(uploaded_file).convert("RGBA")
    st.image(img_original, caption="Foto Asli", use_container_width=True)
    
    st.markdown("---")
    
    # Pilihan Tipe Latar
    bg_type = st.radio("Pilih Latar Belakang Baru:", ["Transparan", "Ganti Warna", "Gambar Pemandangan"], horizontal=True)
    
    selected_color = "#FFFFFF"
    bg_image_file = None
    
    # Logika Input berdasarkan pilihan
    if bg_type == "Ganti Warna":
        selected_color = st.color_picker("Pilih Warna Latar:", "#0071C5")
    elif bg_type == "Gambar Pemandangan":
        bg_image_file = st.file_uploader("Unggah Gambar Pemandangan...", type=["jpg", "png", "jpeg"])
        
    if st.button("🪄 Proses Foto Kualitas Ultra", type="primary"):
        # Validasi: Jika pilih pemandangan tapi lupa upload
        if bg_type == "Gambar Pemandangan" and not bg_image_file:
            st.warning("⚠️ Harap unggah gambar pemandangan terlebih dahulu sebelum memproses!")
        else:
            # LANGKAH 1: Potong Latar (Hanya panggil API jika belum ada di memori)
            if st.session_state.fg_image is None:
                with st.spinner("AI sedang memotong foto dengan akurasi piksel..."):
                    uploaded_file.seek(0)
                    result_bytes = remove_bg_api(uploaded_file)
                    
                    if result_bytes:
                        # Simpan hasil potong ke memori aplikasi
                        st.session_state.fg_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
            
            # LANGKAH 2: Terapkan Latar Belakang Baru
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
                        # Gunakan ImageOps.fit agar gambar pemandangan proporsional (tidak gepeng)
                        bg_img = ImageOps.fit(bg_img, fg.size, method=Image.Resampling.LANCZOS)
                        bg_img.paste(fg, (0, 0), fg)
                        final_img = bg_img
                        
                st.success("Selesai! Hasil editan siap diunduh.")
                st.image(final_img, caption="Hasil Akhir Kualitas HD", use_container_width=True)
                
                # Tombol Download
                buf = io.BytesIO()
                final_img.save(buf, format="PNG")
                st.download_button("📥 Download Hasil HD", data=buf.getvalue(), file_name="hasil_edit_ultra.png", mime="image/png")

st.info("💡 **Catatan Pintar:** AI hanya akan memotong foto satu kali. Jika Anda ingin mengganti-ganti warna latar setelahnya, kuota API Anda tidak akan terpotong lagi.")
