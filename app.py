import streamlit as st
import requests
from PIL import Image
import io

# Konfigurasi Halaman
st.set_page_config(page_title="Studio Foto AI Ultra", layout="centered")
st.title("🚀 Studio Foto AI (Powered by Remove.bg)")
st.write("Kualitas industri. Meja dan detail rumit pasti hilang!")

# API Key kamu
REMOVE_BG_API_KEY = "F6Thg63UMox3LeHkgqNwbnVy"

def remove_bg_api(image_file):
    """Fungsi untuk memproses gambar lewat API remove.bg"""
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
uploaded_file = st.file_uploader("Unggah foto yang ingin dibersihkan...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Tampilkan Foto Asli
    img_original = Image.open(uploaded_file)
    st.image(img_original, caption="Foto Asli", width="stretch")
    
    # Pilihan Warna Latar
    st.markdown("---")
    bg_choice = st.radio("Pilih Latar Belakang Baru:", ["Transparan", "Warna Merah", "Warna Biru", "Pilih Warna Sendiri"], horizontal=True)
    
    custom_color = "#FF0000" # Default merah
    if bg_choice == "Warna Biru": custom_color = "#0000FF"
    elif bg_choice == "Pilih Warna Sendiri": custom_color = st.color_picker("Pilih Warna:", "#00FF00")

    if st.button("🪄 Bersihkan Foto Sekarang", type="primary"):
        with st.spinner("Menghubungi server remove.bg untuk hasil sempurna..."):
            # Karena API butuh file mentah, kita kirim ulang bytes-nya
            uploaded_file.seek(0)
            result_bytes = remove_bg_api(uploaded_file)
            
            if result_bytes:
                # Proses hasil dari API
                foreground = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                
                if bg_choice == "Transparan":
                    final_image = foreground
                else:
                    # Buat latar warna solid
                    background = Image.new("RGBA", foreground.size, custom_color)
                    background.paste(foreground, (0, 0), foreground)
                    final_image = background
                
                st.success("Selesai! Hasil jauh lebih rapi, kan?")
                st.image(final_image, caption="Hasil Kualitas Ultra", width="stretch")
                
                # Tombol Download
                buf = io.BytesIO()
                final_image.save(buf, format="PNG")
                st.download_button("📥 Download Hasil HD", data=buf.getvalue(), file_name="hasil_ultra.png", mime="image/png")

st.info("Info: Menggunakan API eksternal lebih akurat dalam membedakan warna baju dengan benda di sekitarnya.")
