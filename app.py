import streamlit as st
from rembg import remove
from PIL import Image
import io

# Konfigurasi Halaman Web
st.set_page_config(page_title="AI Background Editor v2", layout="centered")

st.title("📸 AI Background Editor v2")
st.write("Hapus latar belakang foto dan ganti dengan warna. Sekarang dengan peningkatan detail tepi!")

# Widget Unggah File
uploaded_file = st.file_uploader("Pilih foto...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGBA")
    
    st.markdown("---")
    st.subheader("Pengaturan Latar Belakang")
    
    bg_color = st.color_picker("Pilih warna latar belakang baru", "#FF0000")
    gunakan_warna = st.checkbox("Terapkan warna latar belakang ini?")

    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Original")
        st.image(image, use_container_width=True)

    with st.spinner('Sedang memproses AI... Tunggu sebentar karena AI bekerja lebih keras untuk detail tepi.'):
        # 1. Proses potong objek dengan parameter matting untuk detail tepi
        img_byte = io.BytesIO()
        image.save(img_byte, format='PNG')
        
        # Panggil fungsi remove dengan parameter matting
        # Menurunkan ambang batas latar belakang (alpha_matting_background_threshold) 
        # dan erode size untuk mencoba menyelamatkan lebih banyak detail.
        result_bytes = remove(
            img_byte.getvalue(),
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10, # Nilai rendah untuk menyelamatkan objek
            alpha_matting_erode_size=10,
            model='u2net' # Atau coba ganti ke 'u2netp' untuk kecepatan, atau 'isnet-general-use' untuk model yang berbeda
        )
        fg_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

        # 2. Proses ganti warna background (jika dicentang)
        if gunakan_warna:
            # Buat kanvas baru seukuran foto dengan warna pilihan user
            background = Image.new("RGBA", fg_image.size, bg_color)
            
            # Tempelkan foto objek di atas kanvas warna
            background.paste(fg_image, (0, 0), fg_image)
            
            # Gambar akhir adalah hasil gabungannya
            final_image = background
        else:
            final_image = fg_image

    with col2:
        st.header("Hasil (Peningkatan Tepi)")
        st.image(final_image, use_container_width=True)

    # Siapkan file untuk di-download
    buf = io.BytesIO()
    final_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    st.markdown("---")
    st.download_button(
        label="📥 Download Hasil (PNG)",
        data=byte_im,
        file_name="hasil_edit_foto.png",
        mime="image/png",
        use_container_width=True
    )
