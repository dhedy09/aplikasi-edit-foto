import streamlit as st
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from datetime import datetime
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio AI Ultra", layout="centered", page_icon="✨")

# --- SISTEM LOGIN (KATA SANDI) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terbatas")
    st.write("Aplikasi ini bersifat privat. Silakan masukkan kata sandi untuk melanjutkan.")
    
    password_input = st.text_input("Kata Sandi:", type="password")
    if st.button("Masuk"):
        if password_input == st.secrets["APP_PASSWORD"]: 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Kata sandi salah!")
    st.stop()

# ==========================================
# JIKA BERHASIL LOGIN, APLIKASI UTAMA JALAN
# ==========================================

REMOVE_BG_API_KEY = st.secrets["REMOVE_BG_API_KEY"]

if 'fg_image' not in st.session_state:
    st.session_state.fg_image = None
if 'last_uploaded_id' not in st.session_state:
    st.session_state.last_uploaded_id = None

def bersihkan_memori():
    st.session_state.fg_image = None
    st.session_state.last_uploaded_id = None

def format_size(size_in_bytes):
    """Mengubah ukuran bytes menjadi KB atau MB"""
    if size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

# --- SIDEBAR: PENGATURAN MINIMALIS ---
with st.sidebar:
    st.caption("🔧 Pengaturan Sistem")
    if st.button("🗑️ Bersihkan Memori RAM", use_container_width=True):
        bersihkan_memori()
        st.success("RAM bersih! 🚀")
        
    if st.button("🚪 Keluar (Logout)", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        bersihkan_memori()
        st.rerun()

# --- NAVIGASI MODERN (TABS) ---
st.title("✨ Studio Multatuli AI")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["✂️ Hapus Latar", "🗜️ Kompres", "🎨 Warna", "🔄 Format", "📍 Teks & Waktu"])

# ==========================================
# TAB 1: HAPUS LATAR (AI)
# ==========================================
with tab1:
    st.write("Kualitas industri, potongan super rapi dengan tenaga AI.")

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
            st.error(f"Error API: {response.status_code} - {response.text}")
            return None

    uploaded_file = st.file_uploader("Unggah foto...", type=["jpg", "png", "jpeg"], key="upload_bg")

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
            bg_image_file = st.file_uploader("Unggah Pemandangan...", type=["jpg", "png", "jpeg"])
            
        if st.button("🪄 Proses Kualitas Ultra", type="primary"):
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
                            
                    st.success("Selesai!")
                    st.image(final_img, caption="Hasil Akhir", use_container_width=True)
                    
                    buf = io.BytesIO()
                    final_img.save(buf, format="PNG")
                    st.download_button("📥 Download Hasil HD", data=buf.getvalue(), file_name="hapus_latar_hd.png", mime="image/png")

# ==========================================
# TAB 2: KOMPRESOR FOTO (REAL-TIME)
# ==========================================
with tab2:
    st.write("Kecilkan ukuran file secara *real-time* tanpa mengurangi kualitas secara drastis.")

    compress_file = st.file_uploader("Unggah foto yang ingin dikompres...", type=["jpg", "png", "jpeg"], key="upload_compress")

    if compress_file:
        original_size = len(compress_file.getvalue())
        img = Image.open(compress_file)
        
        # Konversi ke RGB agar bisa disimpan sebagai JPEG yang ringan
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        st.markdown("---")
        st.write("🎚️ **Geser slider di bawah ini untuk melihat perubahan ukuran secara instan!**")
        
        # Slider yang memicu perubahan real-time
        kualitas = st.slider(
            "Tingkat Kualitas Gambar", 
            min_value=1, max_value=100, value=75, step=1
        )
        
        # PROSES OTOMATIS TANPA TOMBOL
        buf_compress = io.BytesIO()
        img.save(buf_compress, format="JPEG", quality=kualitas, optimize=True)
        compressed_size = len(buf_compress.getvalue())
        
        # Tampilkan Metrik Real-Time
        col1, col2 = st.columns(2)
        col1.metric("📦 Ukuran Asli", format_size(original_size))
        
        # Beri warna merah jika hasil kompresi ternyata lebih besar (jarang terjadi, tapi mungkin jika kualitas 100)
        delta_val = original_size - compressed_size
        delta_color = "normal" if delta_val > 0 else "inverse"
        col2.metric("⚡ Ukuran Baru", format_size(compressed_size), delta=f"{format_size(abs(delta_val))} {'lebih kecil' if delta_val > 0 else 'lebih besar'}", delta_color=delta_color)
        
        st.download_button(
            label="📥 Download Foto Terkompresi",
            data=buf_compress.getvalue(),
            file_name=f"kompres_{kualitas}.jpg",
            mime="image/jpeg",
            type="primary",
            use_container_width=True
        )

