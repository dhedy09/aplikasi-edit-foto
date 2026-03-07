import streamlit as st
import requests
from PIL import Image, ImageFilter
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio Foto AI Ultra Pro", layout="centered")
st.title("🚀 Studio Foto AI Ultra (Powered by Remove.bg)")
st.write("Kualitas industri dengan fitur lengkap: Ganti Latar & Efek Bokeh!")

# API Key kamu
REMOVE_BG_API_KEY = "F6Thg63UMox3LeHkgqNwbnVy"

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

# --- UI TAB MENU ---
tab1, tab2 = st.tabs(["🎨 Ganti Latar", "💧 Efek Blur (Portrait)"])

# ==========================================
# TAB 1: GANTI LATAR (WARNA & PEMANDANGAN)
# ==========================================
with tab1:
    st.header("Hapus & Ganti Latar Belakang")
    file_tab1 = st.file_uploader("1. Unggah Foto Utama...", type=["jpg", "png", "jpeg"], key="u1")
    
    if file_tab1:
        img1 = Image.open(file_tab1).convert("RGBA")
        st.image(img1, caption="Foto Asli", width="stretch")
        
        st.markdown("---")
        bg_type = st.radio("2. Pilih Tipe Latar Baru:", ["Transparan", "Ganti Warna", "Gambar Pemandangan"], horizontal=True)
        
        # Logika Input berdasarkan pilihan
        selected_color = "#FFFFFF"
        bg_image_file = None
        
        if bg_type == "Ganti Warna":
            selected_color = st.color_picker("Pilih Warna Latar:", "#FF0000")
        elif bg_type == "Gambar Pemandangan":
            bg_image_file = st.file_uploader("Unggah Gambar Pemandangan...", type=["jpg", "png", "jpeg"], key="bg_img")
            
        if st.button("🪄 Proses Ganti Latar", type="primary", key="btn1"):
            with st.spinner("AI sedang memotong foto dengan kualitas Ultra..."):
                file_tab1.seek(0)
                result_bytes = remove_bg_api(file_tab1)
                
                if result_bytes:
                    fg = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                    final_img = fg
                    
                    if bg_type == "Ganti Warna":
                        bg = Image.new("RGBA", fg.size, selected_color)
                        bg.paste(fg, (0, 0), fg)
                        final_img = bg
                    elif bg_type == "Gambar Pemandangan" and bg_image_file:
                        bg_img = Image.open(bg_image_file).convert("RGBA")
                        bg_img = bg_img.resize(fg.size)
                        bg_img.paste(fg, (0, 0), fg)
                        final_img = bg_img
                        
                    st.success("Selesai! Hasil sangat rapi.")
                    st.image(final_img, caption="Hasil Akhir", width="stretch")
                    
                    # Download
                    buf = io.BytesIO()
                    final_img.save(buf, format="PNG")
                    st.download_button("📥 Download Hasil", data=buf.getvalue(), file_name="hasil_latar.png", mime="image/png")

# ==========================================
# TAB 2: EFEK BLUR (DSLR BOKEH)
# ==========================================
with tab2:
    st.header("Efek Kamera DSLR (Blur Latar)")
    file_tab2 = st.file_uploader("Unggah Foto...", type=["jpg", "png", "jpeg"], key="u2")
    
    if file_tab2:
        img2 = Image.open(file_tab2).convert("RGBA")
        st.image(img2, caption="Foto Asli", width="stretch")
        
        blur_amount = st.slider("Tingkat Keburaman (Blur)", min_value=1, max_value=20, value=7)
        
        if st.button("💧 Terapkan Efek Blur", type="primary", key="btn2"):
            with st.spinner("Menghasilkan efek bokeh profesional..."):
                # 1. Proses potong orang lewat API
                file_tab2.seek(0)
                result_bytes = remove_bg_api(file_tab2)
                
                if result_bytes:
                    fg2 = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                    
                    # 2. Buat background blur dari foto asli
                    bg_blurred = img2.filter(ImageFilter.GaussianBlur(blur_amount))
                    
                    # 3. Gabungkan
                    bg_blurred.paste(fg2, (0, 0), fg2)
                    
                    st.success("Selesai! Efek blur diaplikasikan.")
                    st.image(bg_blurred, caption="Hasil Blur Portrait", width="stretch")
                    
                    # Download
                    buf2 = io.BytesIO()
                    bg_blurred.save(buf2, format="PNG")
                    st.download_button("📥 Download Hasil Blur", data=buf2.getvalue(), file_name="hasil_blur.png", mime="image/png")
