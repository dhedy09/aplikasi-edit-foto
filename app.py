import streamlit as st
from rembg import remove
from PIL import Image, ImageFilter
import io

# Konfigurasi Halaman Web
st.set_page_config(page_title="Studio Foto AI Pro", layout="centered")
st.title("✨ Studio Foto AI Pro")
st.write("Aplikasi edit foto cerdas. Pilih menu di bawah ini!")

# --- MEMBUAT TAB MENU ---
tab1, tab2 = st.tabs(["🎨 Ganti Latar", "💧 Efek Blur (Portrait)"])

# ==========================================
# TAB 1: GANTI LATAR (WARNA & GAMBAR)
# ==========================================
with tab1:
    st.header("Hapus & Ganti Latar Belakang")
    file_tab1 = st.file_uploader("1. Unggah Foto Utama...", type=["jpg", "png", "jpeg"], key="file1")
    
    if file_tab1:
        img1 = Image.open(file_tab1)
        st.image(img1, caption="Foto Asli", use_container_width=True)
        
        st.markdown("---")
        # Pilihan Tipe Latar
        bg_type = st.radio("2. Pilih Tipe Latar Baru:", ["Transparan", "Warna Solid", "Gambar Pemandangan"], horizontal=True)
        
        bg_color = "#FFFFFF"
        bg_image_file = None
        
        # Logika memunculkan menu sesuai pilihan
        if bg_type == "Warna Solid":
            bg_color = st.color_picker("Pilih Warna:", "#FF0000")
        elif bg_type == "Gambar Pemandangan":
            bg_image_file = st.file_uploader("Unggah Gambar Pemandangan/Latar...", type=["jpg", "png", "jpeg"], key="bg_file")
        
        # Tombol Eksekusi
        if st.button("🪄 Proses Ganti Latar", type="primary"):
            with st.spinner("AI sedang bekerja..."):
                # Proses potong objek dengan AI Rembg
                img_byte = io.BytesIO()
                img1.save(img_byte, format='PNG')
                res_bytes = remove(img_byte.getvalue())
                fg = Image.open(io.BytesIO(res_bytes)).convert("RGBA")
                
                final_img1 = fg # Default jika memilih transparan
                
                if bg_type == "Warna Solid":
                    bg = Image.new("RGBA", fg.size, bg_color)
                    bg.paste(fg, (0, 0), fg)
                    final_img1 = bg
                elif bg_type == "Gambar Pemandangan" and bg_image_file is not None:
                    bg_img = Image.open(bg_image_file).convert("RGBA")
                    bg_img = bg_img.resize(fg.size) # Samakan ukuran latar dengan foto asli
                    bg_img.paste(fg, (0, 0), fg)
                    final_img1 = bg_img
                    
                st.success("Selesai!")
                st.image(final_img1, caption="Hasil Akhir", use_container_width=True)
                
                # Siapkan file untuk download
                buf1 = io.BytesIO()
                final_img1.save(buf1, format="PNG")
                st.download_button("📥 Download Hasil", data=buf1.getvalue(), file_name="hasil_latar.png", mime="image/png")

# ==========================================
# TAB 2: EFEK BLUR (BOKEH)
# ==========================================
with tab2:
    st.header("Efek Kamera DSLR (Blur Latar)")
    file_tab2 = st.file_uploader("Unggah Foto...", type=["jpg", "png", "jpeg"], key="file2")
    
    if file_tab2:
        img2 = Image.open(file_tab2).convert("RGBA")
        st.image(img2, caption="Foto Asli", use_container_width=True)
        
        # Slider untuk mengatur tingkat blur
        blur_amount = st.slider("Tingkat Keburaman (Blur)", min_value=1, max_value=20, value=7)
        
        if st.button("💧 Terapkan Efek Blur", type="primary"):
            with st.spinner("Menerapkan efek lensa DSLR..."):
                # 1. Buat versi foto yang diblur seluruhnya
                bg_blurred = img2.filter(ImageFilter.GaussianBlur(blur_amount))
                
                # 2. Potong objek utamanya saja menggunakan AI Rembg
                img_byte2 = io.BytesIO()
                img2.save(img_byte2, format='PNG')
                res_bytes2 = remove(img_byte2.getvalue())
                fg2 = Image.open(io.BytesIO(res_bytes2)).convert("RGBA")
                
                # 3. Tempel objek utama (yang tajam) di atas foto yang diblur
                bg_blurred.paste(fg2, (0, 0), fg2)
                
                st.success("Selesai!")
                st.image(bg_blurred, caption="Hasil Blur", use_container_width=True)
                
                buf2 = io.BytesIO()
                bg_blurred.save(buf2, format="PNG")
                st.download_button("📥 Download Hasil Blur", data=buf2.getvalue(), file_name="hasil_blur.png", mime="image/png")
