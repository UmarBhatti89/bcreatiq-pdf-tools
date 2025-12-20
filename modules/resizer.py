# modules/resizer.py
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import io

def get_content_bbox(page, threshold_val=250):
    """Page ka colored content detect karke uska Box return karta hai"""
    try:
        # High DPI scan for better detection
        pix = page.get_pixmap(dpi=144)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        gray = img.convert("L")
        
        # Threshold logic
        bw = gray.point(lambda x: 0 if x < threshold_val else 255, '1')
        inverted_bw = ImageOps.invert(bw.convert('L'))
        bbox = inverted_bw.getbbox()
        
        if bbox:
            scale = 72 / 144
            x0, y0, x1, y1 = bbox
            # Safety margin (-2 pixels)
            return fitz.Rect((x0*scale)+2, (y0*scale)+2, (x1*scale)-2, (y1*scale)-2)
        else:
            return page.rect
    except Exception as e:
        print(f"Error detecting content: {e}")
        return page.rect

def process_pdf_resize(input_file, target_w, target_h, mode, threshold_val):
    doc = fitz.open(stream=input_file.read(), filetype="pdf")
    new_doc = fitz.open()

    # Inches to Points (1 inch = 72 points)
    tgt_w_pts = target_w * 72
    tgt_h_pts = target_h * 72

    total_pages = len(doc)

    for i, page in enumerate(doc):
        # Naya blank page target size ka
        new_page = new_doc.new_page(width=tgt_w_pts, height=tgt_h_pts)
        
        # --- LOGIC SELECTION (Fixed Name Matching) ---
        
        # Option 1: Simple Resize (Jo aapke dropdown me "Simple Resize" hai)
        if mode == "Simple Resize" or "Simple" in mode:
            new_page.show_pdf_page(
                new_page.rect, doc, page.number, keep_proportion=True
            )
            
        # Option 2: Force Fit (Jo aapke dropdown me "Force Fit" hai)
        elif mode == "Force Fit" or "Force" in mode:
            src_rect = get_content_bbox(page, threshold_val)
            new_page.show_pdf_page(
                new_page.rect, doc, page.number, keep_proportion=False, clip=src_rect
            )
            
        # Option 3: Smart Center Crop (Same name)
        elif mode == "Smart Center Crop" or "Smart" in mode:
            src_rect = get_content_bbox(page, threshold_val)
            
            # Square/Center Calculation
            width = src_rect.width
            height = src_rect.height
            box_size = min(width, height)
            
            center_x = src_rect.x0 + (width / 2)
            center_y = src_rect.y0 + (height / 2)
            
            clip_rect = fitz.Rect(
                center_x - (box_size / 2),
                center_y - (box_size / 2),
                center_x + (box_size / 2),
                center_y + (box_size / 2)
            )
            clip_rect = clip_rect & src_rect # Safety

            new_page.show_pdf_page(
                new_page.rect, doc, page.number, keep_proportion=True, clip=clip_rect
            )

    output_buffer = io.BytesIO()
    new_doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, total_pages