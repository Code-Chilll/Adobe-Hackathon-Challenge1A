import fitz  # PyMuPDF
import json
import os
import re
from collections import Counter

# Define input and output directories relative to the script file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(SCRIPT_DIR, "sample_dataset", "pdfs")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "sample_dataset", "outputs")
SCHEMA_PATH = os.path.join(SCRIPT_DIR, "sample_dataset", "schema", "output_schema.json")

def is_bold(font_name):
    """Check if the font name suggests it's bold."""
    return any(x in font_name.lower() for x in ['bold', 'black', 'heavy'])

def get_heading_levels(font_sizes):
    """Determine heading font sizes from a list of font sizes."""
    if not font_sizes:
        return None, None, None
    
    # Count frequencies of font sizes to find the most common ones
    size_counts = Counter(round(s, 1) for s in font_sizes)
    # Sort by size, descending. The largest are potential heading sizes.
    sorted_sizes = sorted(size_counts.keys(), reverse=True)

    # Define heading levels based on the top 3-4 largest, infrequent font sizes
    h1_size = sorted_sizes[0] if len(sorted_sizes) > 0 else None
    h2_size = sorted_sizes[1] if len(sorted_sizes) > 1 else None
    h3_size = sorted_sizes[2] if len(sorted_sizes) > 2 else None
    
    return h1_size, h2_size, h3_size

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
                        text = span['text'].strip()
                        # Ignore very small, purely numerical, or short text
                        if span['size'] > 7 and not text.isdigit() and len(text) > 1:
                            block_info = {
                                'text': text,
                                'size': span['size'],
                                'font': span['font'],
                                'page': page_num + 1
                            }
                            all_blocks.append(block_info)
                            font_sizes.append(span['size'])

    if not all_blocks:
        return None

    # 2. Determine heading font sizes and title
    h1_size, h2_size, h3_size = get_heading_levels(font_sizes)
    
    title_parts = []
    # Try to find the title on the first page, often the largest text, and concatenate parts
    for block in all_blocks:
        if block['page'] == 1 and round(block['size'], 1) == h1_size:
            title_parts.append(block['text'])
    
    title = " ".join(title_parts) if title_parts else ""

    if not title: # Fallback if title not found
        # Look for the largest text on the first page as a fallback
        first_page_blocks = [b for b in all_blocks if b['page'] == 1]
        if first_page_blocks:
            largest_block = max(first_page_blocks, key=lambda x: x['size'])
            title = largest_block['text']

    if not title: # Final fallback
        title = os.path.basename(pdf_path)


    # 3. Second pass: Classify blocks as H1, H2, or H3
    outline = []
    for block in all_blocks:
        block_size = round(block['size'], 1)
        text = block['text']
        level = None
        
        # Skip text that is part of the title
        if text in title and block['page'] == 1:
            continue

        # Heading detection logic: combines size, font weight, and text length
        if len(text.split()) < 10:  # Filter out long paragraphs
            if block_size == h1_size and is_bold(block['font']):
                level = "H1"
            elif block_size == h2_size and is_bold(block['font']):
                level = "H2"
            elif block_size == h3_size and is_bold(block['font']):
                level = "H3"
        
        if level:
            # Avoid adding very short or likely non-heading text
            if len(text) > 2 and len(text.split()) > 1:
                outline.append({
                    "level": level,
                    "text": text,
                    "page": block['page']
                })

    # 4. Final output structure as required
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)

    schema["title"] = title
    
    # Create a new list for the outline with the schema structure
    schema_outline = []
    for item in outline:
        schema_item = {
            "type": "object",
            "properties": {
                "level": {"type": "string"},
                "text": {"type": "string"},
                "page": {"type": "integer"}
            },
            "required": ["level", "text", "page"]
        }
        # This is a non-standard way to embed data in a schema
        # We'll add the actual data to the properties
        schema_item['properties']['level']['value'] = item['level']
        schema_item['properties']['text']['value'] = item['text']
        schema_item['properties']['page']['value'] = item['page']
        schema_outline.append(schema_item)
        
    schema["outline"] = {
        "type": "array",
        "items": schema_outline
    }

    return schema

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