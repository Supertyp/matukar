"""
05_review_ui.py — OCR review and correction tool
=================================================
Side-by-side view of the text region image and the OCR output.
Edit the text and save to _transcribed/.

Reads from  : _ocr/<story>/
              _separated/_text/<story>/   (images)
              _separated/_drawings/<story>/ (drawing for context, if available)
Saves to    : _transcribed/<story>/

Usage:
    python tools/05_review_ui.py
    python tools/05_review_ui.py --story dgb1-tambuna22-manam-volcano
    python tools/05_review_ui.py --port 5001
"""

import argparse
import json
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_file

OCR_DIR          = Path("_ocr")
TEXT_IMG_DIR     = Path("_separated/_text")
DRAWING_IMG_DIR  = Path("_separated/_drawings")
TRANSCRIBED_DIR  = Path("_transcribed")

app = Flask(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def get_stories():
    return sorted([d.name for d in OCR_DIR.iterdir() if d.is_dir()])


def get_regions(story: str) -> list[dict]:
    """
    Return sorted list of region dicts for a story.
    Each dict: {stem, txt_img, drawing_img (or None), ocr_text, transcribed_text}
    """
    text_img_dir = TEXT_IMG_DIR / story
    ocr_dir      = OCR_DIR / story
    trans_dir    = TRANSCRIBED_DIR / story
    draw_dir     = DRAWING_IMG_DIR / story

    regions = []
    for img_path in sorted(text_img_dir.glob("*_text_*.png")):
        stem      = img_path.stem          # e.g. page_003_text_0
        ocr_path  = ocr_dir  / f"{stem}.txt"
        trans_path = trans_dir / f"{stem}.txt"

        ocr_text  = ocr_path.read_text(encoding="utf-8").strip() if ocr_path.exists() else ""
        saved_text = trans_path.read_text(encoding="utf-8").strip() if trans_path.exists() else ocr_text

        # Try to find matching drawing (same page number)
        page_part   = "_".join(stem.split("_")[:2])   # e.g. page_003
        draw_idx    = stem.split("_")[-1]              # e.g. 0
        draw_path   = draw_dir / f"{page_part}_drawing_{draw_idx}.png"
        draw_name   = draw_path.name if draw_path.exists() else None

        regions.append({
            "stem":       stem,
            "img":        img_path.name,
            "drawing":    draw_name,
            "ocr":        ocr_text,
            "text":       saved_text,
            "saved":      trans_path.exists(),
        })
    return regions


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML_PAGE


@app.route("/api/stories")
def api_stories():
    return jsonify(get_stories())


@app.route("/api/regions/<story>")
def api_regions(story):
    return jsonify(get_regions(story))


@app.route("/api/text_image/<story>/<filename>")
def api_text_image(story, filename):
    return send_file(str((TEXT_IMG_DIR / story / filename).resolve()), mimetype="image/png")


@app.route("/api/drawing_image/<story>/<filename>")
def api_drawing_image(story, filename):
    return send_file(str((DRAWING_IMG_DIR / story / filename).resolve()), mimetype="image/png")


@app.route("/api/save", methods=["POST"])
def api_save():
    data  = request.get_json()
    story = data["story"]
    stem  = data["stem"]
    text  = data["text"]
    out_dir = TRANSCRIBED_DIR / story
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.txt").write_text(text, encoding="utf-8")
    return jsonify({"ok": True})


# ── HTML page ─────────────────────────────────────────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Matukar — Text Review</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:sans-serif;background:#1a1a1a;color:#ddd;
       display:flex;flex-direction:column;height:100vh;padding:12px;gap:8px;overflow:hidden}
  h2{font-size:17px;flex-shrink:0}
  .topbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;flex-shrink:0}
  select,button{padding:6px 12px;border-radius:4px;border:1px solid #555;
    background:#2c2c2c;color:#ddd;cursor:pointer;font-size:13px}
  button:hover{background:#3a3a3a}
  .primary{background:#1a5fb4!important;border-color:#1a5fb4!important}
  .green{background:#2d6a2d!important;border-color:#2d6a2d!important}
  #status{font-size:12px;color:#aaa;flex-shrink:0;min-height:14px}

  /* three-column layout */
  .main{display:flex;gap:10px;flex:1;min-height:0}

  /* col 1: region list */
  .region-list{width:170px;flex-shrink:0;background:#222;border:1px solid #3a3a3a;
    border-radius:6px;overflow-y:auto;display:flex;flex-direction:column}
  .region-list-header{font-size:11px;color:#777;padding:8px 10px;
    border-bottom:1px solid #333;flex-shrink:0;text-transform:uppercase;letter-spacing:.05em}
  .region-item{padding:7px 10px;font-size:12px;cursor:pointer;border-bottom:1px solid #2a2a2a;
    display:flex;align-items:center;gap:6px;line-height:1.3}
  .region-item:hover{background:#2c2c2c}
  .region-item.active{background:#1a3a5a;color:#fff}
  .region-item .tick{color:#5c5;font-size:11px;flex-shrink:0}
  .region-item .lbl{color:#888;font-size:10px}

  /* col 2: images */
  .images{width:35%;flex-shrink:0;display:flex;flex-direction:column;gap:8px;overflow-y:auto}
  .img-box{background:#2a2a2a;border:1px solid #444;border-radius:4px;padding:8px}
  .img-box label{font-size:11px;color:#777;margin-bottom:4px;display:block}
  .img-box img{width:100%;display:block;border-radius:2px}

  /* col 3: editor */
  .editor-col{display:flex;flex-direction:column;gap:8px;flex:1;min-height:0}
  .ocr-ref{background:#1e1e1e;border:1px solid #383838;border-radius:4px;padding:8px;
    font-size:12px;color:#666;white-space:pre-wrap;overflow-y:auto;
    max-height:120px;flex-shrink:0;font-family:monospace}
  .ocr-ref-label{font-size:10px;color:#555;margin-bottom:3px;text-transform:uppercase}
  textarea{flex:1;background:#2c2c2c;color:#eee;border:1px solid #555;
    border-radius:4px;padding:10px;font-size:15px;line-height:1.7;
    resize:none;font-family:inherit;min-height:0}
  textarea:focus{outline:none;border-color:#4a90d9}
  .nav{display:flex;gap:6px;align-items:center;flex-shrink:0}
  .dirty-dot{width:8px;height:8px;border-radius:50%;background:#ffa500;
    display:none;flex-shrink:0;margin-left:4px}
</style>
</head>
<body>

<h2>Text Review &amp; Correction</h2>

<div class="topbar">
  <label>Story: <select id="storySel"></select></label>
  <div class="dirty-dot" id="dirtyDot" title="Unsaved changes"></div>
  <span id="status"></span>
</div>

<div class="main">

  <!-- region list -->
  <div class="region-list">
    <div class="region-list-header">Regions</div>
    <div id="regionList"></div>
  </div>

  <!-- images -->
  <div class="images">
    <div class="img-box">
      <label>Text region</label>
      <img id="textImg" src="" alt="">
    </div>
    <div class="img-box" id="drawBox" style="display:none">
      <label>Drawing (context)</label>
      <img id="drawImg" src="" alt="">
    </div>
  </div>

  <!-- editor -->
  <div class="editor-col">
    <div class="ocr-ref">
      <div class="ocr-ref-label">Original OCR (reference)</div>
      <div id="ocrRef"></div>
    </div>
    <textarea id="editor" spellcheck="false"
              placeholder="Transcribed text..."></textarea>
    <div class="nav">
      <button onclick="saveAndPrev()">&#8592; Save &amp; prev</button>
      <button class="green" onclick="saveAndNext()">Save &amp; next &#8594;</button>
      <button class="primary" onclick="saveCurrent()">Save (Ctrl+S)</button>
    </div>
  </div>

</div>

<script>
let story='', regions=[], idx=0, dirty=false;

const storySel  = document.getElementById('storySel');
const textImg   = document.getElementById('textImg');
const drawImg   = document.getElementById('drawImg');
const drawBox   = document.getElementById('drawBox');
const editor    = document.getElementById('editor');
const ocrRef    = document.getElementById('ocrRef');
const statusEl  = document.getElementById('status');
const dirtyDot  = document.getElementById('dirtyDot');
const listEl    = document.getElementById('regionList');

function status(msg, colour) {
  statusEl.textContent = msg;
  statusEl.style.color = colour || '#aaa';
}

function setDirty(val) {
  dirty = val;
  dirtyDot.style.display = val ? 'block' : 'none';
}

// ── region list ───────────────────────────────────────────────────────────────
function buildList() {
  listEl.innerHTML = '';
  regions.forEach((r, i) => {
    const el = document.createElement('div');
    el.className = 'region-item' + (i === idx ? ' active' : '');
    el.dataset.i = i;
    el.innerHTML =
      `<span class="tick">${r.saved ? '✓' : '·'}</span>` +
      `<span>${r.stem.replace('_text_', ' #')}</span>`;
    el.addEventListener('click', () => navigateTo(i));
    listEl.appendChild(el);
  });
}

function updateListItem(i) {
  const items = listEl.querySelectorAll('.region-item');
  items.forEach((el, j) => {
    el.classList.toggle('active', j === i);
    const tick = el.querySelector('.tick');
    if (tick) tick.textContent = regions[j].saved ? '✓' : '·';
  });
  // Scroll active item into view
  if (items[i]) items[i].scrollIntoView({block:'nearest'});
}

// ── navigation ────────────────────────────────────────────────────────────────
async function navigateTo(i) {
  if (dirty) await saveCurrent();
  showRegion(i);
}

function showRegion(i) {
  if (!regions.length) return;
  idx = Math.max(0, Math.min(i, regions.length - 1));
  const r = regions[idx];

  textImg.src = `/api/text_image/${story}/${r.img}?t=${Date.now()}`;

  if (r.drawing) {
    drawBox.style.display = 'block';
    drawImg.src = `/api/drawing_image/${story}/${r.drawing}?t=${Date.now()}`;
  } else {
    drawBox.style.display = 'none';
  }

  ocrRef.textContent = r.ocr || '(no OCR output)';
  // Always show the latest saved transcription (not OCR) for editing
  editor.value = r.text || r.ocr || '';
  editor.focus();
  setDirty(false);
  status('');
  updateListItem(idx);
}

// ── save ──────────────────────────────────────────────────────────────────────
async function saveCurrent() {
  const r = regions[idx];
  const text = editor.value;
  await fetch('/api/save', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({story, stem: r.stem, text})
  });
  r.text  = text;
  r.saved = true;
  setDirty(false);
  status('Saved.', '#5c5');
  updateListItem(idx);
}

async function saveAndNext() {
  await saveCurrent();
  if (idx < regions.length - 1) showRegion(idx + 1);
  else status('All done!', '#5c5');
}

async function saveAndPrev() {
  await saveCurrent();
  if (idx > 0) showRegion(idx - 1);
}

// Mark dirty on any edit
editor.addEventListener('input', () => setDirty(true));

// Keyboard shortcuts
editor.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); saveAndNext(); }
  if (e.ctrlKey && e.key === 's')     { e.preventDefault(); saveCurrent(); }
});

// Warn on page close if unsaved
window.addEventListener('beforeunload', e => {
  if (dirty) { e.preventDefault(); e.returnValue = ''; }
});

// ── story load ────────────────────────────────────────────────────────────────
async function loadStory(name) {
  story = name;
  status('Loading...');
  const r = await fetch(`/api/regions/${name}`);
  regions = await r.json();
  if (regions.length) { buildList(); showRegion(0); }
  else status('No regions found.');
}

storySel.addEventListener('change', () => loadStory(storySel.value));

(async () => {
  const r = await fetch('/api/stories');
  const stories = await r.json();
  stories.forEach(s => {
    const o = document.createElement('option');
    o.value = o.textContent = s;
    storySel.appendChild(o);
  });
  if (stories.length) loadStory(stories[0]);
})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR review and correction UI.")
    parser.add_argument("--story", type=str, default=None)
    parser.add_argument("--port",  type=int, default=5001)
    args = parser.parse_args()

    url = f"http://localhost:{args.port}"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"Opening {url} ...")
    app.run(port=args.port, debug=False)
