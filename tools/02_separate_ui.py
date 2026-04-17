"""
02_separate_ui.py — Region separation tool (Flask + HTML canvas)
================================================================
Opens a browser-based tool for marking drawing and text regions.

Workflow per page:
  1. Drag to draw a bounding box (orange while dragging)
  2. Select Drawing or Text radio button
  3. Click "Add Region"  (red = drawing, blue = text)
  4. Repeat, then "Save & next"

Output:
    _separated/_drawings/<story>/page_001_drawing_0.png  + page_001.json
    _separated/_text/<story>/page_001_text_0.png

Usage:
    python tools/02_separate_ui.py
    python tools/02_separate_ui.py --story dgb1-tambuna22-manam-volcano
    python tools/02_separate_ui.py --port 5000
"""

import argparse
import json
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from PIL import Image as PILImage

PAGES_DIR    = Path("_pages")
DRAWINGS_DIR = Path("_separated/_drawings")
TEXT_DIR     = Path("_separated/_text")

app = Flask(__name__)


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML_PAGE


@app.route("/api/stories")
def api_stories():
    stories = sorted([d.name for d in PAGES_DIR.iterdir() if d.is_dir()])
    return jsonify(stories)


@app.route("/api/pages/<story>")
def api_pages(story):
    pages = sorted([p.name for p in (PAGES_DIR / story).glob("page_*.png")])
    return jsonify(pages)


@app.route("/api/image/<story>/<page>")
def api_image(story, page):
    path = PAGES_DIR / story / page
    return send_file(str(path.resolve()), mimetype="image/png")


@app.route("/api/save", methods=["POST"])
def api_save():
    data    = request.get_json()
    story   = data["story"]
    page    = data["page"]
    boxes   = data["boxes"]
    base    = PILImage.open(PAGES_DIR / story / page)
    saved   = _crop_and_save(base, boxes, story, Path(page).stem)
    return jsonify({"saved": saved})


def _crop_and_save(base_img, boxes, story, page_stem):
    saved, dn, tn, meta = [], 0, 0, []
    w, h = base_img.size
    for box in boxes:
        x1 = int(box["x1"] * w);  y1 = int(box["y1"] * h)
        x2 = int(box["x2"] * w);  y2 = int(box["y2"] * h)
        crop = base_img.crop((x1, y1, x2, y2))
        if box["label"] == "drawing":
            d = DRAWINGS_DIR / story;  d.mkdir(parents=True, exist_ok=True)
            fname = f"{page_stem}_drawing_{dn}.png";  dn += 1
        else:
            d = TEXT_DIR / story;  d.mkdir(parents=True, exist_ok=True)
            fname = f"{page_stem}_text_{tn}.png";  tn += 1
        crop.save(str(d / fname))
        saved.append(fname)
        meta.append({"file": fname, "label": box["label"],
                     "bbox": [x1, y1, x2, y2]})
    jd = DRAWINGS_DIR / story;  jd.mkdir(parents=True, exist_ok=True)
    (jd / f"{page_stem}.json").write_text(json.dumps(meta, indent=2))
    return saved


