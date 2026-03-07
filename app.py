import streamlit as st
from rembg import remove
from PIL import Image
import io

st.set_page_config(page_title="AI Background Editor", layout="centered")

st.title("📸 AI Background Editor")
st.write("Hapus latar belakang foto dan ganti dengan warna kesukaanmu!")

# Widget Unggah File
uploaded_file = st.file_uploader("Pilih foto...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    st.markdown("---")
    st.subheader("Pengaturan Latar Belakang")
    
    # Memilih warna (Default diset ke Merah)
    bg_color = st.color_picker("Pilih warna latar belakang baru", "#FF0000")
    
    # Checkbox untuk mengaktifkan warna latar (kalau tidak dicentang, tetap transparan)
    gunakan_warna = st.checkbox("Terapkan warna latar belakang ini?")

    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Original")
        st.image(image, use_container_width=True)

    with st.spinner('Sedang memproses AI...'):
        # 1. Proses penghapusan background
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        
        result_bytes = remove(img_byte_arr.getvalue())
        # Pastikan gambar hasil rembg berformat RGBA (memiliki channel Alpha/Transparan)
        result_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

        # 2. Proses ganti warna background (jika dicentang)
        if gunakan_warna:
            # Buat kanvas baru seukuran foto dengan warna pilihan user
            background = Image.new("RGBA", result_image.size, bg_color)
            
            # Tempelkan foto objek di atas kanvas warna (menggunakan transparansi foto sbg mask)
            background.paste(result_image, (0, 0), result_image)
            
            # Gambar akhir adalah hasil gabungannya
            final_image = background
        else:
            # Jika tidak dicentang, biarkan transparan
            final_image = result_image

    with col2:
        st.header("Hasil")
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
