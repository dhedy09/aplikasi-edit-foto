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
            margin_tepi = st.number_input("Margin Tepi Kertas (pixel)", min_value=0, max_value=200, value=40, help="Jarak aman dari batas ujung kertas (agar tidak terpotong printer).")
        with col_jarak:
            jarak_foto = st.number_input("Jarak Antar Foto (pixel)", min_value=0, max_value=150, value=30, help="Ruang putih di antara foto untuk tempat menggunting.")

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