# ── Single-page HTML app ──────────────────────────────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Matukar — Region Separation</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:sans-serif;background:#1a1a1a;color:#ddd;padding:14px}
  h2{margin-bottom:10px;font-size:18px}
  .bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
  select,button{padding:6px 12px;border-radius:4px;border:1px solid #555;
    background:#2c2c2c;color:#ddd;cursor:pointer;font-size:13px}
  button:hover{background:#3a3a3a}
  .primary{background:#1a5fb4!important;border-color:#1a5fb4!important}
  .primary:hover{background:#2272d8!important}
  .status{font-size:12px;color:#aaa;margin-bottom:8px;min-height:16px}
  #regions{font-size:12px;color:#aaa;margin-top:6px;min-height:16px}
  canvas{display:block;cursor:crosshair;max-width:100%}
  label{display:flex;align-items:center;gap:4px;cursor:pointer;font-size:13px}
</style>
</head>
<body>
<h2>Step 2: Mark Drawing &amp; Text Regions</h2>

<div class="bar">
  <label>Story:
    <select id="storySel"></select>
  </label>
  <span id="progress"></span>
</div>

<div class="bar">
  <label><input type="radio" name="lbl" value="drawing" checked> &#x1F534; Drawing</label>
  <label><input type="radio" name="lbl" value="text"> &#x1F535; Text</label>
  <button class="primary" onclick="addRegion()">Add Region</button>
  <button onclick="undoLast()">Undo</button>
  <button class="primary" onclick="saveAndNext()">Save &amp; next</button>
  <button onclick="skipPage()">Skip</button>
</div>

<div id="status" class="status">Loading&#x2026;</div>
<canvas id="canvas"></canvas>
<div id="regions"></div>

<script>
const canvas = document.getElementById('canvas');
const ctx    = canvas.getContext('2d');
const sel    = document.getElementById('storySel');

let story='', pages=[], idx=0, boxes=[], pending=null;
let dragging=false, sx=0,sy=0,cx=0,cy=0;
const img = new Image();

img.onload = () => {
  const maxW = Math.min(window.innerWidth - 28, img.naturalWidth);
  canvas.width  = maxW;
  canvas.height = Math.round(maxW * img.naturalHeight / img.naturalWidth);
  redraw();
};

function pos(e) {
  const r = canvas.getBoundingClientRect();
  // scale from CSS pixels to canvas pixels
  return [
    (e.clientX - r.left) * (canvas.width  / r.width),
    (e.clientY - r.top)  * (canvas.height / r.height)
  ];
}

canvas.addEventListener('mousedown', e => {
  [sx,sy] = pos(e); cx=sx; cy=sy;
  dragging=true; pending=null;
  e.preventDefault();
});
window.addEventListener('mousemove', e => {
  if (!dragging) return;
  [cx,cy] = pos(e); redraw();
});
window.addEventListener('mouseup', e => {
  if (!dragging) return;
  dragging=false;
  [cx,cy] = pos(e);
  const x1=Math.min(sx,cx)/canvas.width,  y1=Math.min(sy,cy)/canvas.height;
  const x2=Math.max(sx,cx)/canvas.width,  y2=Math.max(sy,cy)/canvas.height;
  if ((x2-x1)<0.01||(y2-y1)<0.01){redraw();return;}
  pending={x1,y1,x2,y2};
  status('Box drawn — pick Drawing or Text, then Add Region.');
  redraw();
});

function redraw() {
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

  boxes.forEach(b => {
    const d = b.label==='drawing';
    ctx.fillStyle   = d ? 'rgba(220,50,50,.35)' : 'rgba(50,110,220,.35)';
    ctx.strokeStyle = d ? '#ff5555' : '#5588ff';
    ctx.lineWidth=2; ctx.setLineDash([]);
    const bx=b.x1*canvas.width, by=b.y1*canvas.height;
    const bw=(b.x2-b.x1)*canvas.width, bh=(b.y2-b.y1)*canvas.height;
    ctx.fillRect(bx,by,bw,bh); ctx.strokeRect(bx,by,bw,bh);
    ctx.fillStyle='#fff'; ctx.font='bold 12px sans-serif';
    ctx.fillText(b.label, bx+5, by+16);
  });

  function drawBox(x1,y1,x2,y2,fill,stroke,dash) {
    ctx.fillStyle=fill; ctx.strokeStyle=stroke;
    ctx.lineWidth=2; ctx.setLineDash(dash||[]);
    ctx.fillRect(x1,y1,x2-x1,y2-y1);
    ctx.strokeRect(x1,y1,x2-x1,y2-y1);
    ctx.setLineDash([]);
  }

  if (pending) {
    drawBox(pending.x1*canvas.width, pending.y1*canvas.height,
            pending.x2*canvas.width, pending.y2*canvas.height,
            'rgba(255,165,0,.2)','#ffa500',[6,3]);
  }
  if (dragging) {
    drawBox(Math.min(sx,cx),Math.min(sy,cy),
            Math.max(sx,cx),Math.max(sy,cy),
            'rgba(255,165,0,.15)','#ffa500',[6,3]);
  }
}

function getLabel() {
  return document.querySelector('input[name="lbl"]:checked').value;
}
function status(msg){ document.getElementById('status').textContent=msg; }
function updateList(){
  document.getElementById('regions').textContent =
    boxes.length ? boxes.map((b,i)=>`${i+1}. ${b.label}`).join('  |  ') : '';
}

function addRegion(){
  if(!pending){status('Draw a box first.');return;}
  boxes.push({...pending,label:getLabel()});
  pending=null; updateList();
  status(`Added ${boxes[boxes.length-1].label}. Draw another or Save & next.`);
  redraw();
}
function undoLast(){
  if(boxes.length)boxes.pop();
  pending=null; updateList(); status('Removed last region.'); redraw();
}
async function saveAndNext(){
  if(!boxes.length){status('Add at least one region first.');return;}
  status('Saving\u2026');
  const r=await fetch('/api/save',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({story,page:pages[idx],boxes})});
  const d=await r.json();
  status(`Saved ${d.saved.length} region(s).`);
  advance();
}
function skipPage(){ status('Skipped.'); advance(); }
function advance(){
  if(idx<pages.length-1){ idx++; boxes=[]; pending=null; updateList(); loadImg(); }
  else { status('All pages done!'); }
}
function loadImg(){
  document.getElementById('progress').textContent=`Page ${idx+1} / ${pages.length}`;
  img.src=`/api/image/${story}/${pages[idx]}?t=${Date.now()}`;
}

async function loadStory(name){
  story=name; idx=0; boxes=[]; pending=null; updateList();
  const r=await fetch(`/api/pages/${name}`);
  pages=await r.json();
  if(pages.length) loadImg(); else status('No pages found.');
}

sel.addEventListener('change',()=>loadStory(sel.value));
window.addEventListener('resize',()=>{ if(img.src && img.complete) img.onload(); });

(async()=>{
  const r=await fetch('/api/stories');
  const stories=await r.json();
  stories.forEach(s=>{
    const o=document.createElement('option');
    o.value=o.textContent=s; sel.appendChild(o);
  });
  if(stories.length) loadStory(stories[0]);
})();
</script>
</body>
</html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Region separation UI.")
    parser.add_argument("--story", type=str, default=None)
    parser.add_argument("--port",  type=int, default=5000)
    args = parser.parse_args()

    url = f"http://localhost:{args.port}"
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"Opening {url} ...")
    app.run(port=args.port, debug=False)
