# modules/ocr_engine.py
import fitz  # PyMuPDF
import pytesseract
from pdf2docx import Converter
from PIL import Image
import io
import os

# NOTE: Cloud par path set karne ki zaroorat nahi hoti, 
# aur pythoncom (Windows library) ki bhi zaroorat nahi hai.

# ==============================================================================
# HELPER: IMAGES NIKALNA
# ==============================================================================
def get_images_from_upload(uploaded_file, input_type):
    images = []
    if input_type == "image":
        img = Image.open(uploaded_file)
        images.append(img)
    else:
        uploaded_file.seek(0)
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            # High Quality Scan for Cloud
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
    return images

# ==============================================================================
# 1. OCR TO WORD (TEXT-ONLY LAYOUT MODE)
# ==============================================================================
def ocr_to_word_logic(uploaded_file, input_type="pdf"):
    temp_pdf_path = "temp_text_layer.pdf"
    docx_output_path = "converted_ocr_final.docx"
    
    try:
        # 1. Images nikalein
        images = get_images_from_upload(uploaded_file, input_type)

        # 2. OCR Loop
        merged_pdf = fitz.open()
        
        # Cloud par Urdu+English support ke liye 'eng+urd' use karein
        # 'textonly_pdf=1' image hata kar sirf text rakhega (Best for Word conversion)
        custom_config = r'-c textonly_pdf=1 --oem 3 --psm 6' 
        
        for img in images:
            try:
                # Pehle koshish karein ke Urdu+English dono dhoonde
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='eng+urd', config=custom_config)
                img_pdf = fitz.open("pdf", pdf_bytes)
                merged_pdf.insert_pdf(img_pdf)
            except Exception:
                # Agar fail ho to sirf English try kare
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='eng', config=custom_config)
                img_pdf = fitz.open("pdf", pdf_bytes)
                merged_pdf.insert_pdf(img_pdf)

        merged_pdf.save(temp_pdf_path)

        # 3. Convert to Word
        cv = Converter(temp_pdf_path)
        cv.convert(docx_output_path) 
        cv.close()
        
        with open(docx_output_path, "rb") as f:
            docx_data = io.BytesIO(f.read())

        return docx_data

    except Exception as e:
        raise RuntimeError(f"Conversion Error: {e}")
        
    finally:
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)
        if os.path.exists(docx_output_path): os.remove(docx_output_path)

# ==============================================================================
# 2. OCR TO SEARCHABLE PDF
# ==============================================================================
def ocr_to_searchable_pdf_logic(uploaded_file, input_type="pdf"):
    try:
        images = get_images_from_upload(uploaded_file, input_type)
        merged_pdf = fitz.open()
        custom_config = r'--oem 3 --psm 3'
        
        for img in images:
            # Urdu + English
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='eng+urd', config=custom_config)
            img_pdf = fitz.open("pdf", pdf_bytes)
            merged_pdf.insert_pdf(img_pdf)
            
        output_buffer = io.BytesIO()
        merged_pdf.save(output_buffer)
        output_buffer.seek(0)
        return output_buffer

    except Exception as e:
        raise RuntimeError(f"PDF OCR Error: {e}")

# ==============================================================================
# 3. EXTRACT RAW TEXT
# ==============================================================================
def extract_raw_text_logic(uploaded_file, input_type):
    try:
        images = get_images_from_upload(uploaded_file, input_type)
        full_text = ""
        for i, img in enumerate(images):
            # Urdu + English
            text = pytesseract.image_to_string(img, lang='eng+urd')
            full_text += f"\n\n--- PAGE {i+1} ---\n\n{text}"
        return full_text
    except Exception as e:
        raise RuntimeError(f"Text Extraction Error: {e}")