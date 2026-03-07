import streamlit as st
from rembg import remove, new_session
from PIL import Image, ImageFilter
import io

# Konfigurasi Halaman Web
st.set_page_config(page_title="Studio Foto AI Pro", layout="centered")
st.title("✨ Studio Foto AI Pro (Portrait Edition)")
st.write("Menggunakan AI Spesialis Manusia. Telinga & tangan lebih presisi!")

# Memuat AI Khusus Manusia (Aman untuk RAM Streamlit)
@st.cache_resource
def get_human_model():
    # Model ini dilatih khusus untuk anatomi manusia
    return new_session("u2net_human_seg")

# Fungsi pembantu untuk memproses gambar
def process_remove_bg(image_input):
    img_byte = io.BytesIO()
    image_input.save(img_byte, format='PNG')
    
    # Mematikan alpha_matting agar tidak bocor warna merah, 
    # dan menggunakan model spesialis manusia
    res_bytes = remove(
        img_byte.getvalue(),
        session=get_human_model(),
        alpha_matting=False 
    )
    return Image.open(io.BytesIO(res_bytes)).convert("RGBA")

# --- MEMBUAT TAB MENU ---
tab1, tab2 = st.tabs(["🎨 Ganti Latar", "💧 Efek Blur (Portrait)"])

# ==========================================
# TAB 1: GANTI LATAR (WARNA & GAMBAR)
# ==========================================
with tab1:
    st.header("Hapus & Ganti Latar Belakang")
    file_tab1 = st.file_uploader("1. Unggah Foto Utama...", type=["jpg", "png", "jpeg"], key="file1")
    
    if file_tab1:
        img1 = Image.open(file_tab1).convert("RGBA")
        st.image(img1, caption="Foto Asli", width="stretch")
        
        st.markdown("---")
        bg_type = st.radio("2. Pilih Tipe Latar Baru:", ["Transparan", "Warna Solid", "Gambar Pemandangan"], horizontal=True)
        
        bg_color = "#FFFFFF"
        bg_image_file = None
        
        if bg_type == "Warna Solid":
            bg_color = st.color_picker("Pilih Warna:", "#FF0000")
        elif bg_type == "Gambar Pemandangan":
            bg_image_file = st.file_uploader("Unggah Gambar Pemandangan/Latar...", type=["jpg", "png", "jpeg"], key="bg_file")
        
        if st.button("🪄 Proses Ganti Latar", type="primary"):
            with st.spinner("AI Spesialis Manusia sedang bekerja..."):
                fg = process_remove_bg(img1)
                
                final_img1 = fg # Default Transparan
                
                if bg_type == "Warna Solid":
                    bg = Image.new("RGBA", fg.size, bg_color)
                    bg.paste(fg, (0, 0), fg)
                    final_img1 = bg
                elif bg_type == "Gambar Pemandangan" and bg_image_file is not None:
                    bg_img = Image.open(bg_image_file).convert("RGBA")
                    bg_img = bg_img.resize(fg.size)
                    bg_img.paste(fg, (0, 0), fg)
                    final_img1 = bg_img
                    
                st.success("Selesai!")
                st.image(final_img1, caption="Hasil Akhir (Telinga Lebih Tajam)", width="stretch")
                
                buf1 = io.BytesIO()
                final_img1.save(buf1, format="PNG")
                st.download_button("📥 Download Hasil", data=buf1.getvalue(), file_name="hasil_edit_portrait.png", mime="image/png")

# ==========================================
# TAB 2: EFEK BLUR (BOKEH)
# ==========================================
with tab2:
    st.header("Efek Kamera DSLR (Blur Latar)")
    file_tab2 = st.file_uploader("Unggah Foto...", type=["jpg", "png", "jpeg"], key="file2")
    
    if file_tab2:
        img2 = Image.open(file_tab2).convert("RGBA")
        st.image(img2, caption="Foto Asli", width="stretch")
        
        blur_amount = st.slider("Tingkat Keburaman (Blur)", min_value=1, max_value=20, value=7)
        
        if st.button("💧 Terapkan Efek Blur", type="primary"):
            with st.spinner("Menerapkan efek lensa DSLR..."):
                bg_blurred = img2.filter(ImageFilter.GaussianBlur(blur_amount))
                fg2 = process_remove_bg(img2)
                bg_blurred.paste(fg2, (0, 0), fg2)
                
                st.success("Selesai!")
                st.image(bg_blurred, caption="Hasil Blur", width="stretch")
                
                buf2 = io.BytesIO()
                bg_blurred.save(buf2, format="PNG")
                st.download_button("📥 Download Hasil Blur", data=buf2.getvalue(), file_name="hasil_blur.png", mime="image/png")
