import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

st.set_page_config(page_title="PDF Compressor / Optimizer", layout="wide")

st.title("📄 PDF Compressor / Optimizer")

st.markdown("""
### 💡 How Compression Works
This tool reduces PDF file size by:
- 🖼️ Downsampling images (e.g., 300 DPI → 100–150 DPI)
- 🔄 Converting pages to JPEG images with adjustable quality
- ✂️ Removing unused objects and metadata
- 🧩 Rebuilding the PDF with compressed images

| PDF Type | Before | After | Approx. Compression |
|-----------|---------|--------|--------------------|
| 📄 Scanned Image PDFs | 100 MB | 10–20 MB | ✅ 80–90% reduction |
| 🧾 Mixed PDFs | 100 MB | 60–80 MB | ⚙️ 20–40% reduction |
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

    with st.spinner("🔄 Compressing PDF... Please wait..."):
        for page_number in range(len(input_pdf)):
            page = input_pdf.load_page(page_number)
            pix = page.get_pixmap(dpi=dpi)

            # Convert pixmap to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Compress and write to BytesIO
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=image_quality, optimize=True)
            img_bytes.seek(0)

            # Create new page and insert compressed image
            rect = fitz.Rect(0, 0, pix.width, pix.height)
            new_page = output_pdf.new_page(width=rect.width, height=rect.height)
            new_page.insert_image(rect, stream=img_bytes.getvalue())

            progress.progress((page_number + 1) / len(input_pdf))

        optimized_bytes = output_pdf.tobytes()

    input_pdf.close()
    output_pdf.close()

    original_size = len(pdf_bytes)
    compressed_size = len(optimized_bytes)
    reduction = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0

    st.success(f"✅ Compression complete! Reduced size by {reduction:.1f}%")
    st.write(f"**Original:** {original_size / (1024*1024):.2f} MB → **Compressed:** {compressed_size / (1024*1024):.2f} MB")

    # ===== Optional Preview (First 5 pages) =====
    st.subheader("👁️ Preview (First 5 Pages)")
    try:
        orig_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        comp_doc = fitz.open(stream=optimized_bytes, filetype="pdf")

        num_pages = min(5, len(orig_doc))
        for i in range(num_pages):
            col1, col2 = st.columns(2)
            with col1:
                opix = orig_doc.load_page(i).get_pixmap(dpi=80)
                st.image(opix.tobytes("png"), caption=f"Original Page {i+1}", use_container_width=True)
            with col2:
                cpix = comp_doc.load_page(i).get_pixmap(dpi=80)
                st.image(cpix.tobytes("png"), caption=f"Compressed Page {i+1}", use_container_width=True)
        orig_doc.close()
        comp_doc.close()
    except Exception as e:
        st.warning(f"Preview unavailable: {e}")

    # ===== Download Button =====
    st.download_button(
        label="📥 Download Compressed PDF",
        data=optimized_bytes,
        file_name=f"compressed_{uploaded_file.name}",
        mime="application/pdf"
    )
