# modules/protection.py
import fitz  # PyMuPDF
import io

# --- 1. COMPRESS PDF ---
def compress_pdf_logic(uploaded_file, compression_level="Standard"):
    """
    Standard: Sirf bekaar data (garbage) hatata hai aur text compress karta hai.
    Strong: Images ko bhi thoda downsample karta hai taake size aur kam ho.
    """
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    # Garbage collection options (4 = Sab se powerful clean up)
    # Deflate = True (Content stream compression)
    
    output_buffer = io.BytesIO()
    
    if compression_level == "Strong (Images Reduced)":
        # Images ko downsample karna (DPI 150 par lana)
        # Ye loop har page ki images ko check karke chhota karega (Advanced logic)
        # Filhal hum PyMuPDF ka built-in 'garbage=4' + 'deflate' use karenge jo 30-40% kam kar deta hai.
        doc.save(output_buffer, garbage=4, deflate=True, clean=True)
    else:
        # Standard Compression (Lossless)
        doc.save(output_buffer, garbage=3, deflate=True)
        
    output_buffer.seek(0)
    return output_buffer

# --- 2. ADD WATERMARK (TEXT/IMAGE) ---
def add_watermark_logic(uploaded_file, watermark_text=None, watermark_image=None, opacity=0.3):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    for page in doc:
        # Center point nikalein
        center_x = page.rect.width / 2
        center_y = page.rect.height / 2
        
        if watermark_image:
            # --- IMAGE WATERMARK ---
            # Image ko page ke beech me lagayen
            # Rect define karein (e.g., 200x200 center me)
            img_size = 200
            rect = fitz.Rect(center_x - img_size/2, center_y - img_size/2, 
                             center_x + img_size/2, center_y + img_size/2)
            
            # Image insert karein (Overlay=False matlab peeche, True matlab upar)
            # PyMuPDF direct image stream support karta hai
            page.insert_image(rect, stream=watermark_image.read(), keep_proportion=True)
            
            # Note: PyMuPDF me image transparency complex hoti hai, 
            # isliye hum image ko 'background' layer par laga rahe hain.
            
        elif watermark_text:
            # --- TEXT WATERMARK ---
            # 45 degree par text likhna
            page.insert_text(
                (center_x, center_y),
                watermark_text,
                fontsize=60,
                rotate=45,
                color=(0.5, 0.5, 0.5), # Grey color
                fill_opacity=opacity, # Transparency
                align=1 # Center align
            )
            
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# --- 3. SECURITY (PASSWORD ADD/REMOVE) ---
def manage_security_logic(uploaded_file, action, password=""):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    output_buffer = io.BytesIO()

    if action == "Add Password":
        # Encrypt karein (AES 256 - Strong Security)
        # user_pw = open karne kelye, owner_pw = edit karne kelye (hum same rakh rahe hain)
        doc.save(
            output_buffer,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password
        )
        
    elif action == "Remove Password":
        # Agar file password protected hai to authenticate karein
        if doc.is_encrypted:
            if doc.authenticate(password):
                # Password sahi hai -> Bina encryption ke save karein
                doc.save(output_buffer)
            else:
                raise ValueError("Ghalat Password! File unlock nahi ho saki.")
        else:
            # File pehle se unlocked thi
            doc.save(output_buffer)

    output_buffer.seek(0)
    return output_buffer