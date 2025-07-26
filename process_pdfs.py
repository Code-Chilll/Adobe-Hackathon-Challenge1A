import fitz  # PyMuPDF
import json
import os
import re
from collections import Counter

# Define input and output directories as specified in the hackathon brief 
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def is_bold(font_name):
    """Check if the font name suggests it's bold."""
    return any(x in font_name.lower() for x in ['bold', 'black', 'heavy'])

def extract_outline(pdf_path):
    """
    Extracts the title and a hierarchical outline (H1, H2, H3) from a PDF.
    
    This function analyzes text properties like font size and style to identify
    structural elements of the document.
    """
    doc = fitz.open(pdf_path)
    all_blocks = []
    font_sizes = []

    # 1. First pass: Extract all text blocks and font sizes
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Ignore very small text and purely numerical text
                        if span['size'] > 7 and not span['text'].strip().isdigit():
                            all_blocks.append({
                                'text': span['text'].strip(),
                                'size': span['size'],
                                'font': span['font'],
                                'page': page_num + 1
                            })
                            font_sizes.append(span['size'])

    if not font_sizes:
        return None

    # 2. Determine heading font sizes
    # Count frequencies of font sizes to find the most common ones
    size_counts = Counter(round(s, 1) for s in font_sizes)
    # Sort by size, descending. The largest are potential heading sizes.
    sorted_sizes = sorted(size_counts.keys(), reverse=True)

    # Define heading levels based on the top 3-4 largest, infrequent font sizes
    h1_size = sorted_sizes[0] if len(sorted_sizes) > 0 else None
    h2_size = sorted_sizes[1] if len(sorted_sizes) > 1 else None
    h3_size = sorted_sizes[2] if len(sorted_sizes) > 2 else None
    
    title = ""
    outline = []

    # 3. Second pass: Classify blocks as Title, H1, H2, or H3
    # Try to find the title on the first page, often the largest text
    for block in all_blocks:
        if block['page'] == 1 and round(block['size'], 1) == h1_size:
            title = block['text']
            break
    if not title: # Fallback if title not found
        title = os.path.basename(pdf_path)

    for block in all_blocks:
        block_size = round(block['size'], 1)
        level = None
        
        # Heading detection logic: combines size and font weight 
        if block_size == h1_size and is_bold(block['font']):
             # Avoid re-adding the title as an H1 heading
            if block['text'] != title:
                level = "H1"
        elif block_size == h2_size and is_bold(block['font']):
            level = "H2"
        elif block_size == h3_size and is_bold(block['font']):
            level = "H3"
        
        if level:
            outline.append({
                "level": level,
                "text": block['text'],
                "page": block['page']
            })

    # 4. Final output structure as required [cite: 43]
    result = {
        "title": title,
        "outline": outline
    }
    return result

def main():
    """
    Main function to process all PDF files in the input directory.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            output_data = extract_outline(pdf_path)

            if output_data:
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                print(f"Processed {filename} -> {output_filename}")

if __name__ == "__main__":
    main()