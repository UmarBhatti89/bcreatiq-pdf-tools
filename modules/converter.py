# modules/converter.py
import fitz  # PyMuPDF
from PIL import Image
import io
import zipfile
import os
from docx2pdf import convert
from pdf2docx import Converter

# --- 1. PDF TO IMAGES ---
def pdf_to_images_logic(uploaded_file, img_format="png", dpi=200):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            if img_format.lower() in ["jpg", "jpeg"]:
                img_data = pix.tobytes("jpg")
                ext = "jpg"
            else:
                img_data = pix.tobytes("png")
                ext = "png"
            zf.writestr(f"page_{i+1}.{ext}", img_data)

    zip_buffer.seek(0)
    return zip_buffer

# --- 2. IMAGES TO PDF ---
def images_to_pdf_logic(uploaded_images):
    if not uploaded_images: return None
    pil_images = []
    for img_file in uploaded_images:
        img = Image.open(img_file)
        if img.mode == 'RGBA':
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        pil_images.append(img)

    output = io.BytesIO()
    if pil_images:
        pil_images[0].save(output, "PDF", save_all=True, append_images=pil_images[1:])
    output.seek(0)
    return output

# --- 3. WORD TO PDF (Requires MS Word Installed) ---
def word_to_pdf_logic(uploaded_file):
    # Temp file banani padegi kyunki library path mangti hai
    temp_docx = "temp_input.docx"
    temp_pdf = "temp_output.pdf"
    
    with open(temp_docx, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    try:
        # Conversion
        convert(temp_docx, temp_pdf)
        
        # Read Result
        with open(temp_pdf, "rb") as f:
            pdf_data = f.read()
            
        return io.BytesIO(pdf_data)
        
    finally:
        # Cleanup (Files delete karein)
        if os.path.exists(temp_docx): os.remove(temp_docx)
        if os.path.exists(temp_pdf): os.remove(temp_pdf)

# --- 4. PDF TO WORD ---
def pdf_to_word_logic(uploaded_file):
    temp_pdf = "temp_input.pdf"
    temp_docx = "temp_output.docx"
    
    with open(temp_pdf, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    try:
        cv = Converter(temp_pdf)
        cv.convert(temp_docx)
        cv.close()
        
        with open(temp_docx, "rb") as f:
            docx_data = f.read()
            
        return io.BytesIO(docx_data)
        
    finally:
        if os.path.exists(temp_pdf): os.remove(temp_pdf)
        if os.path.exists(temp_docx): os.remove(temp_docx)