# Matukar — Notebook Digitisation Pipeline

A Python workflow for digitising handmade artist notebooks containing drawings and handwritten text in **Tok Pisin** and **Matukar Panau** — an endangered Austronesian language with a community-designed orthography and font.

The pipeline takes raw scanned PDFs of notebook pages and produces print-ready book PDFs with drawings and typeset captions. It is designed to be reusable for similar projects involving handmade notebooks, endangered-language materials, or community art archives.

---

## Pipeline overview

```
_raw/  (source PDFs)
  |
  v  01_extract.py        — extract pages as high-res PNGs
_pages/
  |
  v  02_separate_ui.py    — browser UI: mark drawing vs text regions per page
_separated/
  |-- _drawings/          — manually process and copy to _enhanced/
  |-- _text/
  |
  v  03_ocr.py            — Tesseract OCR on text regions -> draft text files
_ocr/
  |
  v  04_review_ui.py      — browser UI: review and correct transcriptions
_transcribed/
  |
  v  05_assemble.py       — combine _enhanced/ drawings + _transcribed/ text -> PDF
_output/
```

---

## Quickstart

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR

Tesseract must be installed separately from the Python package.

**Windows** — download the installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and run it. Then set the path in `tools/03_ocr.py`:

```python
_TESSERACT_WIN = Path(r"C:\Users\<you>\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
```

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 3. Add your PDFs

Drop story PDFs into `_raw/`. The pipeline uses the filename (lowercased, spaces → hyphens) as the story folder name throughout.

```
_raw/
  DGB1-tambuna22-manam-volcano.pdf
  DGB1-tambuna23-grass-skirt-bandicoot.pdf
  ...
```

### 4. Run the pipeline

```bash
# Step 1 — extract all PDFs to PNG pages (300 DPI)
python tools/01_extract.py

# Step 2 — mark drawing and text regions in browser (opens at http://localhost:5000)
python tools/02_separate_ui.py

# -- manually enhance drawings from _separated/_drawings/ and copy to _enhanced/ --

# Step 3 — OCR all text regions
python tools/03_ocr.py

# Step 4 — review and correct transcriptions in browser (opens at http://localhost:5001)
python tools/04_review_ui.py

# Step 5 — assemble final book PDFs
python tools/05_assemble.py
```

To process a single story at any step:
```bash
python tools/01_extract.py --story dgb1-tambuna22-manam-volcano
```

---

## Folder structure

| Folder | Contents | Committed to git |
|---|---|---|
| `_raw/` | Source PDFs | No |
| `_pages/` | Extracted page images (temporary) | No |
| `_separated/_drawings/` | Cropped drawing regions | No |
| `_separated/_text/` | Cropped text regions | No |
| `_enhanced/` | Manually processed drawings for assembly | No |
| `_ocr/` | Raw Tesseract output — do not edit | No |
| `_transcribed/` | Corrected transcriptions — edit these | No |
| `_output/` | Final assembled book PDFs | No |
| `tools/` | Pipeline scripts | Yes |
| `font/` | Matukarjobo-Regular community font | Yes |

All content folders contain a `.gitkeep` so the folder structure is preserved in version control without committing any images, PDFs, or text files.

---

## Languages

- **Tok Pisin** — PNG creole, Latin script. Tesseract `eng` produces usable drafts.
- **Matukar Panau** — endangered Austronesian language. Latin script with community orthography. Font: **Matukarjobo-Regular** (included in `font/`). OCR drafts require manual correction in the review UI.

---

## Requirements

See [requirements.txt](requirements.txt).

| Package | Purpose |
|---|---|
| `pymupdf` | PDF -> high-res PNG extraction |
| `Pillow` | Image I/O |
| `pytesseract` | Tesseract OCR wrapper |
| `flask` | Browser-based UI tools |
| `fpdf2` | Book PDF assembly with custom font support |
| `tqdm` | Progress bars |

---

## Adapting for other projects

1. Replace the PDFs in `_raw/`
2. Update the Tesseract `--lang` flag in `tools/03_ocr.py` for your languages
3. Update the font path in `tools/05_assemble.py` if using a different typeface

Issues and pull requests welcome.

---

## Acknowledgements

The drawings in this project are the original work of a Matukar Panau community artist. The Matukarjobo font was designed by the Matukar Panau language community.
