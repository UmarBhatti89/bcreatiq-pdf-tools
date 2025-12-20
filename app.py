import streamlit as st
from PIL import Image
import base64

# --- IMPORTS FROM MODULES ---
from modules.resizer import process_pdf_resize
from modules.file_ops import (
    merge_pdfs_logic, split_pdf_logic, split_all_pages_logic,
    reorder_pdf_logic, move_page_logic, rotate_pdf_logic
)
from modules.ocr_engine import (
    ocr_to_word_logic, ocr_to_searchable_pdf_logic, extract_raw_text_logic
)
from modules.converter import (
    pdf_to_images_logic, images_to_pdf_logic,
    word_to_pdf_logic, pdf_to_word_logic
)
from modules.protection import (
    compress_pdf_logic, add_watermark_logic,
    manage_security_logic
)
from modules.editor import remove_text_logic

# ======================================================
# 1. PAGE CONFIG & STYLING
# ======================================================
st.set_page_config(
    page_title="bCreatiq PDF Suite",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (THEME) ---
# app.py mein local_css function ko is se replace karein:

def local_css():
    st.markdown("""
    <style>
        /* MAIN BACKGROUND & FONT */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* MOBILE OPTIMIZATION: Reduce top padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }

        /* SIDEBAR STYLE */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }

        /* CUSTOM BUTTONS (Gradient) */
        .stButton>button {
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            color: white;
            border: none;
            padding: 10px 24px;
            width: 100%;  /* Full width on mobile */
            border-radius: 8px;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: 0.3s;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #d53369 0%, #daae51 100%);
            transform: scale(1.02);
        }

        /* CARD STYLE */
        .css-1r6slb0 {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ======================================================
# 2. HELPER FUNCTIONS
# ======================================================
def valid_output(data):
    # Check if data exists
    return data is not None

def safe_download(label, data, name, mime):
    if valid_output(data):
        st.download_button(
            label=label,
            data=data,
            file_name=name,
            mime=mime,
            use_container_width=True # Full width button
        )
    else:
        st.warning("⚠️ No output generated. Please check your inputs.")

# ======================================================
# 3. SIDEBAR NAVIGATION
# ======================================================
with st.sidebar:
    # --- LOGO AREA ---
    try:
        # Logo display karein (Make sure logo.png folder me ho)
        st.image("logo.png", use_container_width=True)
    except:
        st.title("bCreatiq") # Agar logo na mile to Text dikhaye
        st.caption("Automation & Design Lab")

    st.markdown("---")
    
    # --- MENU ---
    tool = st.radio(
        "Select a Tool:",
        [
            "📐 Page Resizer & Cropper",
            "📂 File Operations",
            "🔄 Conversion Tools",
            "🛡️ Optimization & Security",
            "📝 Content Editor"
        ],
        label_visibility="collapsed" # Hide label for cleaner look
    )

    st.markdown("---")
    st.info("Developed by **bCreatiq Tech Lab**\n\nNeed Help? info@bcreatiq.com")

# ======================================================
# 4. MAIN CONTENT AREA
# ======================================================

# --- HEADER SECTION ---
# Tool ke hisab se header aur description
header_icons = {
    "📐 Page Resizer & Cropper": "Resize, Crop & Adjust PDF Pages",
    "📂 File Operations": "Merge, Split, Rotate & Reorder",
    "🔄 Conversion Tools": "Convert between PDF, Images, Word & OCR",
    "🛡️ Optimization & Security": "Compress, Watermark & Protect",
    "📝 Content Editor": "Remove Text & Clean Documents"
}

st.title(tool.split(" ", 1)[1]) # Icon hata kar title dikhayen
st.markdown(f"*{header_icons[tool]}*")
st.markdown("---")

# ======================================================
# TOOL 1: PAGE RESIZER
# ======================================================
if "Resizer" in tool:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("1. Upload File")
        f = st.file_uploader("Upload PDF", type="pdf")
        
    with col2:
        st.subheader("2. Settings")
        w = st.number_input("Target Width (inch)", 1.0, 50.0, 8.5)
        h = st.number_input("Target Height (inch)", 1.0, 50.0, 11.0)
        mode = st.selectbox("Processing Mode", ["Simple Resize", "Smart Center Crop", "Force Fit"])
        
        threshold = 250
        if "Crop" in mode or "Fit" in mode:
            threshold = st.slider("White Detection Sensitivity", 200, 255, 250)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Start Processing") and f:
        with st.spinner("Resizing pages..."):
            try:
                res, cnt = process_pdf_resize(f, w, h, mode, threshold)
                st.success(f"Success! {cnt} pages processed.")
                safe_download("⬇️ Download Result", res, "resized_bcreatiq.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")

# ======================================================
# TOOL 2: FILE OPERATIONS
# ======================================================
elif "File Operations" in tool:
    action = st.selectbox("What would you like to do?", 
                          ["Merge PDFs", "Split PDF", "Reorder Pages", "Rotate Pages"])
    st.divider()

    if action == "Merge PDFs":
        files = st.file_uploader("Select PDF Files", type="pdf", accept_multiple_files=True)
        if st.button("🔗 Merge Files") and files:
            safe_download("⬇️ Download Merged", merge_pdfs_logic(files), "merged.pdf", "application/pdf")

    elif action == "Split PDF":
        f = st.file_uploader("Upload PDF", type="pdf")
        split_mode = st.radio("Mode", ["Extract Specific Pages", "Split All Pages (ZIP)"], horizontal=True)
        
        if split_mode == "Extract Specific Pages":
            r = st.text_input("Pages (e.g. 1-3, 5)")
            if st.button("✂️ Extract") and f and r:
                safe_download("⬇️ Download", split_pdf_logic(f, r), "extracted.pdf", "application/pdf")
        else:
            if st.button("📦 Split All & Zip") and f:
                safe_download("⬇️ Download ZIP", split_all_pages_logic(f), "split_pages.zip", "application/zip")

    elif action == "Reorder Pages":
        f = st.file_uploader("Upload PDF", type="pdf")
        mode = st.radio("Mode", ["Move Single Page", "Custom Order"], horizontal=True)
        
        if mode == "Move Single Page":
            c1, c2 = st.columns(2)
            with c1: pg_move = st.number_input("Move Page", min_value=1)
            with c2: pg_to = st.number_input("To Position", min_value=1)
            if st.button("Move") and f:
                safe_download("⬇️ Download", move_page_logic(f, pg_move, pg_to), "reordered.pdf", "application/pdf")
        else:
            o = st.text_input("New Order (e.g. 2, 1, 3)")
            if st.button("Reorder") and f and o:
                safe_download("⬇️ Download", reorder_pdf_logic(f, o), "reordered.pdf", "application/pdf")

    elif action == "Rotate Pages":
        f = st.file_uploader("Upload PDF", type="pdf")
        c1, c2 = st.columns(2)
        with c1: deg = st.selectbox("Angle", [90, 180, 270])
        with c2: pgs = st.text_input("Pages (Leave empty for ALL)")
        if st.button("Rotate") and f:
            safe_download("⬇️ Download", rotate_pdf_logic(f, deg, pgs), "rotated.pdf", "application/pdf")

# ======================================================
# TOOL 3: CONVERSION
# ======================================================
elif "Conversion" in tool:
    mode = st.selectbox("Conversion Mode", 
        ["OCR (Scanned → Word/PDF)", "PDF → Images", "Images → PDF", "Word → PDF", "PDF → Word (Digital)"])
    st.divider()

    if "OCR" in mode:
        st.info("💡 Best for Scanned Documents & Images")
        
        c1, c2 = st.columns(2)
        with c1: 
            input_type = st.radio("Input", ("Upload PDF", "Upload Image"))
            file = st.file_uploader("File", type=["pdf", "png", "jpg"]) if input_type == "Upload PDF" else st.file_uploader("File", type=["png", "jpg"])
            ftype = "pdf" if input_type == "Upload PDF" else "image"

        with c2:
            st.markdown("#### Actions")
            tab1, tab2 = st.tabs(["⬇️ Download File", "📜 View Text"])
            
            with tab1:
                fmt = st.radio("Format", ("Editable Word", "Searchable PDF"))
                if st.button("Convert & Download") and file:
                    with st.spinner("Running OCR..."):
                        try:
                            if "Word" in fmt:
                                res = ocr_to_word_logic(file, ftype)
                                safe_download("⬇️ Download Word", res, "ocr.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                            else:
                                res = ocr_to_searchable_pdf_logic(file, ftype)
                                safe_download("⬇️ Download PDF", res, "ocr.pdf", "application/pdf")
                        except Exception as e: st.error(f"Error: {e}")
            
            with tab2:
                if st.button("Extract Text") and file:
                    try:
                        st.text_area("Result", extract_raw_text_logic(file, ftype), height=300)
                    except Exception as e: st.error(str(e))

    elif "PDF → Images" in mode:
        f = st.file_uploader("PDF", type="pdf")
        if st.button("Convert to JPG/PNG") and f:
            safe_download("⬇️ Download ZIP", pdf_to_images_logic(f, "png"), "images.zip", "application/zip")

    elif "Images → PDF" in mode:
        imgs = st.file_uploader("Images", type=["png","jpg"], accept_multiple_files=True)
        if st.button("Create PDF") and imgs:
            safe_download("⬇️ Download PDF", images_to_pdf_logic(imgs), "images.pdf", "application/pdf")

    elif "Word → PDF" in mode:
        f = st.file_uploader("Word Doc", type="docx")
        if st.button("Convert") and f:
            safe_download("⬇️ Download PDF", word_to_pdf_logic(f), "converted.pdf", "application/pdf")
            
    elif "PDF → Word" in mode:
        f = st.file_uploader("Digital PDF", type="pdf")
        if st.button("Convert") and f:
            safe_download("⬇️ Download Word", pdf_to_word_logic(f), "converted.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ======================================================
# TOOL 4: OPTIMIZATION
# ======================================================
elif "Optimization" in tool:
    opt = st.selectbox("Select Action", ["Compress PDF", "Add Watermark", "Password Security"])
    st.divider()
    f = st.file_uploader("Upload PDF", type="pdf")

    if f and opt == "Compress PDF":
        lvl = st.select_slider("Compression Level", ["Standard", "Strong"])
        if st.button("Compress"):
            safe_download("⬇️ Download", compress_pdf_logic(f, lvl), "compressed.pdf", "application/pdf")

    elif f and opt == "Add Watermark":
        wm_type = st.radio("Type", ["Text", "Image"])
        if wm_type == "Text":
            txt = st.text_input("Watermark Text", "CONFIDENTIAL")
            if st.button("Apply"):
                safe_download("⬇️ Download", add_watermark_logic(f, watermark_text=txt), "wm.pdf", "application/pdf")
        else:
            img = st.file_uploader("Upload Logo", type=["png", "jpg"])
            if st.button("Apply") and img:
                safe_download("⬇️ Download", add_watermark_logic(f, watermark_image=img), "wm.pdf", "application/pdf")

    elif f and opt == "Password Security":
        pw = st.text_input("Password", type="password")
        if st.button("Protect PDF") and pw:
            safe_download("⬇️ Download", manage_security_logic(f, "Add Password", pw), "protected.pdf", "application/pdf")

# ======================================================
# TOOL 5: CONTENT EDITOR
# ======================================================
elif "Content Editor" in tool:
    st.info("🚫 This tool permanently removes text from the PDF.")
    f = st.file_uploader("Upload PDF", type="pdf")
    
    c1, c2 = st.columns(2)
    with c1:
        txt = st.text_input("Text to Remove (Case insensitive)")
    with c2:
        clean_all = st.checkbox("Remove ALL Text (Clean Slate)")
        
    if st.button("Start Cleaning") and f:
        try:
            res, cnt = remove_text_logic(f, txt, remove_all=clean_all)
            if cnt > 0:
                st.success(f"Removed content from {cnt} pages.")
                safe_download("⬇️ Download Cleaned PDF", res, "cleaned.pdf", "application/pdf")
            else:
                st.warning("No matching text found.")
        except Exception as e:

            st.error(f"Error: {e}")
