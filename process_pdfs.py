
import fitz  # PyMuPDF
import json
from pathlib import Path
from collections import Counter

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")

HEADING_THRESHOLD_MULTIPLIER = 1.2


def discover_title(doc, pdf_path):
    """
    Extracts a PDF's title using metadata, first page, or filename.
    """
    # Strategy 1: Check the metadata property.
    if doc.metadata and doc.metadata.get('title'):
        title_from_meta = doc.metadata['title'].strip()
        # Make sure the title is meaningful before accepting it.
        if title_from_meta and len(title_from_meta) > 5 and 'untitled' not in title_from_meta.lower():
            return title_from_meta

    # Strategy 2: Find the largest font on the first page.
    try:
        first_page = doc[0]
        blocks = first_page.get_text("dict", sort=True)["blocks"]
        if blocks:
            max_font_size = 0
            title_candidate = ""
            # A quick loop to find the text with the biggest font size.
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        if "spans" in line and line["spans"]:
                            for span in line["spans"]:
                                if span["size"] > max_font_size:
                                    max_font_size = span["size"]
                                    title_candidate = span["text"]
            
            title_candidate = title_candidate.strip()
            # A final check to make sure we didn't just grab a page number.
            if len(title_candidate) > 4 and not title_candidate.isnumeric():
                return title_candidate
    except Exception:
        # If anything goes wrong here, it's not critical. Just move on.
        pass

    # Strategy 3: When all else fails, use the filename.
    return pdf_path.stem.replace('_', ' ').replace('-', ' ').title()

def create_outline_from_scratch(doc):
    """
    Generates an outline by analyzing font sizes if no official outline exists.
    """
    print("No official outline found. Building one from scratch...")
    outline = []
    
    style_profile = Counter()
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line and line["spans"]:
                        # We only care about the size for this profiling step.
                        font_size = round(line["spans"][0]["size"])
                        style_profile[font_size] += 1

    if not style_profile:
        return [] # Can't do anything with an empty document.

    body_font_size = style_profile.most_common(1)[0][0]
    
    heading_sizes = sorted([size for size in style_profile if size > body_font_size * HEADING_THRESHOLD_MULTIPLIER], reverse=True)
    
    style_map = {size: level + 1 for level, size in enumerate(heading_sizes)}

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line and line["spans"]:
                        span = line["spans"][0]
                        font_size = round(span["size"])
                        
                        if font_size in style_map:
                            text = span["text"].strip()
                            
                            if len(text) > 2 and not text.isnumeric():
                                heading_level = f"H{style_map[font_size]}"
                                outline.append({
                                    "level": heading_level,
                                    "text": text,
                                    "page": page_num + 1
                                })
    return outline


def analyze_single_pdf(pdf_path):
    """
    Processes a single PDF file: extracts title and outline, saves as JSON.
    """
    print(f"Processing {pdf_path.name}...")
    doc = None
    try:
        doc = fitz.open(pdf_path)
        
        title = discover_title(doc, pdf_path)

        table_of_contents = doc.get_toc()
        
        outline = []
        if table_of_contents:
            outline = [
                {"level": f"H{level}", "text": str(text), "page": int(page)}
                for level, text, page in table_of_contents
            ]
        else:
            outline = create_outline_from_scratch(doc)

        final_json = {"title": title, "outline": outline}
        
        output_filename = OUTPUT_DIR / f"{pdf_path.stem}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, indent=4, ensure_ascii=False)
        print(f"Successfully generated {output_filename.name}")

    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}")
    finally:
        if doc:
            doc.close()

def run_batch_processor():
    """Finds and processes all PDF files in the input directory."""
    print("Starting up the PDF Processor...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in the '{INPUT_DIR}' directory.")
        return
    print(f"Found {len(pdf_files)} PDF(s) to process.")
    for pdf_file in pdf_files:
        analyze_single_pdf(pdf_file)
    print("All done! Check the output folder for your JSON files.")

# --- Script Execution ---
if __name__ == "__main__":
    run_batch_processor()