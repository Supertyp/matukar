"""
06_assemble.py — Assemble final book PDF
=========================================
Combines enhanced drawings and corrected transcriptions into a
print-ready PDF with the Matukar Panau community font.

Layout per story page:
  - Full-width drawing (centred, with padding)
  - Caption text below in Matukarjobo-Regular font

Output:
    _output/
        DGB1-tambuna22-manam-volcano.pdf
        ...

Usage:
    python tools/06_assemble.py
    python tools/06_assemble.py --story DGB1-tambuna22-manam-volcano
    python tools/06_assemble.py --page-size A4   # A4 or LETTER
"""

import argparse
import json
import re
from pathlib import Path

from fpdf import FPDF
from PIL import Image

ENHANCED_DIR = Path("_enhanced")
TRANSCRIBED_DIR = Path("_transcribed")
DRAWINGS_META_DIR = Path("_separated/_drawings")  # JSON sidecar files
OUTPUT_DIR = Path("_output")
FONT_DIR = Path("font")

FONT_NAME = "MatukarJobo"
FONT_FILE = FONT_DIR / "Matukarjobo-Regular.ttf"

PAGE_SIZES = {
    "A4": (210, 297),      # mm
    "LETTER": (215.9, 279.4),
}

MARGIN = 15  # mm
CAPTION_SIZE = 11  # pt
TITLE_SIZE = 16  # pt


class BookPDF(FPDF):
    def __init__(self, page_size: tuple[float, float]):
        super().__init__(unit="mm", format=page_size)
        self.set_auto_page_break(auto=True, margin=MARGIN)
        self._register_font()

    def _register_font(self):
        if not FONT_FILE.exists():
            print(f"Warning: font not found at {FONT_FILE}, falling back to Helvetica.")
            return
        self.add_font(FONT_NAME, style="", fname=str(FONT_FILE))

    def story_title_page(self, title: str):
        self.add_page()
        self.set_font(FONT_NAME if FONT_FILE.exists() else "Helvetica", size=TITLE_SIZE)
        self.ln(40)
        self.cell(0, 10, title.replace("-", " ").title(), align="C", new_x="LMARGIN", new_y="NEXT")

    def drawing_page(self, drawing_path: Path, caption_text: str):
        self.add_page()
        usable_w = self.w - 2 * MARGIN
        usable_h = self.h - 2 * MARGIN

        # Reserve space for caption
        caption_h = 20  # mm estimate
        drawing_h = usable_h - caption_h

        # Scale drawing to fit
        with Image.open(drawing_path) as img:
            img_w, img_h = img.size
        aspect = img_w / img_h
        draw_w = min(usable_w, drawing_h * aspect)
        draw_h = draw_w / aspect

        x = MARGIN + (usable_w - draw_w) / 2
        self.image(str(drawing_path), x=x, y=MARGIN, w=draw_w, h=draw_h)

        # Caption below
        caption_y = MARGIN + draw_h + 5
        self.set_y(caption_y)
        font = FONT_NAME if FONT_FILE.exists() else "Helvetica"
        self.set_font(font, size=CAPTION_SIZE)
        self.multi_cell(0, 6, caption_text, align="C")


def load_page_pairs(story: str) -> list[tuple[Path, str]]:
    """
    Return a list of (drawing_path, caption_text) pairs for a story,
    ordered by page number.
    """
    enhanced_dir = ENHANCED_DIR / story
    transcribed_dir = TRANSCRIBED_DIR / story
    meta_dir = DRAWINGS_META_DIR / story

    pairs = []
    json_files = sorted(meta_dir.glob("*.json"))

    for json_path in json_files:
        with open(json_path) as f:
            regions = json.load(f)

        drawings = [r for r in regions if r["label"] == "drawing"]
        texts = [r for r in regions if r["label"] == "text"]

        for i, drawing_region in enumerate(drawings):
            drawing_file = enhanced_dir / drawing_region["file"]
            if not drawing_file.exists():
                # Fall back to unenhanced version
                drawing_file = Path("_separated/_drawings") / story / drawing_region["file"]

            # Match caption by index (first text region -> first drawing, etc.)
            caption = ""
            if i < len(texts):
                text_stem = Path(texts[i]["file"]).stem
                caption_path = transcribed_dir / f"{text_stem}.txt"
                if caption_path.exists():
                    caption = caption_path.read_text(encoding="utf-8").strip()

            if drawing_file.exists():
                pairs.append((drawing_file, caption))

    return pairs


def assemble_story(story: str, page_size: tuple[float, float]) -> Path:
    pairs = load_page_pairs(story)
    if not pairs:
        print(f"  No drawing/caption pairs found for {story}. Run earlier steps first.")
        return None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{story}.pdf"

    pdf = BookPDF(page_size=page_size)
    pdf.story_title_page(story)

    for drawing_path, caption in pairs:
        pdf.drawing_page(drawing_path, caption)

    pdf.output(str(out_path))
    print(f"  -> {len(pairs)} pages assembled -> {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Assemble book PDF from drawings and transcriptions.")
    parser.add_argument("--story", type=str, default=None, help="Assemble one story only")
    parser.add_argument("--page-size", choices=PAGE_SIZES.keys(), default="A4")
    args = parser.parse_args()

    page_size = PAGE_SIZES[args.page_size]
    stories = sorted([d.name for d in ENHANCED_DIR.iterdir() if d.is_dir()])

    if not stories:
        print(f"No stories found in {ENHANCED_DIR}/. Complete earlier pipeline steps first.")
        return

    for story in stories:
        if args.story and story != args.story:
            continue
        print(f"\nAssembling: {story}")
        assemble_story(story, page_size)


if __name__ == "__main__":
    main()
