import streamlit as st
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from datetime import datetime
from geopy.geocoders import Nominatim
import io

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Studio AI Ultra", layout="centered", page_icon="✨")

# --- SISTEM LOGIN (KATA SANDI) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Akses Terbatas")
    st.write("Aplikasi ini bersifat privat. Silakan masukkan kata sandi untuk melanjutkan.")
    
    # Membungkus input dan tombol ke dalam st.form agar bisa pakai 'Enter'
    with st.form("login_form"):
        password_input = st.text_input("Kata Sandi:", type="password")
        
        # st.button diganti menjadi st.form_submit_button
        tombol_masuk = st.form_submit_button("Masuk")
        
        if tombol_masuk:
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
st.title("✨ STUDIO FOTO MAMAYO")
# tab1, tab2, tab3, tab4, tab5 = st.tabs(["✂️ Hapus Latar", "🗜️ Kompres", "🎨 Warna", "🔄 Format", "🪄 Filter"])
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["✂️ Latar", "🗜️ Kompres", "🎨 Warna", "🔄 Format", "🪄 Filter", "🖨️ Cetak Foto"])

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
# TAB 5: FILTER ESTETIK ALA INSTAGRAM
# ==========================================
with tab5:
    st.write("Berikan sentuhan artistik pada foto Anda dengan satu klik!")
    
    filter_file = st.file_uploader("Unggah foto untuk diberi filter...", type=["jpg", "png", "jpeg"], key="upload_filter")
    
    if filter_file:
        img_asli_filter = Image.open(filter_file)
        
        # Pilihan Filter menggunakan Dropdown
        pilihan_filter = st.selectbox(
            "Pilih Efek Visual:", 
            ["Pilih Filter...", "⚫⚪ Hitam Putih (Grayscale)", "💧 Blur Halus", "✏️ Sketsa (Contour)", "🔍 Tajamkan Detail", "🌌 Tepi Menyala (Edge Enhance)"]
        )
        
        if pilihan_filter != "Pilih Filter...":
            with st.spinner(f"Menerapkan {pilihan_filter}..."):
                # Proses penerapan filter
                if pilihan_filter == "⚫⚪ Hitam Putih (Grayscale)":
                    img_hasil = ImageOps.grayscale(img_asli_filter)
                elif pilihan_filter == "💧 Blur Halus":
                    img_hasil = img_asli_filter.filter(ImageFilter.GaussianBlur(radius=5))
                elif pilihan_filter == "✏️ Sketsa (Contour)":
                    img_hasil = img_asli_filter.filter(ImageFilter.CONTOUR)
                elif pilihan_filter == "🔍 Tajamkan Detail":
                    img_hasil = img_asli_filter.filter(ImageFilter.DETAIL)
                elif pilihan_filter == "🌌 Tepi Menyala (Edge Enhance)":
                    img_hasil = img_asli_filter.filter(ImageFilter.EDGE_ENHANCE_MORE)
                
                st.markdown("---")
                st.image(img_hasil, caption=f"✨ Hasil: {pilihan_filter}", use_container_width=True)
                
                # Menyiapkan file untuk didownload
                buf_filter = io.BytesIO()
                
                # Konversi format jika filternya membuang warna (misal: grayscale)
                if img_hasil.mode in ("L", "P", "RGBA"):
                    img_hasil = img_hasil.convert("RGB")
                    
                img_hasil.save(buf_filter, format="JPEG", quality=95)
                    
                st.download_button(
                    label="📥 Download Foto Estetik",
                    data=buf_filter.getvalue(),
                    file_name="hasil_filter.jpg",
                    mime="image/jpeg",
                    type="primary",
                    use_container_width=True
                )