# ==========================================
# TAB 3: EDITOR WARNA & CAHAYA
# ==========================================
with tab3:
    st.write("Sesuaikan kecerahan, kontras, dan saturasi foto Anda secara *real-time*!")

    enhance_file = st.file_uploader("Unggah foto untuk diedit warnanya...", type=["jpg", "png", "jpeg"], key="upload_enhance")

    if enhance_file:
        img_asli = Image.open(enhance_file)

        # --- Mulai dari sini, semuanya masuk ke dalam 'if enhance_file:' ---

        # Inisialisasi nilai memori awal jika belum ada
        if "kecerahan" not in st.session_state:
            st.session_state.kecerahan = 1.0
            st.session_state.kontras = 1.0
            st.session_state.saturasi = 1.0
        
        # Fungsi untuk mereset memori warna
        def reset_warna():
            st.session_state.kecerahan = 1.0
            st.session_state.kontras = 1.0
            st.session_state.saturasi = 1.0
        
        # Tombol Reset
        st.button("🔄 Reset ke Semula", on_click=reset_warna)
        
        # Buat 3 kolom untuk slider agar rapi menyamping
        col_b, col_c, col_s = st.columns(3)
        with col_b:
            kecerahan = st.slider("☀️ Kecerahan", min_value=0.5, max_value=2.0, step=0.1, key="kecerahan")
        with col_c:
            kontras = st.slider("🌗 Kontras", min_value=0.5, max_value=2.0, step=0.1, key="kontras")
        with col_s:
            saturasi = st.slider("🌈 Saturasi (Warna)", min_value=0.0, max_value=2.0, step=0.1, key="saturasi")

        # --- Bagian di bawah ini sejajar kembali dengan col_b, col_c, col_s ---
        
        # Proses Edit Instan
        img_edit = ImageEnhance.Brightness(img_asli).enhance(kecerahan)
        img_edit = ImageEnhance.Contrast(img_edit).enhance(kontras)
        img_edit = ImageEnhance.Color(img_edit).enhance(saturasi)

        st.markdown("---")
        # Tampilkan Hasil Edit
        st.image(img_edit, caption="✨ Hasil Editan Langsung", use_container_width=True)

        # Tombol Download
        buf_edit = io.BytesIO()
        img_edit.save(buf_edit, format="PNG")
        st.download_button(
            label="📥 Download Hasil Edit",
            data=buf_edit.getvalue(),
            file_name="hasil_edit_warna.png",
            mime="image/png",
            type="primary",
            use_container_width=True
        )

# ==========================================
# TAB 4: KONVERTER FORMAT (UBAH KE JPG/PNG/WEBP)
# ==========================================
with tab4:
    st.write("Ubah format foto Anda ke resolusi atau ekstensi lain dengan mudah.")
    
    convert_file = st.file_uploader("Unggah foto yang akan diubah formatnya...", type=["jpg", "png", "jpeg", "webp"], key="upload_convert")
    
    if convert_file:
        img_konversi = Image.open(convert_file)
        st.image(img_konversi, caption="Foto Asli", use_container_width=True)
        
        st.markdown("---")
        format_tujuan = st.selectbox("Pilih Format Hasil Akhir:", ["PNG", "JPEG", "WEBP"])
        
        if st.button(f"🔄 Ubah ke {format_tujuan}", type="primary", use_container_width=True):
            with st.spinner(f"Mengubah ke {format_tujuan}..."):
                # Jika ingin simpan ke JPEG tapi foto aslinya PNG (punya transparansi), ubah mode warnanya dulu
                if format_tujuan == "JPEG" and img_konversi.mode in ("RGBA", "P"):
                    img_konversi = img_konversi.convert("RGB")
                    
                buf_konversi = io.BytesIO()
                img_konversi.save(buf_konversi, format=format_tujuan)
                
                st.success(f"Berhasil diubah ke {format_tujuan}!")
                
                # Ekstensi file otomatis menyesuaikan pilihan
                ekstensi = format_tujuan.lower()
                st.download_button(
                    label=f"📥 Download File .{ekstensi}",
                    data=buf_konversi.getvalue(),
                    file_name=f"hasil_konversi.{ekstensi}",
                    mime=f"image/{ekstensi}",
                    type="primary"
                )

# ==========================================
# TAB 5: STEMPEL ESTETIK (TEKS, LOKASI & WAKTU)
# ==========================================
with tab5:
    st.write("Tambahkan cap lokasi, momen, dan waktu ala Instagram Story.")
    
    watermark_file = st.file_uploader("Unggah foto...", type=["jpg", "png", "jpeg"], key="upload_watermark")
    
    if watermark_file:
        img_wm = Image.open(watermark_file).convert("RGBA") # Wajib RGBA untuk efek transparan
        
        # --- Pengaturan Pengguna ---
        col_teks, col_pos = st.columns(2)
        with col_teks:
            teks_lokasi = st.text_input("📍 Ketik Lokasi / Momen:", "Bandar Lampung, Indonesia")
            tambah_waktu = st.checkbox("🕰️ Tambahkan Waktu Saat Ini?", value=True)
        with col_pos:
            posisi = st.selectbox("Letak Stempel:", ["Kanan Bawah", "Kiri Bawah", "Kiri Atas", "Kanan Atas"])
            
        if st.button("🪄 Pasang Stempel", type="primary", use_container_width=True):
            with st.spinner("Menulis di atas foto..."):
                # Siapkan Teks Akhir
                teks_akhir = teks_lokasi
                if tambah_waktu:
                    waktu_sekarang = datetime.now().strftime("%d %b %Y - %H:%M")
                    teks_akhir = f"{teks_lokasi}\n{waktu_sekarang}" if teks_lokasi else waktu_sekarang
                
                # Buat layer transparan kosong seukuran foto asli
                txt_layer = Image.new("RGBA", img_wm.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(txt_layer)
                
                # Ukuran font dinamis (menyesuaikan besar foto)
                ukuran_font = max(int(img_wm.width * 0.03), 15)
                
                # Coba pakai Roboto jika ada di folder, jika tidak pakai font bawaan
                try:
                    font = ImageFont.truetype("Roboto-Regular.ttf", ukuran_font)
                except IOError:
                    font = ImageFont.load_default()
                    
                # Hitung ukuran kotak teks
                bbox = draw.multiline_textbbox((0, 0), teks_akhir, font=font)
                teks_lebar = bbox[2] - bbox[0]
                teks_tinggi = bbox[3] - bbox[1]
                
                # Margin & Padding (Jarak teks ke tepi kotak)
                padding = 20
                margin = 30
                
                # Tentukan Koordinat X dan Y berdasarkan pilihan posisi
                if posisi == "Kiri Atas":
                    x, y = margin, margin
                elif posisi == "Kanan Atas":
                    x, y = img_wm.width - teks_lebar - margin - (padding*2), margin
                elif posisi == "Kiri Bawah":
                    x, y = margin, img_wm.height - teks_tinggi - margin - (padding*2)
                else: # Kanan Bawah (Default)
                    x, y = img_wm.width - teks_lebar - margin - (padding*2), img_wm.height - teks_tinggi - margin - (padding*2)
                
                # Gambar Kotak Hitam Semi-Transparan (Alpha 120 dari 255)
                kotak_bg = [x, y, x + teks_lebar + (padding*2), y + teks_tinggi + (padding*2)]
                draw.rectangle(kotak_bg, fill=(0, 0, 0, 120))
                
                # Tulis Teks Berwarna Putih di atas kotak
                draw.multiline_text((x + padding, y + padding), teks_akhir, font=font, fill=(255, 255, 255, 255))
                
                # Gabungkan foto asli dengan layer teks
                hasil_akhir = Image.alpha_composite(img_wm, txt_layer)
                hasil_akhir = hasil_akhir.convert("RGB") # Kembalikan ke RGB agar bisa di-download sbg JPG
                
                st.markdown("---")
                st.image(hasil_akhir, caption="✨ Hasil Stempel Estetik", use_container_width=True)
                
                # Tombol Download
                buf_wm = io.BytesIO()
                hasil_akhir.save(buf_wm, format="JPEG", quality=95)
                st.download_button(
                    label="📥 Download Foto",
                    data=buf_wm.getvalue(),
                    file_name="foto_stempel.jpg",
                    mime="image/jpeg",
                    type="primary"
                )

