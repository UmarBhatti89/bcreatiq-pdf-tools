# modules/converter.py
import fitz  # PyMuPDF
import io
from PIL import Image
import os
from pdf2docx import Converter

# NOTE: Humne 'docx2pdf' hata diya hai kyunki wo Cloud par crash karta hai.

# ======================================================
# 1. PDF TO IMAGES
# ======================================================
def pdf_to_images_logic(uploaded_file, ext="png"):
    try:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        
        # Zip file memory me banayenge
        import zipfile
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes(ext)
                zf.writestr(f"page_{i+1}.{ext}", img_data)
                
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        raise RuntimeError(f"Error converting to images: {e}")

# ======================================================
# 2. IMAGES TO PDF
# ======================================================
def images_to_pdf_logic(image_files):
    try:
        if not image_files:
            return None
            
        # Pehli image ko base banayen
        first_image = Image.open(image_files[0])
        first_image = first_image.convert("RGB")
        
        other_images = []
        for f in image_files[1:]:
            img = Image.open(f)
            img = img.convert("RGB")
            other_images.append(img)
            
        output_buffer = io.BytesIO()
        first_image.save(output_buffer, save_all=True, append_images=other_images, format="PDF")
        output_buffer.seek(0)
        return output_buffer
    except Exception as e:
        raise RuntimeError(f"Error creating PDF: {e}")

# ======================================================
# 3. PDF TO WORD (Digital Only)
# ======================================================
def pdf_to_word_logic(uploaded_file):
    docx_path = "converted_digital.docx"
    temp_pdf_path = "temp_input.pdf"
    
    try:
        uploaded_file.seek(0)
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.read())
            
        cv = Converter(temp_pdf_path)
        cv.convert(docx_path)
        cv.close()
        
        with open(docx_path, "rb") as f:
            data = io.BytesIO(f.read())
            
        return data
    except Exception as e:
        raise RuntimeError(f"Conversion Error: {e}")
    finally:
        if os.path.exists(docx_path): os.remove(docx_path)
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)

# ======================================================
# 4. WORD TO PDF (DISABLED FOR CLOUD)
# ======================================================
def word_to_pdf_logic(docx_file):
    # Ye function Cloud par nahi chal sakta bina MS Word ke.
    # Hum bas ek error raise karenge taake user ko pata chal jaye.
    raise NotImplementedError("⚠️ Word to PDF conversion requires Windows Server. This feature is disabled on Free Cloud Hosting.")
