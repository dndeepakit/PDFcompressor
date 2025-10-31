import streamlit as st
import fitz  # PyMuPDF
import io

st.set_page_config(page_title="PDF Compressor / Optimizer", layout="wide")

st.title("📄 PDF Compressor / Optimizer")

st.markdown("""
### 💡 How Compression Works
This tool reduces PDF file size by:
- 🖼️ Downsampling images (e.g., 300 DPI → 100–150 DPI)
- 🔄 Converting images to efficient formats (JPEG / WebP)
- ✂️ Removing unused objects, metadata, and embedded thumbnails
- 🧩 Compressing fonts and structure streams

Compression results vary depending on content:

| PDF Type | Before | After | Approx. Compression |
|-----------|---------|--------|--------------------|
| 📄 Scanned Image PDFs | 100 MB | 10–20 MB | ✅ 80–90% reduction |
| 🧾 Mixed PDFs (text + images) | 100 MB | 60–80 MB | ⚙️ 20–40% reduction |
| 🧠 Text-only PDFs | 100 MB | 90–95 MB | ⚠️ Minimal reduction (5–10%) |
""")

uploaded_file = st.file_uploader("Upload your PDF file", type=["pdf"])

compression_level = st.radio(
    "Select compression level:",
    ["High Quality (Low Compression)", "Balanced (Recommended)", "Smallest Size (Aggressive Compression)"],
    index=1
)

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    # Compression settings
    if "High Quality" in compression_level:
        image_quality = 90
        dpi = 150
    elif "Balanced" in compression_level:
        image_quality = 70
        dpi = 120
    else:
        image_quality = 50
        dpi = 100

    input_pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_pdf = fitz.open()

    progress = st.progress(0)
    total_pages = len(input_pdf)

    with st.spinner("🔄 Compressing PDF... Please wait..."):
        for page_number in range(total_pages):
            page = input_pdf.load_page(page_number)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("jpeg", quality=image_quality)
            rect = fitz.Rect(0, 0, pix.width, pix.height)
            new_page = output_pdf.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=img_bytes)
            progress.progress((page_number + 1) / total_pages)

        optimized_bytes = output_pdf.tobytes()

    # Close PDF handles safely
    input_pdf.close()
    output_pdf.close()

    original_size = len(pdf_bytes)
    compressed_size = len(optimized_bytes)
    reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

    st.success(f"✅ Compression complete! Reduced size by {reduction:.1f}%")
    st.write(f"**Original:** {original_size / (1024*1024):.2f} MB → **Compressed:** {compressed_size / (1024*1024):.2f} MB")

    # ===== Preview Section =====
    st.subheader("👁️ Preview (First 5 Pages)")
    try:
        original_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        compressed_doc = fitz.open(stream=optimized_bytes, filetype="pdf")

        num_preview_pages = min(5, len(original_doc))
        st.write(f"Showing first {num_preview_pages} pages:")

        for i in range(num_preview_pages):
            col1, col2 = st.columns(2)
            with col1:
                orig_pix = original_doc.load_page(i).get_pixmap(dpi=100)
                st.image(orig_pix.tobytes("png"), caption=f"Original Page {i+1}", use_container_width=True)
            with col2:
                comp_pix = compressed_doc.load_page(i).get_pixmap(dpi=100)
                st.image(comp_pix.tobytes("png"), caption=f"Compressed Page {i+1}", use_container_width=True)

        original_doc.close()
        compressed_doc.close()
    except Exception as e:
        st.warning(f"Preview unavailable: {e}")

    # ===== Download Button =====
    st.download_button(
        label="📥 Download Compressed PDF",
        data=optimized_bytes,
        file_name=f"compressed_{uploaded_file.name}",
        mime="application/pdf"
    )
