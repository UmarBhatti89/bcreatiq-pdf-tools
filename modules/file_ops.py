# modules/file_ops.py
import fitz  # PyMuPDF
import io
import zipfile

def parse_page_string(page_str, total_pages=None):
    """
    User input "1, 3-5" ko list [0, 2, 3, 4] mein convert karta hai.
    """
    pages = []
    if not page_str.strip():
        return []
        
    try:
        parts = page_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                # Range Logic
                if start > end: start, end = end, start # Swap if 5-1
                pages.extend(range(start - 1, end))
            else:
                pages.append(int(part) - 1)
        
        # Validation: Remove invalid pages (jo total se zyada hon)
        if total_pages:
            pages = [p for p in pages if 0 <= p < total_pages]
            
        return sorted(list(set(pages))) # Remove duplicates & Sort
    except ValueError:
        return []

# --- 1. MERGE ---
def merge_pdfs_logic(uploaded_files):
    merged_doc = fitz.open()
    for file in uploaded_files:
        file.seek(0)
        doc = fitz.open(stream=file.read(), filetype="pdf")
        merged_doc.insert_pdf(doc)
    
    output = io.BytesIO()
    merged_doc.save(output)
    output.seek(0)
    return output

# --- 2. SPLIT (Custom Range) ---
def split_pdf_logic(uploaded_file, page_range_str):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    new_doc = fitz.open()
    
    selected_pages = parse_page_string(page_range_str, len(doc))
    
    if not selected_pages:
        return None

    for p_num in selected_pages:
        new_doc.insert_pdf(doc, from_page=p_num, to_page=p_num)

    output = io.BytesIO()
    new_doc.save(output)
    output.seek(0)
    return output

# --- 3. SPLIT ALL (Burst Mode - ZIP Output) ---
def split_all_pages_logic(uploaded_file):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(len(doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            
            # Save individual PDF to memory
            pdf_bytes = new_doc.write()
            
            # Add to Zip
            zf.writestr(f"page_{i+1}.pdf", pdf_bytes)
            new_doc.close()

    zip_buffer.seek(0)
    return zip_buffer

# --- 4. REORDER (Full List) ---
def reorder_pdf_logic(uploaded_file, order_str):
    # User manually likhta hai: "2, 1, 3"
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    # Is function me hum 'parse_page_string' use nahi karte kyunke
    # user ko allow hai ke wo pages repeat kare ya aage peeche kare (No Sort)
    try:
        parts = order_str.split(',')
        new_order = [int(p.strip())-1 for p in parts]
    except:
        return None

    new_doc = fitz.open()
    for p_num in new_order:
        if 0 <= p_num < len(doc):
            new_doc.insert_pdf(doc, from_page=p_num, to_page=p_num)
            
    output = io.BytesIO()
    new_doc.save(output)
    output.seek(0)
    return output

# --- 5. MOVE PAGE (Smart Reorder) ---
def move_page_logic(uploaded_file, page_to_move, new_position):
    """
    Page X ko utha kar Position Y par rakhta hai, baaki adjust hojate hain.
    Example: Move Page 5 to Position 1.
    """
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    total_pages = len(doc)
    
    # 0-based index conversion
    src_idx = page_to_move - 1
    dest_idx = new_position - 1
    
    if not (0 <= src_idx < total_pages) or not (0 <= dest_idx < total_pages):
        return None
        
    # Page list banao: [0, 1, 2, 3...]
    page_list = list(range(total_pages))
    
    # List manipulation
    page_list.pop(src_idx) # Remove from old spot
    page_list.insert(dest_idx, src_idx) # Insert at new spot
    
    # Rebuild PDF
    new_doc = fitz.open()
    for p_num in page_list:
        new_doc.insert_pdf(doc, from_page=p_num, to_page=p_num)
        
    output = io.BytesIO()
    new_doc.save(output)
    output.seek(0)
    return output

# --- 6. ROTATE (Selective) ---
def rotate_pdf_logic(uploaded_file, rotation_angle, page_str=""):
    uploaded_file.seek(0)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    
    # Agar user ne kuch nahi likha to matlab "ALL PAGES"
    target_pages = []
    if page_str.strip():
        target_pages = parse_page_string(page_str, len(doc))
    else:
        target_pages = range(len(doc)) # All pages

    for i in target_pages:
        # PyMuPDF rotation add karta hai (Existing + New)
        # Hum set_rotation use karenge taake fixed value ho
        doc[i].set_rotation(rotation_angle)

    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer