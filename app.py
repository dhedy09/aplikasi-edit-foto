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
uploaded_file = st.file_uploader("Unggah foto...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    img_original = Image.open(uploaded_file)
    st.image(img_original, caption="Foto Asli", width="stretch")
    
    st.markdown("---")
    # BAGIAN YANG DIUBAH: Pilihan dibuat simpel
    bg_choice = st.radio("Pilih Latar Belakang:", ["Transparan", "Ganti Warna"], horizontal=True)
    
    selected_color = "#FFFFFF" # Default Putih
    if bg_choice == "Ganti Warna":
        # Color picker akan muncul jika user memilih "Ganti Warna"
        selected_color = st.color_picker("Pilih Warna Latar:", "#FF0000")

    if st.button("🪄 Bersihkan Foto Sekarang", type="primary"):
        with st.spinner("Proses penghapusan latar oleh AI..."):
            uploaded_file.seek(0)
            result_bytes = remove_bg_api(uploaded_file)
            
            if result_bytes:
                foreground = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                
                if bg_choice == "Transparan":
                    final_image = foreground
                else:
                    # Logika pewarnaan yang lebih bersih
                    background = Image.new("RGBA", foreground.size, selected_color)
                    background.paste(foreground, (0, 0), foreground)
                    final_image = background
                
                st.success("Selesai!")
                st.image(final_image, caption="Hasil Akhir", width="stretch")
                
                buf = io.BytesIO()
                final_image.save(buf, format="PNG")
                st.download_button("📥 Download Hasil", data=buf.getvalue(), file_name="hasil_clean.png", mime="image/png")
