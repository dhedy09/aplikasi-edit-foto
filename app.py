import streamlit as st
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from datetime import datetime
from geopy.geocoders import Nominatim
import io
import numpy as np
from streamlit_cropper import st_cropper
import fitz  # Ini adalah nama pemanggilan untuk PyMuPDF

# --- 1. KONFIGURASI HALAMAN (WAJIB PALING ATAS & CUMA 1 KALI) ---
st.set_page_config(
    page_title="Studio Mamayo | Alat Foto & SPJ",
    page_icon="📸",
    layout="wide", # Pastikan selalu wide agar tidak sempit
    initial_sidebar_state="expanded"
)

# --- 2. HILANGKAN JEJAK STREAMLIT (CSS) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

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

# --- PENGATURAN SIDEBAR KIRI ---
with st.sidebar:
    # Jika Anda punya file logo, bisa gunakan: st.image("logo_anda.png")
    # Untuk sementara kita pakai teks besar:
    st.markdown("<h1 style='text-align: center;'>📸 Studio Mamayo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Administrasi Digital</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📌 Tentang Aplikasi")
    st.write("Aplikasi cerdas untuk membantu memproses pas foto massal, hapus latar belakang, hingga penyusunan lampiran SPJ dengan hitungan detik.")
    
    st.markdown("---")
    st.info("💡 **Tips:** Gunakan komputer/laptop untuk pengalaman drag-and-drop file yang lebih cepat.")
    
    st.markdown("---")
    st.markdown("**Versi:** 1.0 (Final Release)")
    st.markdown("**Dibuat untuk:** Pekerja Cerdas 🚀")

