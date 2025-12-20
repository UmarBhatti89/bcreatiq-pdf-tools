# modules/merger.py
import fitz  # PyMuPDF
import io

def merge_pdfs_logic(uploaded_files):
    """
    Multiple uploaded files ko leta hai aur ek single PDF mein jod deta hai.
    """
    merged_doc = fitz.open() # Khali PDF

    for file in uploaded_files:
        # Har upload ki hui file ko read karke open karein
        try:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            merged_doc.insert_pdf(doc) # Main document mein pages insert karein
        except Exception as e:
            print(f"File skip hui (Error): {e}")
        
        # File ko dobara read karne ke liye reset karein (Safety)
        file.seek(0)

    # Output buffer banayen
    output_buffer = io.BytesIO()
    merged_doc.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer