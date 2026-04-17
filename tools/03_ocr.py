"""
05_ocr.py — OCR text regions -> plain text files
================================================
Runs Tesseract OCR on each text-region PNG from _separated/_text/ and
saves the raw output to _ocr/ for manual correction into _transcribed/.

Language notes:
  - Tok Pisin uses standard Latin script -> Tesseract eng works reasonably well
  - Matukar Panau also uses Latin script (community orthography)
  - OCR output will need human correction; treat it as a first draft

Output structure:
    _ocr/
        DGB1-tambuna22-manam-volcano/
            page_001_text_0.txt
            ...
    _transcribed/          ← copy files here and edit for final versions
        DGB1-tambuna22-manam-volcano/

Usage:
    python tools/05_ocr.py
    python tools/05_ocr.py --story DGB1-tambuna22-manam-volcano
    python tools/05_ocr.py --lang eng+tpi   # if Tok Pisin tessdata available
"""

import argparse
import shutil
from pathlib import Path

import pytesseract
from PIL import Image
from tqdm import tqdm

TEXT_DIR = Path("_separated/_text")
OCR_DIR = Path("_ocr")
TRANSCRIBED_DIR = Path("_transcribed")

# Point pytesseract at the Windows installer's default location.
# Change this path if you installed Tesseract elsewhere.
_TESSERACT_WIN = Path(r"C:\Users\u1018237\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
if _TESSERACT_WIN.exists():
    pytesseract.pytesseract.tesseract_cmd = str(_TESSERACT_WIN)

# Tesseract language string. Tok Pisin (tpi) tessdata can be added if available.
# Download from: https://github.com/tesseract-ocr/tessdata
DEFAULT_LANG = "eng"


def ocr_image(image_path: Path, lang: str) -> str:
    """Run Tesseract on a single image and return the extracted text."""
    img = Image.open(image_path)
    # PSM 6: assume a single uniform block of text
    config = "--psm 6"
    text = pytesseract.image_to_string(img, lang=lang, config=config)
    return text.strip()


def process_story(story: str, lang: str) -> None:
    in_dir = TEXT_DIR / story
    ocr_out_dir = OCR_DIR / story
    transcribed_out_dir = TRANSCRIBED_DIR / story

    ocr_out_dir.mkdir(parents=True, exist_ok=True)
    transcribed_out_dir.mkdir(parents=True, exist_ok=True)

    text_images = sorted(in_dir.glob("*_text_*.png"))
    if not text_images:
        print(f"  No text images found in {in_dir}/")
        return

    for img_path in tqdm(text_images, desc=story, unit="region"):
        text = ocr_image(img_path, lang)
        out_stem = img_path.stem

        # Save raw OCR output
        ocr_path = ocr_out_dir / f"{out_stem}.txt"
        ocr_path.write_text(text, encoding="utf-8")

        # Copy to _transcribed/ only if it doesn't already exist (preserve edits)
        transcribed_path = transcribed_out_dir / f"{out_stem}.txt"
        if not transcribed_path.exists():
            shutil.copy(ocr_path, transcribed_path)

    print(f"  -> {len(text_images)} text regions processed -> {ocr_out_dir}/")
    print(f"  -> Review and correct files in {transcribed_out_dir}/")


def main():
    parser = argparse.ArgumentParser(description="OCR text regions to plain text files.")
    parser.add_argument("--story", type=str, default=None, help="Process one story only")
    parser.add_argument("--lang", type=str, default=DEFAULT_LANG,
                        help=f"Tesseract language string (default: {DEFAULT_LANG})")
    args = parser.parse_args()

    stories = sorted([d.name for d in TEXT_DIR.iterdir() if d.is_dir()])
    if not stories:
        print(f"No stories found in {TEXT_DIR}/. Run 03_separate_ui.py first.")
        return

    for story in stories:
        if args.story and story != args.story:
            continue
        print(f"\nOCR: {story}")
        process_story(story, lang=args.lang)


if __name__ == "__main__":
    main()