# --- NAVIGASI MODERN (TABS) ---
st.title("✨ STUDIO FOTO MAMAYO")
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["✂️ Latar", "🗜️ Kompres", "🎨 Warna", "🔄 Format", "🪄 Filter", "🖨️ Cetak Foto", "📑 Lampiran SPJ", "✍️ Ekstrak TTD", "📄 Alat PDF"])

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
# TAB 6: STUDIO CETAK MULTI-FOTO (KERANJANG MASSAL)
# ==========================================
with tab6:
    st.write("Unggah banyak foto sekaligus (Massal) atau satu per satu, lalu cetak rapi dalam kertas A4.")

    # Inisialisasi keranjang cetak jika belum ada
    if "keranjang_cetak" not in st.session_state:
        st.session_state.keranjang_cetak = []

    # 1. Bagian Input Foto & Ukuran
    with st.expander("➕ Tambah Foto ke Antrean Cetak", expanded=True):
        col_up, col_set = st.columns([1, 1])
        
        with col_up:
            # PERUBAHAN UTAMA: accept_multiple_files=True ditambahkan di sini
            foto_input = st.file_uploader("Pilih Satu atau Banyak Foto sekaligus...", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="input_multi_cetak")
            
            # Jika ada foto yang diunggah, tampilkan info
            if foto_input:
                st.info(f"✅ {len(foto_input)} foto siap diproses.")
                # Tampilkan preview kecil untuk maksimal 3 foto pertama saja agar tidak memenuhi layar
                cols = st.columns(min(len(foto_input), 3))
                for i in range(min(len(foto_input), 3)):
                    cols[i].image(foto_input[i], use_container_width=True)
                if len(foto_input) > 3:
                    st.caption(f"... dan {len(foto_input) - 3} foto lainnya.")
        
        with col_set:
            opsi_ukuran = ["2x3", "3x4", "4x6", "2R", "3R", "4R", "5R", "6R", "8R", "10R"]
            pilih_uk = st.selectbox("Pilih Ukuran:", opsi_ukuran)
            pilih_jml = st.number_input("Jumlah lembar PER FOTO:", min_value=1, max_value=50, value=2)
            
            if st.button("📥 Masukkan Semua ke Keranjang", use_container_width=True):
                if foto_input:
                    # Loop untuk memasukkan SEMUA foto yang diunggah ke keranjang sekaligus
                    for file in foto_input:
                        img_data = Image.open(file).convert("RGB")
                        st.session_state.keranjang_cetak.append({
                            "image": img_data,
                            "ukuran": pilih_uk,
                            "jumlah": pilih_jml,
                            "nama_file": file.name
                        })
                    st.success(f"Berhasil memasukkan {len(foto_input)} foto ke antrean!")
                else:
                    st.error("Silakan pilih foto dulu!")

    # 2. Tampilkan Keranjang & Tombol Reset
    if st.session_state.keranjang_cetak:
        st.markdown("### 🛒 Daftar Antrean Cetak")
        
        # Menghitung total lembar foto yang akan dicetak
        total_cetak = sum(item['jumlah'] for item in st.session_state.keranjang_cetak)
        st.write(f"**Total file di keranjang:** {len(st.session_state.keranjang_cetak)} foto.")
        st.write(f"**Total yang akan diprint:** {total_cetak} lembar potongan foto.")
        
        if st.button("🗑️ Kosongkan Keranjang"):
            st.session_state.keranjang_cetak = []
            st.rerun()

        st.markdown("---")

        # --- FITUR BARU: PENGATURAN KUSTOMISASI KERTAS ---
        st.markdown("### ⚙️ Pengaturan Kertas & Jarak")
        st.info("💡 Sesuaikan nilai ini jika jarak antar foto terlalu sempit atau terlalu lebar.")
        col_margin, col_jarak = st.columns(2)
        with col_margin:
            margin_tepi = st.number_input("Margin Tepi Kertas (pixel)", min_value=0, max_value=200, value=50, help="Jarak aman dari batas ujung kertas (agar tidak terpotong printer).")
        with col_jarak:
            jarak_foto = st.number_input("Jarak Antar Foto (pixel)", min_value=0, max_value=150, value=50, help="Ruang putih di antara foto untuk tempat menggunting.")

        # 3. Proses Gabungkan ke PDF & Preview
        if st.button("🖨️ PROSES & LIHAT PRATINJAU", type="primary", use_container_width=True):
            with st.spinner(f"Menyusun {total_cetak} foto ke kertas A4..."):
                dpi = 300
                ukuran_px = {
                    "2x3": (236, 354), "3x4": (354, 472), "4x6": (472, 709),
                    "2R": (709, 1063), "3R": (1051, 1500), "4R": (1205, 1795),
                    "5R": (1500, 2102), "6R": (1795, 2398), "8R": (2398, 3000),
                    "10R": (3000, 3602)
                }
                
                # Mengumpulkan semua pesanan dari keranjang
                semua_pesanan = []
                for item in st.session_state.keranjang_cetak:
                    for _ in range(item['jumlah']):
                        semua_pesanan.append({"img": item['image'], "uk": item['ukuran']})
                
                # Sortir ukuran besar ke kecil agar susunan efisien
                semua_pesanan.sort(key=lambda x: ukuran_px[x['uk']][0] * ukuran_px[x['uk']][1], reverse=True)
                
                a4_w, a4_h = 2480, 3508
                halaman_cetak = []
                kanvas = Image.new("RGB", (a4_w, a4_h), "white")
                
                # Menggunakan variabel kustom dari user
                x, y, tinggi_baris = margin_tepi, margin_tepi, 0
                
                for item in semua_pesanan:
                    w_px, h_px = ukuran_px[item['uk']]
                    foto_crop = ImageOps.fit(item['img'], (w_px, h_px), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    
                    # Border hitam tipis untuk garis gunting
                    draw_border = ImageDraw.Draw(foto_crop)
                    draw_border.rectangle([0, 0, w_px - 1, h_px - 1], outline="black", width=2)

                    if item['uk'] == "10R":
                        k10 = Image.new("RGB", (w_px + margin_tepi*2, h_px + margin_tepi*2), "white")
                        k10.paste(foto_crop, (margin_tepi, margin_tepi))
                        halaman_cetak.append(k10)
                        continue

                    # Cek apakah muat ke kanan
                    if x + w_px + margin_tepi > a4_w:
                        x = margin_tepi
                        y += tinggi_baris + jarak_foto
                        tinggi_baris = 0
                        
                    # Cek apakah muat ke bawah
                    if y + h_px + margin_tepi > a4_h:
                        halaman_cetak.append(kanvas)
                        kanvas = Image.new("RGB", (a4_w, a4_h), "white")
                        x, y, tinggi_baris = margin_tepi, margin_tepi, 0
                        
                    # Tempel foto
                    kanvas.paste(foto_crop, (x, y))
                    x += w_px + jarak_foto
                    tinggi_baris = max(tinggi_baris, h_px)
                
                # Masukkan sisa kertas terakhir
                if kanvas.getbbox():
                    halaman_cetak.append(kanvas)
                
                # Simpan PDF ke memory
                buf_pdf = io.BytesIO()
                halaman_cetak[0].save(buf_pdf, format="PDF", save_all=True, append_images=halaman_cetak[1:])
                
                st.success(f"🎉 Selesai! Menggunakan {len(halaman_cetak)} halaman kertas A4.")

                # --- FITUR BARU: TAMPILKAN PRATINJAU ---
                st.markdown("### 👁️ Pratinjau Hasil Cetak")
                # Jika halamannya banyak, kita tampilkan dalam kolom agar tidak memakan tempat ke bawah
                cols_preview = st.columns(min(len(halaman_cetak), 3)) 
                for i, img_page in enumerate(halaman_cetak):
                    # Menampilkan gambar per halaman
                    cols_preview[i % 3].image(img_page, caption=f"Kertas {i+1}", use_container_width=True)
                
                st.markdown("---")
                
                # Tombol Download
                st.download_button(
                    label="📥 Download File PDF (Siap Print)", 
                    data=buf_pdf.getvalue(), 
                    file_name="cetak_massal_multatuli.pdf", 
                    mime="application/pdf", 
                    type="primary", 
                    use_container_width=True
                )

# ==========================================
# TAB 7: PEMBUAT LAMPIRAN SPJ / DOKUMENTASI
# ==========================================
with tab7:
    st.write("Susun foto dokumentasi kegiatan otomatis untuk lampiran SPJ atau Laporan (Mendukung Kertas F4).")
    
    spj_files = st.file_uploader("Unggah Banyak Foto Kegiatan sekaligus...", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="upload_spj")
    
    if spj_files:
        st.info(f"✅ {len(spj_files)} foto siap disusun.")
        
        # --- INPUT JUDUL & PENGATURAN MARGIN ---
        judul_lampiran = st.text_input("Judul Lampiran (Opsional):", "DOKUMENTASI KEGIATAN")
        
        st.markdown("**⚙️ Pengaturan Jarak (Margin)**")
        col_jarak1, col_jarak2 = st.columns(2)
        with col_jarak1:
            posisi_y_teks = st.number_input("Jarak Judul dari Atas (pixel)", min_value=0, max_value=1000, value=150, step=10, help="Semakin besar angkanya, judul semakin turun ke bawah.")
        with col_jarak2:
            margin_y = st.number_input("Jarak Foto dari Atas (pixel)", min_value=0, max_value=1500, value=350, step=10, help="Pastikan angka ini lebih besar dari Jarak Judul agar foto tidak menabrak teks judul.")
        
        st.markdown("**📄 Pengaturan Kertas & Layout**")
        col_kertas, col_layout = st.columns(2)
        with col_kertas:
            jenis_kertas = st.selectbox("Ukuran Kertas:", ["A4 (21 x 29.7 cm)", "F4 (21 x 33 cm)"])
        with col_layout:
            jenis_layout = st.selectbox("Susunan Foto per Halaman:", ["2 Foto (Atas-Bawah)", "4 Foto (Grid 2x2)", "6 Foto (Grid 3x2)"])
            
        if st.button("📑 PROSES & LIHAT PRATINJAU", type="primary", use_container_width=True):
            with st.spinner("Menyusun foto dan mencetak judul ke halaman..."):
                
                # 1. Tentukan ukuran kertas dalam Pixel (Resolusi Tinggi 300 DPI)
                if "A4" in jenis_kertas:
                    w_kertas, h_kertas = 2480, 3508
                else: # F4 (21 cm x 33 cm)
                    w_kertas, h_kertas = 2480, 3898 
                    
                # 2. Tentukan jumlah baris dan kolom
                if "2 Foto" in jenis_layout:
                    cols, rows = 1, 2
                elif "4 Foto" in jenis_layout:
                    cols, rows = 2, 2
                else: # 6 Foto
                    cols, rows = 2, 3
                    
                # 3. Pengaturan Ruang & Margin
                margin_x = 150 # Margin kiri-kanan kertas
                # margin_y sudah diambil dari input pengguna di atas
                jarak_x = 80   # Jarak horizontal antar foto
                jarak_y = 120  # Jarak vertikal antar foto
                
                avail_w = w_kertas - (margin_x * 2) - (jarak_x * (cols - 1))
                avail_h = h_kertas - (margin_y * 2) - (jarak_y * (rows - 1))
                cell_w = avail_w // cols
                cell_h = avail_h // rows
                
                # Siapkan Font untuk Judul
                try:
                    font_judul = ImageFont.truetype("Roboto-Regular.ttf", 80)
                except:
                    try:
                        font_judul = ImageFont.load_default(size=80)
                    except:
                        font_judul = ImageFont.load_default()
                
                halaman_spj = []
                kanvas_spj = Image.new("RGB", (w_kertas, h_kertas), "white")
                
                idx_foto = 0
                for file in spj_files:
                    img_kegiatan = Image.open(file).convert("RGB")
                    
                    # Potong tengah agar foto tidak gepeng
                    foto_kegiatan = ImageOps.fit(img_kegiatan, (cell_w, cell_h), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
                    
                    # Bingkai garis hitam
                    draw = ImageDraw.Draw(foto_kegiatan)
                    draw.rectangle([0, 0, cell_w-1, cell_h-1], outline="black", width=4)
                    
                    pos_c = idx_foto % cols
                    pos_r = (idx_foto // cols) % rows
                    
                    x = margin_x + pos_c * (cell_w + jarak_x)
                    y = margin_y + pos_r * (cell_h + jarak_y)
                    
                    # Tempel foto
                    kanvas_spj.paste(foto_kegiatan, (x, y))
                    idx_foto += 1
                    
                    # --- CEK JIKA HALAMAN PENUH ATAU FOTO TERAKHIR ---
                    if idx_foto % (cols * rows) == 0 or file == spj_files[-1]:
                        # Tulis Judul di bagian atas halaman ini sebelum disimpan
                        if judul_lampiran:
                            draw_kanvas = ImageDraw.Draw(kanvas_spj)
                            bbox_teks = draw_kanvas.textbbox((0, 0), judul_lampiran.upper(), font=font_judul)
                            lebar_teks = bbox_teks[2] - bbox_teks[0]
                            posisi_x_teks = (w_kertas - lebar_teks) / 2
                            # posisi_y_teks sudah diambil dari input pengguna di atas
                            
                            draw_kanvas.text((posisi_x_teks, posisi_y_teks), judul_lampiran.upper(), fill="black", font=font_judul)
                            
                        # Simpan halaman yang sudah jadi
                        halaman_spj.append(kanvas_spj)
                        
                        # Buat kertas kosong baru jika masih ada foto tersisa
                        if file != spj_files[-1]:
                            kanvas_spj = Image.new("RGB", (w_kertas, h_kertas), "white")
                            
                # --- FITUR PRATINJAU (PREVIEW) ---
                st.success(f"🎉 Selesai! Berhasil membuat dokumen berisi {len(halaman_spj)} halaman.")
                st.markdown("### 👁️ Pratinjau Hasil Lampiran")
                
                cols_preview = st.columns(min(len(halaman_spj), 3)) 
                for i, img_page in enumerate(halaman_spj):
                    cols_preview[i % 3].image(img_page, caption=f"Halaman {i+1}", use_container_width=True)
                
                st.markdown("---")
                
                # --- TOMBOL DOWNLOAD PDF ---
                buf_pdf_spj = io.BytesIO()
                if halaman_spj:
                    halaman_spj[0].save(buf_pdf_spj, format="PDF", save_all=True, append_images=halaman_spj[1:])
                    
                    st.download_button(
                        label=f"📥 Download File PDF ({jenis_kertas})", 
                        data=buf_pdf_spj.getvalue(), 
                        file_name=f"Lampiran_Dokumentasi.pdf", 
                        mime="application/pdf", 
                        type="primary", 
                        use_container_width=True
                    )

# ==========================================
# TAB 8: EKSTRAKTOR TANDA TANGAN & STEMPEL
# ==========================================
with tab8:
    st.write("Ubah foto tanda tangan atau stempel di kertas menjadi gambar transparan (PNG) siap tempel di dokumen.")
    
    ttd_file = st.file_uploader("Unggah Foto Tanda Tangan / Stempel...", type=["jpg", "png", "jpeg"], key="upload_ttd")
    
    if ttd_file:
        # 1. Buka dan perbaiki rotasi dari HP (EXIF fix)
        img_raw = Image.open(ttd_file)
        img_ttd_asli = ImageOps.exif_transpose(img_raw).convert("RGBA")
        
        # --- UI BERSAMPINGAN ---
        col_asli, col_hasil = st.columns(2, gap="medium")
        
        with col_asli:
            st.markdown("### 📷 1. Foto Asli")
            st.image(img_ttd_asli, use_container_width=True)
            
        # --- PENGATURAN REAL-TIME DI TENGAH ---
        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Transparansi (Real-Time)")
        st.info("💡 Geser tuas di bawah ini sampai latar belakang kertas hilang dan tinta terlihat jelas.")
        
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            toleransi = st.slider("Penghapus Kertas (Toleransi)", min_value=0, max_value=255, value=200, help="Semakin tinggi, semakin banyak bagian kertas yang dihapus.")
        with col_set2:
            kontras = st.slider("Tebalkan Tinta (Kontras)", min_value=1.0, max_value=5.0, value=2.0, step=0.1, help="Menebalkan warna tinta agar tidak pudar.")
            
        # --- PROSES INSTAN (TANPA TOMBOL) ---
        enhancer = ImageEnhance.Contrast(img_ttd_asli)
        img_kontras = enhancer.enhance(kontras)
        
        data_piksel = np.array(img_kontras)
        r, g, b = data_piksel[:, :, 0], data_piksel[:, :, 1], data_piksel[:, :, 2]
        kecerahan = (0.299 * r) + (0.587 * g) + (0.114 * b)
        
        alpha_channel = np.where(kecerahan > toleransi, 0, 255).astype(np.uint8)
        data_piksel[:, :, 3] = alpha_channel
        
        img_hasil_ttd = Image.fromarray(data_piksel)
        
        # --- TAMPILKAN HASIL DI KANAN ---
        with col_hasil:
            st.markdown("### ✨ 2. Hasil Transparan")
            st.image(img_hasil_ttd, use_container_width=True)
            
            buf_ttd = io.BytesIO()
            img_hasil_ttd.save(buf_ttd, format="PNG")
            
            # Memperbaiki error datetime yang Anda alami sebelumnya
            from datetime import datetime
            waktu_sekarang = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            st.download_button(
                label="📥 Download (PNG Transparan)", 
                data=buf_ttd.getvalue(), 
                file_name=f"TTD_{waktu_sekarang}.png", 
                mime="image/png", 
                type="primary", 
                use_container_width=True
            )

# ==========================================
# TAB 9: ALAT PDF POWERFUL (KOMPRES, GABUNG, PECAH)
# ==========================================
with tab9:
    st.write("Alat super cepat dan AMAN untuk mengelola file PDF SPJ atau dokumen administrasi Anda.")
    
    # Sub-menu (Sekarang ada 3 pilihan)
    mode_pdf = st.radio(
        "Pilih Mode Alat PDF:", 
        ["🗜️ Kompres Ukuran", "🔗 Gabungkan PDF", "✂️ Pecah PDF (Split)"], 
        horizontal=True
    )
    st.markdown("---")
    
    # ----------------------------------------
    # FITUR 1: KOMPRES PDF (SAFE MODE - LOSSLESS)
    # ----------------------------------------
    if mode_pdf == "🗜️ Kompres Ukuran":
        st.markdown("### 🗜️ Kompresor PDF Pintar (Lossless)")
        st.info("💡 **Cara Kerja:** Menghapus data sampah di dalam file tanpa memburamkan teks/gambar sama sekali. Aman 100% untuk SPJ.")
        
        file_pdf_kompres = st.file_uploader("Unggah 1 File PDF...", type=["pdf"], key="pdf_compress")
        
        if file_pdf_kompres:
            bytes_asli = file_pdf_kompres.getvalue()
            ukuran_asli_mb = len(bytes_asli) / (1024 * 1024)
            st.markdown(f"**📄 Nama File:** `{file_pdf_kompres.name}`")
            
            if st.button("🗜️ BERSIHKAN & KOMPRES PDF", type="primary", use_container_width=True):
                with st.spinner("Menyapu metadata dan merapatkan struktur PDF..."):
                    try:
                        doc = fitz.open(stream=bytes_asli, filetype="pdf")
                        hasil_bytes = doc.tobytes(garbage=4, deflate=True, clean=True)
                        
                        ukuran_baru_mb = len(hasil_bytes) / (1024 * 1024)
                        
                        if ukuran_asli_mb > 0:
                            penghematan = 100 - ((ukuran_baru_mb / ukuran_asli_mb) * 100)
                        else:
                            penghematan = 0
                            
                        if penghematan < 0:
                            penghematan = 0
                            ukuran_baru_mb = ukuran_asli_mb
                            hasil_bytes = bytes_asli 
                            
                        st.success("✅ Proses Selesai! Tidak ada visual yang diburamkan.")
                        
                        col_metrik1, col_metrik2, col_metrik3 = st.columns(3)
                        col_metrik1.metric(label="Ukuran Asli", value=f"{ukuran_asli_mb:.2f} MB")
                        col_metrik2.metric(label="Ukuran Baru", value=f"{ukuran_baru_mb:.2f} MB", delta=f"-{penghematan:.2f}%", delta_color="inverse")
                        
                        if penghematan < 1.0:
                            st.warning("⚠️ Ukuran nyaris tidak berubah karena PDF Anda sudah sangat padat/terkompresi dari asalnya.")
                        
                        from datetime import datetime
                        waktu = datetime.now().strftime("%H%M%S")
                        
                        st.download_button(
                            label="📥 Download PDF Bersih",
                            data=hasil_bytes,
                            file_name=f"Opt_{waktu}_{file_pdf_kompres.name}",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")

    # ----------------------------------------
    # FITUR 2: GABUNG PDF
    # ----------------------------------------
    elif mode_pdf == "🔗 Gabungkan PDF":
        st.markdown("### 🔗 Penggabung PDF (Merge)")
        st.info("💡 **Tips:** Klik tombol Browse lalu pilih beberapa file sekaligus untuk digabungkan.")
        
        file_pdf_gabung = st.file_uploader("Unggah 2 atau lebih File PDF...", type=["pdf"], accept_multiple_files=True, key="pdf_merge")
        
        if file_pdf_gabung:
            if len(file_pdf_gabung) < 2:
                st.warning("⚠️ Mohon unggah minimal 2 file PDF untuk digabungkan.")
            else:
                st.success(f"Terdapat {len(file_pdf_gabung)} file siap digabungkan.")
                
                with st.expander("Lihat Urutan File", expanded=True):
                    for i, file in enumerate(file_pdf_gabung):
                        st.markdown(f"**{i+1}.** `{file.name}`")
                    
                if st.button("🔗 GABUNGKAN SEMUA PDF", type="primary", use_container_width=True):
                    with st.spinner("Menyatukan dokumen..."):
                        try:
                            pdf_utama = fitz.open()
                            for file in file_pdf_gabung:
                                doc_sementara = fitz.open(stream=file.getvalue(), filetype="pdf")
                                pdf_utama.insert_pdf(doc_sementara)
                                
                            hasil_bytes_gabung = pdf_utama.tobytes()
                            st.success("✅ Seluruh file berhasil disatukan!")
                            
                            from datetime import datetime
                            waktu = datetime.now().strftime("%H%M%S")
                            
                            st.download_button(
                                label="📥 Download PDF Gabungan",
                                data=hasil_bytes_gabung,
                                file_name=f"Gabungan_{len(file_pdf_gabung)}_File_{waktu}.pdf",
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Terjadi kesalahan: {e}")

    # ----------------------------------------
    # FITUR 3: PECAH PDF (SPLIT)
    # ----------------------------------------
    elif mode_pdf == "✂️ Pecah PDF (Split)":
        st.markdown("### ✂️ Pemotong PDF (Split)")
        st.info("💡 **Cara Kerja:** Ekstrak halaman tertentu dari dokumen PDF Anda (misal: ambil halaman 2 sampai 5 saja).")
        
        file_pdf_split = st.file_uploader("Unggah 1 File PDF yang ingin dipotong...", type=["pdf"], key="pdf_split")
        
        if file_pdf_split:
            bytes_split = file_pdf_split.getvalue()
            
            try:
                # Buka PDF untuk mendeteksi jumlah halaman
                doc_split = fitz.open(stream=bytes_split, filetype="pdf")
                total_halaman = len(doc_split)
                
                st.success(f"📄 File dimuat! Total dokumen ini memiliki: **{total_halaman} Halaman**.")
                
                # --- PENGATURAN RENTANG HALAMAN ---
                st.markdown("**Pilih rentang halaman yang ingin diambil:**")
                col_hal1, col_hal2 = st.columns(2)
                
                with col_hal1:
                    hal_awal = st.number_input("Mulai dari Halaman", min_value=1, max_value=total_halaman, value=1)
                with col_hal2:
                    hal_akhir = st.number_input("Sampai Halaman", min_value=1, max_value=total_halaman, value=total_halaman)
                
                # Validasi agar halaman awal tidak lebih besar dari halaman akhir
                if hal_awal > hal_akhir:
                    st.error("⚠️ Halaman awal tidak boleh lebih besar dari halaman akhir!")
                else:
                    if st.button("✂️ POTONG & AMBIL HALAMAN", type="primary", use_container_width=True):
                        with st.spinner(f"Mengekstrak halaman {hal_awal} sampai {hal_akhir}..."):
                            # Buat file PDF kosong baru
                            pdf_baru = fitz.open()
                            
                            # Masukkan halaman yang dipilih (Sistem PyMuPDF dimulai dari indeks 0, jadi kita kurangi 1)
                            pdf_baru.insert_pdf(doc_split, from_page=hal_awal-1, to_page=hal_akhir-1)
                            
                            hasil_bytes_split = pdf_baru.tobytes()
                            
                            st.success(f"✅ Berhasil mengambil {hal_akhir - hal_awal + 1} halaman!")
                            
                            from datetime import datetime
                            waktu = datetime.now().strftime("%H%M%S")
                            
                            st.download_button(
                                label="📥 Download PDF Potongan",
                                data=hasil_bytes_split,
                                file_name=f"Potongan_Hal_{hal_awal}-{hal_akhir}_{file_pdf_split.name}",
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True
                            )
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca PDF: {e}")
        
# --- FOOTER APLIKASI ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    # "Dibuat dengan ❤️ oleh <b>[Nama Anda / Tim Anda]</b> | © 2026 Studio Mamayo"
    "Dibuat dengan ❤️ oleh <b>Mamayo</b> | © 2026 Studio Mamayo"
    "</div>", 
    unsafe_allow_html=True
)



























