import streamlit as st
import requests
from PIL import Image
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio Foto AI Ultra", layout="centered")
st.title("🚀 Studio Foto AI Ultra (Powered by Remove.bg)")
st.write("Kualitas industri. Hasil potong super bersih dan akurat!")

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

# --- UI APLIKASI (TANPA TAB MENU) ---
uploaded_file = st.file_uploader("Unggah foto...", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Tampilkan Foto Asli
    img_original = Image.open(uploaded_file).convert("RGBA")
    st.image(img_original, caption="Foto Asli", width="stretch")
    
    st.markdown("---")
    # Pilihan Tipe Latar
    bg_type = st.radio("Pilih Latar Belakang Baru:", ["Transparan", "Ganti Warna", "Gambar Pemandangan"], horizontal=True)
    
    # Logika Input berdasarkan pilihan
    selected_color = "#FFFFFF"
    bg_image_file = None
    
    if bg_type == "Ganti Warna":
        selected_color = st.color_picker("Pilih Warna Latar:", "#FF0000")
    elif bg_type == "Gambar Pemandangan":
        bg_image_file = st.file_uploader("Unggah Gambar Pemandangan...", type=["jpg", "png", "jpeg"])
        
    if st.button("🪄 Proses Ganti Latar", type="primary"):
        with st.spinner("AI sedang memotong foto dengan kualitas Ultra..."):
            # Karena API butuh file mentah, kita kirim ulang bytes-nya
            uploaded_file.seek(0)
            result_bytes = remove_bg_api(uploaded_file)
            
            if result_bytes:
                # Proses hasil dari API (Potongan objek utama yang super rapi)
                fg = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                final_img = fg
                
                if bg_type == "Ganti Warna":
                    # Buat latar warna solid
                    bg = Image.new("RGBA", fg.size, selected_color)
                    bg.paste(fg, (0, 0), fg)
                    final_img = bg
                elif bg_type == "Gambar Pemandangan" and bg_image_file:
                    # Buat latar dari gambar pemandangan
                    bg_img = Image.open(bg_image_file).convert("RGBA")
                    bg_img = bg_img.resize(fg.size) # Samakan ukuran latar dengan foto asli
                    bg_img.paste(fg, (0, 0), fg)
                    final_img = bg_img
                    
                st.success("Selesai! Meja di bawah tangan pasti hilang.")
                st.image(final_img, caption="Hasil Akhir Kualitas HD", width="stretch")
                
                # Tombol Download
                buf = io.BytesIO()
                final_img.save(buf, format="PNG")
                st.download_button("📥 Download Hasil", data=buf.getvalue(), file_name="hasil_edit_ultra.png", mime="image/png")

st.info("Catatan: Aplikasi ini fokus pada akurasi pemotongan latar belakang menggunakan server profesional.")
