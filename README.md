# PDF Outline Extraction Solution

## Approach
This solution processes a directory of PDF files and generates a structured outline (headings and subheadings) for each PDF. The approach is as follows:

1. **Title Extraction:**
   - Attempts to extract the document title from PDF metadata.
   - If metadata is missing or unhelpful, it finds the largest text on the first page.
   - As a last resort, it uses the filename as the title.

2. **Outline Extraction:**
   - If the PDF contains an official Table of Contents (TOC), it is used directly.
   - If not, the script analyzes font sizes throughout the document. Text blocks with font sizes significantly larger than the body text are considered headings. These are mapped to heading levels (H1, H2, H3, etc.) based on their relative sizes.

3. **Output:**
   - For each PDF, a JSON file is created in the output directory, containing the extracted title and outline.

## Models and Libraries Used
- **[PyMuPDF (fitz)](https://pymupdf.readthedocs.io/en/latest/):** Used for reading PDF files, extracting text, metadata, and analyzing font sizes.
- **Python Standard Library:**
  - `json` for output serialization
  - `pathlib.Path` for file and directory management
  - `collections.Counter` for font size analysis

## How to Build and Run

### 1. Build the Docker Image
Run the following command in your project directory:

```
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### 2. Run the Docker Container
Assuming you have your input PDFs in a local `input` folder, and want the output in a local `output` folder:

```
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier
```

- The container will automatically process all PDFs from `/app/input` and write JSON results to `/app/output`.
- For each `filename.pdf` in the input, a corresponding `filename.json` will be created in the output.

## Expected Output
- Each output JSON file contains the document title and a list of outline entries (with heading level, text, and page number).
- Example output structure:

```json
{
  "title": "Sample PDF Title",
  "outline": [
    {"level": "H1", "text": "Introduction", "page": 1},
    {"level": "H2", "text": "Background", "page": 2}
  ]
}
```

## Notes
- The script is robust to missing metadata and missing TOC.
- The heading detection threshold can be adjusted via the `HEADING_THRESHOLD_MULTIPLIER` variable in the code.
- All processing is automatic; no manual intervention is required.

---

For any issues, please check the logs or ensure your PDFs are not encrypted or corrupted.
