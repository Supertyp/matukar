"""
01_extract.py — PDF → PNG page images
======================================
Extracts every page from each PDF in _raw/ as a high-resolution PNG into _pages/.

Output structure:
    _pages/
        DGB1-tambuna22-manam-volcano/
            page_001.png
            page_002.png
            ...

Usage:
    python tools/01_extract.py
    python tools/01_extract.py --dpi 300 --story DGB1-tambuna22-manam-volcano
"""

import argparse
import re
from pathlib import Path

import fitz  # pymupdf
from tqdm import tqdm

RAW_DIR = Path("_raw")
PAGES_DIR = Path("_pages")


def pdf_to_slug(pdf_path: Path) -> str:
    """Convert a PDF filename to a safe folder name (lowercase, hyphens)."""
    name = pdf_path.stem
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name).strip("-").lower()
    return name


def extract_pdf(pdf_path: Path, out_dir: Path, dpi: int = 300) -> None:
    doc = fitz.open(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    for i, page in enumerate(tqdm(doc, desc=pdf_path.stem, unit="page")):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = out_dir / f"page_{i + 1:03d}.png"
        pix.save(str(out_path))

    page_count = len(doc)
    doc.close()
    print(f"  -> {page_count} pages saved to {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Extract PDF pages to PNG images.")
    parser.add_argument("--dpi", type=int, default=300, help="Resolution (default: 300)")
    parser.add_argument("--story", type=str, default=None, help="Process one story only (folder slug)")
    args = parser.parse_args()

    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {RAW_DIR}/")
        return

    for pdf in pdfs:
        slug = pdf_to_slug(pdf)
        if args.story and slug != args.story:
            continue
        out_dir = PAGES_DIR / slug
        print(f"\nExtracting: {pdf.name}  ->  {out_dir}/")
        extract_pdf(pdf, out_dir, dpi=args.dpi)


if __name__ == "__main__":
    main()
