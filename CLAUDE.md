# CLAUDE.md — Project context for Claude Code

## What this project is

A pipeline for digitising handmade notebooks from the Matukar Panau language community in Papua New Guinea. The notebooks contain drawings by a local artist and text in Tok Pisin and Matukar Panau (an endangered language with a community-designed font).

The goal is to produce print-ready book PDFs that can be published and shared with the community.

## Pipeline steps

| Script | Input | Output |
|---|---|---|
| `tools/01_extract.py` | `_raw/*.pdf` | `_pages/<story>/page_NNN.png` |
| `tools/02_separate_ui.py` | `_pages/` | `_separated/_drawings/` + `_separated/_text/` + JSON sidecars |
| `tools/03_ocr.py` | `_separated/_text/` | `_ocr/` (raw) + `_transcribed/` (copy for editing) |
| `tools/04_review_ui.py` | `_ocr/` + `_separated/_text/` + `_separated/_drawings/` | `_transcribed/` |
| `tools/05_assemble.py` | `_enhanced/` + `_transcribed/` + `_separated/_drawings/*.json` | `_output/<story>.pdf` |

The `_enhanced/` folder is populated manually — the user crops and processes drawings from `_separated/_drawings/` and places results there.

## Key design decisions

- **Flask, not Gradio** — the two browser UIs (`02_separate_ui.py`, `04_review_ui.py`) use Flask + vanilla JS canvas. Gradio was tried first but `<script>` tags injected via `innerHTML` are silently ignored by browsers, breaking canvas interactivity.
- **Normalised coordinates** — bounding boxes in JSON sidecars are stored as floats 0–1 (relative to image size) so they are resolution-independent.
- **No content in git** — all images, PDFs, and text files are gitignored. Only the folder structure (`.gitkeep`), scripts, font, and docs are committed.
- **Tesseract path** — on Windows, `tools/03_ocr.py` sets `pytesseract.pytesseract.tesseract_cmd` explicitly because the installer does not add Tesseract to PATH by default. The path is hardcoded to the user's local install.
- **Font** — the Matukarjobo-Regular font (`.ttf` + `.otf`) is included in `font/` and loaded by `fpdf2` during assembly.

## Folder layout

```
_raw/                   source PDFs (gitignored)
_pages/                 extracted page PNGs — temporary, safe to delete (gitignored)
_separated/
  _drawings/            cropped drawing regions + JSON sidecars (gitignored)
  _text/                cropped text regions (gitignored)
_enhanced/              manually processed drawings ready for assembly (gitignored)
_ocr/                   raw Tesseract output — do not edit (gitignored)
_transcribed/           corrected transcriptions — final captions (gitignored)
_output/                assembled book PDFs (gitignored)
font/                   Matukarjobo-Regular (.ttf + .otf) — committed
tools/                  pipeline scripts — committed
```

## Running the tools

Python is via Anaconda on Windows:
```
C:\Users\u1018237\AppData\Local\anaconda3\python.exe tools/<script>.py
```

Tesseract is installed at:
```
C:\Users\u1018237\AppData\Local\Programs\Tesseract-OCR\
```

The two Flask UIs open automatically in the browser:
- `02_separate_ui.py` → http://localhost:5000
- `04_review_ui.py`   → http://localhost:5001