# ==========================================
# TAB 6: STUDIO CETAK FOTO (MIX & MATCH)
# ==========================================
with tab6:
    st.write("Cetak pasfoto dan ukuran studio (R) presisi tinggi. Hasil akhir berupa PDF siap print (Kertas A4).")
    
    cetak_file = st.file_uploader("Unggah foto yang akan dicetak...", type=["jpg", "png", "jpeg"], key="upload_cetak")
    
    if cetak_file:
        img_cetak = Image.open(cetak_file).convert("RGB")
        st.image(img_cetak, caption="Foto Asli", width=250)
        
        st.markdown("### 🎛️ Atur Jumlah Cetakan")
        st.info("💡 Isi angka 0 jika tidak ingin mencetak ukuran tersebut.")
        
        # Kolom Input Jumlah
        col_pas, col_r1, col_r2 = st.columns(3)
        
        with col_pas:
            st.markdown("**Pasfoto**")
            jml_2x3 = st.number_input("2x3 cm", min_value=0, max_value=50, value=0)
            jml_3x4 = st.number_input("3x4 cm", min_value=0, max_value=50, value=0)
            jml_4x6 = st.number_input("4x6 cm", min_value=0, max_value=50, value=0)
            
        with col_r1:
            st.markdown("**Ukuran Studio R**")
            jml_2r = st.number_input("2R (Dompet)", min_value=0, max_value=20, value=0)
            jml_3r = st.number_input("3R", min_value=0, max_value=20, value=0)
            jml_4r = st.number_input("4R", min_value=0, max_value=20, value=0)
            jml_5r = st.number_input("5R", min_value=0, max_value=10, value=0)
            
        with col_r2:
            st.markdown("**Cetak Besar**")
            jml_6r = st.number_input("6R", min_value=0, max_value=10, value=0)
            jml_8r = st.number_input("8R (A4 Penuh)", min_value=0, max_value=10, value=0)
            jml_10r = st.number_input("10R (Ekstra Besar)", min_value=0, max_value=5, value=0)
            
        if st.button("🖨️ Buat File Cetak (PDF)", type="primary", use_container_width=True):
            with st.spinner("Memotong dan menyusun foto ke kertas..."):
                # Kamus Ukuran dalam Pixel (Resolusi 300 DPI)
                dpi = 300
                ukuran_px = {
                    "2x3": (236, 354), "3x4": (354, 472), "4x6": (472, 709),
                    "2R": (709, 1063), "3R": (1051, 1500), "4R": (1205, 1795),
                    "5R": (1500, 2102), "6R": (1795, 2398), "8R": (2398, 3000),
                    "10R": (3000, 3602)
                }
                
                # Mengumpulkan semua pesanan
                pesanan = []
                pesanan.extend(["2x3"] * jml_2x3)
                pesanan.extend(["3x4"] * jml_3x4)
                pesanan.extend(["4x6"] * jml_4x6)
                pesanan.extend(["2R"] * jml_2r)
                pesanan.extend(["3R"] * jml_3r)
                pesanan.extend(["4R"] * jml_4r)
                pesanan.extend(["5R"] * jml_5r)
                pesanan.extend(["6R"] * jml_6r)
                pesanan.extend(["8R"] * jml_8r)
                pesanan.extend(["10R"] * jml_10r)
                
                if not pesanan:
                    st.warning("⚠️ Anda belum memasukkan jumlah foto yang ingin dicetak!")
                else:
                    # Sortir dari ukuran terbesar ke terkecil agar susunannya rapi (Bin Packing sederhana)
                    pesanan.sort(key=lambda x: ukuran_px[x][0] * ukuran_px[x][1], reverse=True)
                    
                    # Ukuran Kertas A4 dalam pixel (300 DPI)
                    a4_w, a4_h = 2480, 3508
                    margin = 50 # Jarak antar foto untuk gunting
                    
                    halaman_cetak = []
                    kanvas_saat_ini = Image.new("RGB", (a4_w, a4_h), "white")
                    x, y = margin, margin
                    tinggi_baris = 0
                    
                    for nama_ukuran in pesanan:
                        w_px, h_px = ukuran_px[nama_ukuran]
                        
                        # Potong cerdas (Center Crop anti-gepeng)
                        foto_crop = ImageOps.fit(img_cetak, (w_px, h_px), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                        
                        # 10R lebih besar dari A4, buatkan kanvas khusus
                        if nama_ukuran == "10R":
                            kanvas_10r = Image.new("RGB", (w_px + margin*2, h_px + margin*2), "white")
                            kanvas_10r.paste(foto_crop, (margin, margin))
                            halaman_cetak.append(kanvas_10r)
                            continue
                            
                        # Cek apakah muat ke samping, kalau tidak turun baris
                        if x + w_px + margin > a4_w:
                            x = margin
                            y += tinggi_baris + margin
                            tinggi_baris = 0
                            
                        # Cek apakah muat ke bawah, kalau tidak buat kertas baru
                        if y + h_px + margin > a4_h:
                            halaman_cetak.append(kanvas_saat_ini)
                            kanvas_saat_ini = Image.new("RGB", (a4_w, a4_h), "white")
                            x, y = margin, margin
                            tinggi_baris = 0
                            
                        # Tempel foto ke kanvas
                        kanvas_saat_ini.paste(foto_crop, (x, y))
                        
                        # Update posisi
                        x += w_px + margin
                        tinggi_baris = max(tinggi_baris, h_px)
                        
                    # Simpan sisa kanvas terakhir (jika ada isinya)
                    if kanvas_saat_ini.getbbox():
                        halaman_cetak.append(kanvas_saat_ini)
                        
                    # Proses menjadi 1 file PDF
                    buf_pdf = io.BytesIO()
                    if len(halaman_cetak) > 0:
                        halaman_cetak[0].save(
                            buf_pdf, format="PDF", save_all=True, append_images=halaman_cetak[1:]
                        )
                    
                    st.success(f"🎉 Selesai! Menghasilkan {len(halaman_cetak)} lembar kertas.")
                    
                    st.download_button(
                        label="📄 Download File Siap Print (.PDF)",
                        data=buf_pdf.getvalue(),
                        file_name="cetak_studio_multatuli.pdf",
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                    st.info("💡 **Tips Nge-Print:** Buka PDF-nya, tekan `Ctrl + P`, lalu pastikan pengaturan ukuran kertasnya **A4** dan skalanya **Actual Size (100%)** agar ukurannya akurat!")





