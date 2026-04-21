# modules/editor.py
import fitz  # PyMuPDF
import io
from PIL import Image
import sys
import pytesseract


# Check karega ke operating system konsa hai
if sys.platform.startswith('win'):
    # Agar Windows hai (Aapka Local PC), toh yeh path use kare
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # Agar Linux hai (Streamlit Cloud), toh kuch declare karne ki zaroorat nahi
    # Tesseract packages.txt ke zariye automatically pick ho jayega
    pass

def get_dominant_color(page, rect):
    """Background color detect karta hai taake patch match kare"""
    try:
        pix = page.get_pixmap(clip=rect)
        if pix.width < 1 or pix.height < 1:
            return (1, 1, 1) # Default White
        r, g, b = pix.pixel(0, 0)
        return (r/255, g/255, b/255)
    except:
        return (1, 1, 1)

def remove_text_logic(uploaded_file, text_to_remove=None, remove_all=False, use_ocr=False, custom_color=None):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    pages_modified = 0

    for page in doc:
        hits = []
        
        # ==========================================
        # 1. EDITABLE TEXT REMOVAL (Fast & Clean)
        # ==========================================
        if remove_all:
            # Agar sab hatana hai, to hum "Search" nahi karenge,
            # balki saare "Text Blocks" uthayenge.
            blocks = page.get_text("blocks")
            for b in blocks:
                # b[:4] coordinates hote hain (x0, y0, x1, y1)
                hits.append(fitz.Rect(b[:4]))
        
        elif text_to_remove:
            # Sirf specific word dhoondo
            text_instances = page.search_for(text_to_remove)
            hits.extend(text_instances)

        # ==========================================
        # 2. OCR TEXT REMOVAL (Images / Scanned)
        # ==========================================
        if use_ocr:
            try:
                # High Quality Image scan
                pix = page.get_pixmap(dpi=200) # 200 DPI is faster than 300
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # OCR Data nikalein
                ocr_data = pytesseract.image_to_data(pil_image, output_type=pytesseract.Output.DICT)
                
                n_boxes = len(ocr_data['text'])
                for i in range(n_boxes):
                    word = ocr_data['text'][i].strip()
                    conf = int(ocr_data['conf'][i])
                    
                    # Logic: 
                    # Agar Remove All hai -> Har wo cheez jo text lagti hai (conf > 40)
                    # Agar Specific hai -> Sirf matching word
                    
                    if conf > 40 and word: # Sirf valid words
                        should_remove = False
                        
                        if remove_all:
                            should_remove = True
                        elif text_to_remove and text_to_remove.lower() in word.lower():
                            should_remove = True
                            
                        if should_remove:
                            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
                            
                            # Scaling (Image -> PDF coords)
                            scale_x = page.rect.width / pil_image.width
                            scale_y = page.rect.height / pil_image.height
                            
                            rect = fitz.Rect(x * scale_x, y * scale_y, (x + w) * scale_x, (y + h) * scale_y)
                            hits.append(rect)
            except Exception as e:
                print(f"OCR Error: {e}")

        # ==========================================
        # 3. APPLY REDACTION (Hide Content)
        # ==========================================
        if hits:
            pages_modified += 1
            for rect in hits:
                if custom_color:
                    fill_color = custom_color
                else:
                    fill_color = get_dominant_color(page, rect)

                # Box draw karein
                page.draw_rect(rect, color=fill_color, fill=fill_color)

    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, pages_modified
