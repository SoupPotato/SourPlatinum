import base64
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import underground_block_builder as B
ASSETS = os.path.join(HERE, 'underground_block_editor_assets')
TEX_DIR = os.path.join(ASSETS, 'hideaway_textures')
OBJ_DIR = os.path.join(ASSETS, 'hideaway_objects')


def data_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def png_size(path):
    raw = open(path, 'rb').read(24)
    return [int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')]


kit = json.load(open(os.path.join(ASSETS, 'cave_kit.json')))
edges = json.load(open(os.path.join(ASSETS, 'ground_edges.json')))
water_kit = json.load(open(os.path.join(ASSETS, 'water_kit.json')))
edge_sheets = set(v['edge'] for v in edges['families'].values()) | {water_kit['bank'], 'puddle_b'}
biomes = json.load(open(os.path.join(ASSETS, 'hideaway_biomes.json')))
tex, sizes, floors, alpha = {}, {}, [], {}
for sub in sorted(os.listdir(TEX_DIR)):
    for fn in sorted(os.listdir(os.path.join(TEX_DIR, sub))):
        if fn.endswith('.png'):
            key = sub + '/' + fn[:-4]
            tex[key] = data_uri(os.path.join(TEX_DIR, sub, fn))
            sizes[key] = png_size(os.path.join(TEX_DIR, sub, fn))
            alphas = set(a for row in B.read_png(os.path.join(TEX_DIR, sub, fn))[2] for r, g, b, a in row)
            if len(alphas) == 1 and 0 < min(alphas) < 255:
                alpha[tex[key]] = round(min(alphas) / 255.0, 3)
            if sub == 'floors' and fn[:-4] not in edge_sheets:
                floors.append(fn[:-4])
for name in ('dun_dhole', 'dun_ent2'):
    tex[name] = data_uri(os.path.join(ASSETS, name + '.png'))
    sizes[name] = png_size(os.path.join(ASSETS, name + '.png'))

props = {}
catalogue = os.path.join(ASSETS, 'hideaway_objects.json')
if os.path.exists(catalogue):
    for entry in json.load(open(catalogue)):
        mesh_path = os.path.join(OBJ_DIR, entry['key'] + '.json')
        if not os.path.exists(mesh_path):
            continue
        mesh = json.load(open(mesh_path))
        for g in mesh['groups']:
            png = os.path.join(OBJ_DIR, mesh['textures'][g['tex']]) if g['tex'] in mesh['textures'] else None
            g['img'] = data_uri(png) if png and os.path.exists(png) else None
        item = {'label': mesh['label'], 'w': mesh['w'], 'h': mesh['h'], 'walkable': mesh.get('walkable', False), 'mesh': mesh['groups']}
        icon = os.path.join(OBJ_DIR, 'icon_' + entry['key'] + '.png')
        if os.path.exists(icon):
            item['icon'] = data_uri(icon)
        props[entry['key']] = item

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hideaway Editor</title>
<style>
:root {
  --bg: #1d1b1a;
  --panel: #2a2725;
  --text: #ece6df;
  --muted: #a99f95;
  --accent: #e0a458;
  --bad: #e5484d;
  --line: #3d3835;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.4 system-ui, sans-serif; }
header { padding: 12px 16px; border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
header h1 { font-size: 16px; margin: 0 12px 0 0; }
button, label.btn, select, input[type=text] { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: 6px; padding: 6px 10px; font: inherit; }
button, label.btn { cursor: pointer; }
button:hover, label.btn:hover { border-color: var(--accent); }
button.on { border-color: var(--accent); color: var(--accent); }
main { display: flex; gap: 16px; padding: 16px; align-items: flex-start; flex-wrap: wrap; }
#grid { image-rendering: pixelated; cursor: crosshair; background: #000; max-width: 100%; touch-action: none; }
#view { position: relative; }
#view canvas { display: block; width: 640px; height: 640px; max-width: 100%; border-radius: 4px; cursor: grab; touch-action: none; background: #26232a; }
#view canvas:active { cursor: grabbing; }
#viewHint { position: absolute; left: 8px; bottom: 8px; font-size: 12px; color: var(--muted); pointer-events: none; }
#side { display: flex; flex-direction: column; gap: 12px; width: 400px; max-width: 100%; }
.panel { background: var(--panel); padding: 10px 12px; border-radius: 8px; }
.panel h2 { font-size: 13px; margin: 0 0 8px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
.tools { display: flex; gap: 6px; flex-wrap: wrap; }
.row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
.row span.label { color: var(--muted); min-width: 92px; }
.swatch { display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.palette { display: grid; grid-template-columns: repeat(auto-fill, minmax(56px, 1fr)); gap: 6px; max-height: 260px; overflow: auto; }
.palette button { padding: 3px; font-size: 10px; line-height: 1.2; display: flex; flex-direction: column; align-items: center; gap: 2px; overflow: hidden; }
.palette .thumb { width: 40px; height: 40px; border-radius: 3px; image-rendering: pixelated; background-size: 20px 20px; }
.palette .thumb.icon { background-size: cover; image-rendering: auto; }
.palette .name { max-width: 52px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#status { min-height: 1.4em; }
#warnings { color: var(--bad); }
code { background: #00000055; padding: 1px 4px; border-radius: 4px; }
p { margin: 6px 0; color: var(--muted); }
p b { color: var(--text); }
kbd { background: #00000055; border: 1px solid var(--line); border-radius: 3px; padding: 0 4px; font-size: 12px; }
</style>
</head>
<body>
<header>
  <h1>Hideaway Editor</h1>
  <select id="biome" title="Hideaway type"></select>
  <select id="size" title="Hideaway size"><option value="32">Small (32x32)</option><option value="64">Big (64x64)</option></select>
  <input type="text" id="name" size="20" title="Hideaway name">
  <button id="undo">Undo</button>
  <button id="redo">Redo</button>
  <button id="new">New</button>
  <button id="save">Save hideaway file</button>
  <label class="btn">Open hideaway file<input id="open" type="file" accept=".json" hidden></label>
  <button id="toggle3d" class="on">3D view</button>
  <button id="resetView">Reset camera</button>
</header>
<main>
  <canvas id="grid"></canvas>
  <div id="view"><canvas id="view3d"></canvas><div id="viewHint">Drag to orbit &middot; right-drag to pan &middot; scroll to zoom</div></div>
  <div id="side">
    <div class="panel">
      <h2>Terrain</h2>
      <div class="tools">
        <button data-tool="." class="on"><span class="swatch" style="background:#6fbf4a"></span>Floor <kbd>1</kbd></button>
        <button data-tool="#"><span class="swatch" style="background:#3a281e"></span>Rock <kbd>2</kbd></button>
        <button data-tool="~"><span class="swatch" style="background:#4a7fc0"></span>Water / lava <kbd>3</kbd></button>
        <button data-tool="X"><span class="swatch" style="background:#000;border:1px solid #b5713f"></span>Exit <kbd>4</kbd></button>
        <button data-tool="height"><span class="swatch" style="background:linear-gradient(#ece6df,#3a281e)"></span>Height only <kbd>5</kbd></button>
      </div>
      <div class="row"><span class="label">Rock height</span><span class="tools" id="rockHeights"></span></div>
      <div class="row"><span class="label">Water depth</span><span class="tools" id="liquidDepths"></span></div>
      <p>Rock rises one storey per tile, like the cave walls. Height 2 is the normal cave wall. Water at depth 0 is a pond or river: it sits just below the ground with an overworld-style shoreline. Depth 1 or 2 makes a deeper pit with cave-wall banks (good for lava).</p>
    </div>
    <div class="panel">
      <h2>Textures <kbd>6</kbd></h2>
      <div class="palette" id="texPalette"></div>
      <p>Paints floors, water and the flat tops of rock. <b>None</b> leaves a rock top black, like the cave walls. Bright grass, path, sand, snow, puddles and lakes get rounded edges and corners automatically on the floor around them, using the same edge tiles as the overworld.</p>
    </div>
    <div class="panel">
      <h2>Objects <kbd>7</kbd></h2>
      <div class="palette" id="objPalette"></div>
      <div class="row"><button id="rotate">Rotate <kbd>R</kbd></button><button data-tool="erase"><span class="swatch" style="background:#e5484d"></span>Remove object <kbd>8</kbd></button></div>
      <p id="objHint">Objects stand on the level of the tile under their corner and block the tiles they cover (flowers, craters and pools stay walkable). <b>R</b> turns the next object.</p>
    </div>
    <div class="panel">
      <h2>Hideaway</h2>
      <div id="status"></div>
      <div id="warnings"></div>
    </div>
    <div class="panel">
      <h2>Adding it to the game</h2>
      <p>Drag to paint. Hold <b>Shift</b> while dragging to fill a rectangle. Right-click a tile to pick up its terrain, height and texture.</p>
      <p><b>Exit</b> goes in a straight cave wall (height 2) right next to the floor, with rock on both sides. It becomes the doorway back to the Underground. Use one exit.</p>
      <p>Save the file into <code>tools/underground_block_editor_assets/hideaways</code>, then run <code>py -3 install_hideaways.py</code> in the tools folder.</p>
    </div>
  </div>
</main>
<script>
const BIOMES = __BIOMES__;
const HTEX = __HTEX__;
const HSIZE = __HSIZE__;
const FLOORS = __FLOORS__;
const PROPS = __PROPS__;
const KIT = __KIT__;
const EDGES = __EDGES__;
const WATER_KIT = __WATER__;
const TEX_ALPHA = __ALPHA__;
const SYMMETRIES = [[1, 0, 0, 1], [0, -1, 1, 0], [-1, 0, 0, -1], [0, 1, -1, 0], [-1, 0, 0, 1], [1, 0, 0, -1], [0, 1, 1, 0], [0, -1, -1, 0]];
const EDGE_OF = {};
for (const [f, v] of Object.entries(EDGES.families)) EDGE_OF[f] = v.edge;
function nameOf(key) { if (!key) return null; return key[0] === '@' ? BIOMES[biome][key.slice(1)] : key; }
function canonMask(mask) {
  const m = mask.split('');
  for (const [d, a, b] of [[0, 1, 3], [2, 1, 4], [5, 3, 6], [7, 4, 6]]) if (m[a] === '1' || m[b] === '1') m[d] = '0';
  return m.join('');
}
function edgeFor(x, z, lv) {
  if (T[z][x] !== '.' || lv.L[z][x] !== 0 || lv.slope[z][x] || EDGE_OF[nameOf(Pn[z][x])]) return null;
  let best = null;
  for (const fam of Object.keys(EDGE_OF)) {
    let mask = '', n = 0;
    for (const [dx, dy] of EDGES.neighbours) {
      const xx = x + dx, zz = z + dy;
      const on = inside(xx, zz) && lv.L[zz][xx] === 0 && !lv.slope[zz][xx] && T[zz][xx] === '.' && nameOf(Pn[zz][xx]) === fam;
      mask += on ? '1' : '0'; if (on) n++;
    }
    if (n && (!best || n > best[0])) best = [n, fam, mask];
  }
  if (!best) return null;
  const [, fam, mask] = best;
  const entry = EDGES.families[fam].masks[mask] || EDGES.canonical[canonMask(mask)];
  if (!entry) return { fill: fam };
  const corners = entry[(x % 2) + '' + (z % 2)] || Object.values(entry)[0];
  return { sheet: 'floors/' + EDGE_OF[fam], corners };
}
function edgeUV(corners, px, py) {
  const s = px / 16, t = py / 16, [nw, ne, se, sw] = corners;
  const u = nw[0] * (1 - s) * t + ne[0] * s * t + se[0] * s * (1 - t) + sw[0] * (1 - s) * (1 - t);
  const v = nw[1] * (1 - s) * t + ne[1] * s * t + se[1] * s * (1 - t) + sw[1] * (1 - s) * (1 - t);
  return [u, v];
}
const STOREY = 16;
const WALL_TEXTURES = ['dun_wall_n', 'dun_wall_s', 'dun_wall_e', 'dun_wall_w', 'dun_wall_c', 'dun_floor', 'dun_floor2'];
const BASE_FLOORS = ['dun_floor', 'dun_floor3', 'dun_floor4'];
const TOP_FLOORS = ['dun_floor2', 'black'];
const NB = []; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) NB.push([dx, dy]);
const WEIGHTS = [1, 2, 1, 2, 0, 2, 1, 2, 1];
const FRONT_TO_DOOR = { '0,1': 'N', '0,-1': 'S', '1,0': 'W', '-1,0': 'E' };

let N = 32, S = 20, biome = 'grassland', extra = {};
let T = [], Hh = [], Pn = [], objects = [];
let tool = '.', rockHeight = 2, liquidDepth = 1, curTex = '@floor', curObj = null, curRot = 0;
let painting = false, rectStart = null, hover = null, before = null;
const undoStack = [], redoStack = [];
const cv = document.getElementById('grid');
const ctx = cv.getContext('2d');

function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function inside(x, z) { return x >= 0 && z >= 0 && x < N && z < N; }

function texPath(key) {
  const b = BIOMES[biome];
  if (!key) return null;
  if (key[0] === '@') return 'floors/' + b[key.slice(1)];
  if (key === 'rock') return 'walls_' + b.walls + '/dun_floor2';
  return 'floors/' + key;
}
function texLabel(key) {
  if (!key) return 'none';
  if (key[0] === '@') return { '@floor': 'Type floor', '@floor2': 'Type floor 2', '@path': 'Type path', '@liquid': 'Type liquid' }[key] + ' (' + BIOMES[biome][key.slice(1)] + ')';
  return key === 'rock' ? 'Rock' : key;
}

const images = {};
function image(path) {
  if (!path) return null;
  if (images[path] === undefined) {
    images[path] = null;
    const img = new Image();
    img.onload = () => { images[path] = img; draw(); };
    img.src = HTEX[path];
  }
  return images[path];
}

function blank(n) {
  T = []; Hh = []; Pn = [];
  for (let z = 0; z < n; z++) {
    T.push([]); Hh.push([]); Pn.push([]);
    for (let x = 0; x < n; x++) {
      const floor = x >= 4 && x < n - 4 && z >= 5 && z < n - 5;
      T[z].push(floor ? '.' : '#'); Hh[z].push(floor ? 0 : 2); Pn[z].push(floor ? '@floor' : null);
    }
  }
  T[4][n / 2] = 'X';
  objects = [];
}

function fromFile(d) {
  const n = d.tiles.length;
  const b = BIOMES[d.biome] || BIOMES.grassland;
  const palette = d.palette || ['@floor', '@floor2', '@liquid'];
  T = []; Hh = []; Pn = [];
  for (let z = 0; z < n; z++) {
    T.push([]); Hh.push([]); Pn.push([]);
    for (let x = 0; x < n; x++) {
      let c = d.tiles[z][x];
      let p = null;
      const pv = d.paint ? d.paint[z][x] : null;
      if (pv && pv !== '-' && pv !== ' ') p = palette[parseInt(pv, 36)];
      if (c === ',') { c = '.'; if (!pv) p = '@floor2'; }
      if (!pv && c === '.') p = '@floor';
      if (!pv && c === '~') p = '@liquid';
      if (c === 'D') c = 'X';
      const hv = d.heights ? d.heights[z][x] : null;
      let h = 0;
      if (c === '#' || c === 'X') h = hv && +hv > 0 ? +hv : 2;
      else if (c === '~') h = hv ? +hv : 0;
      T[z].push(c); Hh[z].push(h); Pn[z].push(p);
    }
  }
  objects = (d.objects || []).map(o => { const [w, h] = footprint(o.key, o.rot || 0); return Object.assign({}, o, { w, h }); });
}

function toFile() {
  const palette = [];
  const idx = k => { let i = palette.indexOf(k); if (i < 0) { palette.push(k); i = palette.length - 1; } return i.toString(36); };
  const name = (document.getElementById('name').value || 'hideaway').replace(/[^A-Za-z0-9_-]/g, '_');
  const tiles = T.map(r => r.join(''));
  const heights = Hh.map(r => r.map(v => String(v)).join(''));
  const paint = Pn.map(r => r.map(p => p ? idx(p) : '-').join(''));
  return Object.assign({}, extra, { name, biome, palette, tiles, heights, paint, objects: objects.map(o => Object.assign({}, o)) });
}

function snapshot() { return JSON.stringify({ T, Hh, Pn, objects, N }); }
function restore(s) {
  const d = JSON.parse(s);
  T = d.T; Hh = d.Hh; Pn = d.Pn; objects = d.objects;
  if (d.N !== N) { N = d.N; resizeGrid(); }
  draw();
}
function resizeGrid() {
  S = Math.floor(640 / N);
  cv.width = N * S; cv.height = N * S;
  document.getElementById('size').value = String(N);
  if (window.resetView3d) window.resetView3d();
}

function levels() {
  const L = [], U = [];
  for (let z = 0; z < N; z++) {
    L.push([]); U.push([]);
    for (let x = 0; x < N; x++) {
      const t = T[z][x];
      L[z].push(t === '#' || t === 'X' ? Hh[z][x] : 0);
      U[z].push(t === '~' ? Hh[z][x] : 0);
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
      const t = T[z][x];
      if (t === '#' || t === 'X') {
        let low = Infinity;
        for (const [dx, dy] of NB) { if ((dx || dy) && inside(x + dx, z + dy)) low = Math.min(low, Math.max(L[z + dy][x + dx], 0)); }
        if (low === Infinity) low = L[z][x];
        const v = Math.min(Hh[z][x], low + 1);
        if (v !== L[z][x]) { L[z][x] = v; changed = true; }
      } else if (t === '~') {
        let low = Infinity;
        for (const [dx, dy] of NB) { if ((dx || dy) && inside(x + dx, z + dy)) low = Math.min(low, T[z + dy][x + dx] === '~' ? U[z + dy][x + dx] : -1); }
        if (low === Infinity) low = U[z][x];
        const v = Math.min(Hh[z][x], low + 1);
        if (v !== U[z][x]) { U[z][x] = v; changed = true; }
      }
    }
  }
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) if (T[z][x] === '~') L[z][x] = -U[z][x];
  const slope = [];
  for (let z = 0; z < N; z++) {
    slope.push([]);
    for (let x = 0; x < N; x++) {
      let s = false;
      for (const [dx, dy] of NB) if (inside(x + dx, z + dy) && L[z + dy][x + dx] < L[z][x]) s = true;
      slope[z].push(s);
    }
  }
  return { L, slope };
}

function exitFront(x, z) {
  const f = [[0, 1], [0, -1], [1, 0], [-1, 0]].filter(([dx, dz]) => inside(x + dx, z + dz) && T[z + dz][x + dx] === '.');
  return f.length === 1 ? f[0] : null;
}

function exitProblems(lv) {
  const bad = [];
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    if (T[z][x] !== 'X') continue;
    const f = exitFront(x, z);
    if (!f) { bad.push([x, z]); continue; }
    let ok = true;
    for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) {
      const dx = f[0] === 0 ? a : b, dz = f[0] === 0 ? b : a;
      const depth = f[0] === 0 ? dz * f[1] : dx * f[0];
      const want = depth > 0 ? 0 : (depth === 0 ? 1 : 2);
      if (!inside(x + dx, z + dz) || lv.L[z + dz][x + dx] !== want) ok = false;
    }
    if (!ok) bad.push([x, z]);
  }
  return bad;
}

function objectAt(x, z) {
  for (let i = objects.length - 1; i >= 0; i--) {
    const o = objects[i];
    if (x >= o.x && x < o.x + (o.w || 1) && z >= o.z && z < o.z + (o.h || 1)) return i;
  }
  return -1;
}

function footprint(id, rot) {
  const p = PROPS[id];
  const w = p ? p.w || 1 : 1, h = p ? p.h || 1 : 1;
  return rot % 2 ? [h, w] : [w, h];
}

const ROCK_SHADES = ['#3a281e', '#5a4130', '#4a3426', '#3a281e', '#2e1f17', '#24170f'];
function draw() {
  if (!T.length) return;
  const lv = levels();
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    const t = T[z][x], edge = edgeFor(x, z, lv);
    const path = edge && edge.fill ? texPath(edge.fill) : texPath(Pn[z][x]), img = path && t !== 'X' ? image(path) : null;
    const sheet = edge && edge.sheet ? image(edge.sheet) : null;
    if (sheet) {
      const w = sheet.width, h = sheet.height, [nw, ne, , sw] = edge.corners;
      const ax = nw[0] * w, ay = (1 - nw[1]) * h, bx = ne[0] * w, by = (1 - ne[1]) * h, cx = sw[0] * w, cy = (1 - sw[1]) * h;
      const det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay);
      if (Math.abs(det) > 1e-6) {
        const i00 = (cy - ay) / det, i01 = -(cx - ax) / det, i10 = -(by - ay) / det, i11 = (bx - ax) / det;
        const a = S * i00, c = S * i01, b = S * i10, d = S * i11;
        ctx.save();
        ctx.beginPath(); ctx.rect(x * S, z * S, S, S); ctx.clip();
        ctx.setTransform(a, b, c, d, x * S - a * ax - c * ay, z * S - b * ax - d * ay);
        ctx.drawImage(sheet, 0, 0);
        ctx.restore();
      }
    } else if (img) {
      const tw = img.width, th = img.height, sx = (x * 16) % tw, sy = (z * 16) % th;
      ctx.drawImage(img, sx, sy, Math.min(16, tw - sx), Math.min(16, th - sy), x * S, z * S, S, S);
    } else {
      ctx.fillStyle = t === 'X' ? '#000' : t === '~' ? '#4a7fc0' : t === '.' ? '#6fbf4a' : ROCK_SHADES[Math.min(5, Hh[z][x])];
      ctx.fillRect(x * S, z * S, S, S);
    }
    if (t === '#' && img) { ctx.fillStyle = 'rgba(30,18,10,0.35)'; ctx.fillRect(x * S, z * S, S, S); }
    if (t === '~' || t === '#') {
      const l = lv.L[z][x];
      if (lv.slope[z][x]) { ctx.fillStyle = 'rgba(0,0,0,0.22)'; ctx.fillRect(x * S, z * S, S, S); }
      if ((t === '#' && Hh[z][x] !== 2) || (t === '~' && Hh[z][x] > 0) || (t === '#' && Pn[z][x])) {
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.font = Math.max(8, Math.floor(S * 0.5)) + 'px system-ui';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        if (S >= 10) ctx.fillText(t === '~' ? '-' + Hh[z][x] : String(Hh[z][x]), x * S + S / 2, z * S + S / 2 + 1);
      }
    }
  }
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    if (T[z][x] !== 'X') continue;
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(x * S + 2, z * S + 2, S - 4, S - 4);
    const f = exitFront(x, z);
    if (f) {
      ctx.fillStyle = '#e0a458';
      ctx.beginPath();
      const cx = x * S + S / 2, cz = z * S + S / 2;
      ctx.moveTo(cx + f[0] * S * 0.35, cz + f[1] * S * 0.35);
      ctx.lineTo(cx - f[1] * S * 0.25, cz + f[0] * S * 0.25);
      ctx.lineTo(cx + f[1] * S * 0.25, cz - f[0] * S * 0.25);
      ctx.fill();
    }
  }
  for (const o of objects) {
    const p = PROPS[o.key];
    const w = o.w || 1, h = o.h || 1;
    ctx.fillStyle = 'rgba(224,164,88,0.35)';
    ctx.fillRect(o.x * S, o.z * S, w * S, h * S);
    const icon = p && p.icon ? image('icon:' + o.key) : null;
    if (icon) ctx.drawImage(icon, o.x * S, o.z * S, w * S, h * S);
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 1.5;
    ctx.strokeRect(o.x * S + 1, o.z * S + 1, w * S - 2, h * S - 2);
  }
  ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = 1;
  for (let i = 0; i <= N; i++) {
    ctx.beginPath(); ctx.moveTo(i * S + 0.5, 0); ctx.lineTo(i * S + 0.5, N * S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * S + 0.5); ctx.lineTo(N * S, i * S + 0.5); ctx.stroke();
  }
  for (let i = 0; i <= N; i += 8) {
    ctx.strokeStyle = i % 32 === 0 && i > 0 && i < N ? 'rgba(224,164,88,0.8)' : 'rgba(255,255,255,0.3)';
    ctx.beginPath(); ctx.moveTo(i * S + 0.5, 0); ctx.lineTo(i * S + 0.5, N * S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * S + 0.5); ctx.lineTo(N * S, i * S + 0.5); ctx.stroke();
  }
  const bad = exitProblems(lv);
  ctx.strokeStyle = '#e5484d'; ctx.lineWidth = 2;
  for (const [x, z] of bad) ctx.strokeRect(x * S + 1, z * S + 1, S - 2, S - 2);
  if (rectStart && hover) {
    const [x0, z0, x1, z1] = rectBounds(rectStart, hover);
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(x0 * S + 1, z0 * S + 1, (x1 - x0 + 1) * S - 2, (z1 - z0 + 1) * S - 2);
  } else if (hover) {
    let [w, h] = tool === 'object' && curObj ? footprint(curObj, curRot) : [1, 1];
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(hover[0] * S + 1, hover[1] * S + 1, w * S - 2, h * S - 2);
  }
  const counts = {};
  T.flat().forEach(c => counts[c] = (counts[c] || 0) + 1);
  const exits = counts['X'] || 0;
  let info = BIOMES[biome].label + ' &middot; ' + (counts['.'] || 0) + ' floor, ' + (counts['~'] || 0) + ' water, ' + objects.length + ' object(s), ' + exits + ' exit';
  if (hover) {
    const [hx, hz] = hover, t = T[hz][hx];
    const kind = { '.': 'floor', '#': 'rock', '~': 'water', 'X': 'exit' }[t];
    info += '<br>tile ' + hx + ', ' + hz + ': ' + kind + (t === '#' ? ' height ' + Hh[hz][hx] : t === '~' ? ' depth ' + Hh[hz][hx] : '') + ' &middot; level ' + lv.L[hz][hx] + (lv.slope[hz][hx] ? ' (slope)' : '') + ' &middot; ' + texLabel(Pn[hz][hx]);
  }
  document.getElementById('status').innerHTML = info;
  const warn = [];
  if (exits !== 1) warn.push('A hideaway needs exactly one exit.');
  if (bad.length) warn.push(bad.length + ' exit(s) need a straight height-2 wall 3 tiles wide with floor in front (marked red).');
  const missing = objects.filter(o => !PROPS[o.key]).length;
  if (missing) warn.push(missing + ' object(s) are not in the catalogue.');
  document.getElementById('warnings').textContent = warn.join(' ');
  store('ugHideawayEditor2', JSON.stringify(toFile()));
  if (window.schedule3d) window.schedule3d();
}

function rectBounds(a, b) { return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])]; }
function tileAt(e) {
  const r = cv.getBoundingClientRect();
  const x = Math.floor((e.clientX - r.left) / r.width * N), z = Math.floor((e.clientY - r.top) / r.height * N);
  return inside(x, z) ? [x, z] : null;
}

function apply(x, z) {
  const t = T[z][x];
  if (tool === '.') {
    if (t !== '.') Pn[z][x] = curTex && curTex !== 'rock' && curTex !== '@liquid' ? curTex : '@floor';
    T[z][x] = '.'; Hh[z][x] = 0;
  } else if (tool === '#') {
    if (t !== '#') Pn[z][x] = null;
    T[z][x] = '#'; Hh[z][x] = rockHeight;
  } else if (tool === '~') {
    if (t !== '~') Pn[z][x] = '@liquid';
    T[z][x] = '~'; Hh[z][x] = liquidDepth;
  } else if (tool === 'X') {
    T[z][x] = 'X'; Hh[z][x] = 2; Pn[z][x] = null;
  } else if (tool === 'height') {
    if (t === '#') Hh[z][x] = rockHeight;
    else if (t === '~') Hh[z][x] = liquidDepth;
  } else if (tool === 'paint') {
    if (t !== 'X') Pn[z][x] = curTex;
  } else if (tool === 'erase') {
    const i = objectAt(x, z);
    if (i >= 0) objects.splice(i, 1);
  }
}

function placeObject(x, z) {
  if (!curObj) return;
  const [w, h] = footprint(curObj, curRot);
  if (x + w > N || z + h > N) return;
  for (let k = objects.length - 1; k >= 0; k--) {
    const o = objects[k];
    if (o.x < x + w && o.x + (o.w || 1) > x && o.z < z + h && o.z + (o.h || 1) > z) objects.splice(k, 1);
  }
  objects.push({ key: curObj, x, z, w, h, rot: curRot });
}

function commit() {
  if (before && before !== snapshot()) { undoStack.push(before); redoStack.length = 0; }
  before = null;
}

cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('pointerdown', e => {
  const t = tileAt(e); if (!t) return;
  const [x, z] = t;
  if (e.button === 2) {
    const k = T[z][x];
    if (k === '#') rockHeight = Hh[z][x]; else if (k === '~') liquidDepth = Hh[z][x];
    if (Pn[z][x]) curTex = Pn[z][x];
    setTool(k); refreshPanels(); return;
  }
  before = snapshot();
  cv.setPointerCapture(e.pointerId);
  if (tool === 'object') { placeObject(x, z); commit(); draw(); return; }
  if (e.shiftKey) { rectStart = t; hover = t; draw(); return; }
  painting = t; apply(x, z); draw();
});
cv.addEventListener('pointermove', e => {
  const t = tileAt(e); hover = t;
  if (painting && t) {
    const [ax, az] = painting, steps = Math.max(Math.abs(t[0] - ax), Math.abs(t[1] - az), 1);
    for (let i = 0; i <= steps; i++) apply(Math.round(ax + (t[0] - ax) * i / steps), Math.round(az + (t[1] - az) * i / steps));
    painting = t;
  }
  draw();
});
cv.addEventListener('pointerup', () => {
  if (rectStart && hover) {
    const [x0, z0, x1, z1] = rectBounds(rectStart, hover);
    for (let z = z0; z <= z1; z++) for (let x = x0; x <= x1; x++) apply(x, z);
  }
  painting = false; rectStart = null; commit(); draw();
});
cv.addEventListener('pointerleave', () => { if (!painting && !rectStart) { hover = null; draw(); } });

function setTool(t) {
  tool = t;
  document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('on', b.dataset.tool === t));
  refreshPanels();
}
document.querySelectorAll('[data-tool]').forEach(b => b.addEventListener('click', () => setTool(b.dataset.tool)));

function refreshPanels() {
  document.querySelectorAll('#rockHeights button').forEach(b => b.classList.toggle('on', +b.dataset.v === rockHeight));
  document.querySelectorAll('#liquidDepths button').forEach(b => b.classList.toggle('on', +b.dataset.v === liquidDepth));
  document.querySelectorAll('#texPalette button').forEach(b => b.classList.toggle('on', tool === 'paint' && (b.dataset.key || null) === (curTex || null) && b.dataset.key !== undefined));
  document.querySelectorAll('#objPalette button').forEach(b => b.classList.toggle('on', tool === 'object' && b.dataset.id === curObj));
}

for (const v of [1, 2, 3, 4]) {
  const b = document.createElement('button'); b.textContent = v; b.dataset.v = v;
  b.onclick = () => { rockHeight = v; if (tool !== '#' && tool !== 'height') setTool('#'); refreshPanels(); };
  document.getElementById('rockHeights').appendChild(b);
}
for (const v of [0, 1, 2]) {
  const b = document.createElement('button'); b.textContent = v; b.dataset.v = v;
  b.onclick = () => { liquidDepth = v; if (tool !== '~' && tool !== 'height') setTool('~'); refreshPanels(); };
  document.getElementById('liquidDepths').appendChild(b);
}

function buildTexPalette() {
  const pal = document.getElementById('texPalette');
  pal.innerHTML = '';
  const keys = [null, 'rock', '@floor', '@floor2', '@path', '@liquid'].concat(FLOORS);
  for (const k of keys) {
    const b = document.createElement('button');
    if (k !== null) b.dataset.key = k; else b.dataset.key = '';
    const th = document.createElement('span'); th.className = 'thumb';
    const p = texPath(k);
    th.style.background = p ? 'url(' + HTEX[p] + ') 0 0 / 20px 20px' : '#000';
    const nm = document.createElement('span'); nm.className = 'name';
    nm.textContent = k === null ? 'None' : k === 'rock' ? 'Rock' : k[0] === '@' ? { '@floor': 'Type 1', '@floor2': 'Type 2', '@path': 'Type path', '@liquid': 'Type liquid' }[k] : k;
    b.title = texLabel(k);
    b.append(th, nm);
    b.onclick = () => { curTex = k; setTool('paint'); };
    pal.appendChild(b);
  }
  document.querySelectorAll('#texPalette button').forEach(b => { if (b.dataset.key === '') b.dataset.key = ''; });
  refreshPanels();
}

function buildObjPalette() {
  const pal = document.getElementById('objPalette');
  pal.innerHTML = '';
  const ids = Object.keys(PROPS);
  if (!ids.length) { document.getElementById('objHint').textContent = 'No objects in the catalogue yet.'; return; }
  for (const id of ids) {
    const p = PROPS[id];
    if (p.icon && !HTEX['icon:' + id]) HTEX['icon:' + id] = p.icon;
    const b = document.createElement('button'); b.dataset.id = id;
    const th = document.createElement('span'); th.className = 'thumb icon';
    th.style.backgroundImage = p.icon ? 'url(' + p.icon + ')' : 'none';
    const nm = document.createElement('span'); nm.className = 'name'; nm.textContent = p.label;
    b.title = p.label + ' (' + (p.w || 1) + 'x' + (p.h || 1) + ' tiles)';
    b.append(th, nm);
    b.onclick = () => { curObj = id; setTool('object'); };
    pal.appendChild(b);
  }
}

document.getElementById('rotate').onclick = () => { curRot = (curRot + 1) % 4; draw(); };
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  const keys = { 1: '.', 2: '#', 3: '~', 4: 'X', 5: 'height', 6: 'paint', 7: 'object', 8: 'erase' };
  if (keys[e.key]) { if (keys[e.key] === 'object' && !curObj) return; setTool(keys[e.key]); }
  if (e.key === 'r' || e.key === 'R') { curRot = (curRot + 1) % 4; draw(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); }
});
function undo() { if (!undoStack.length) return; redoStack.push(snapshot()); restore(undoStack.pop()); }
function redo() { if (!redoStack.length) return; undoStack.push(snapshot()); restore(redoStack.pop()); }
document.getElementById('undo').onclick = undo;
document.getElementById('redo').onclick = redo;

const biomeSel = document.getElementById('biome');
for (const [k, b] of Object.entries(BIOMES)) {
  const o = document.createElement('option'); o.value = k; o.textContent = b.label; biomeSel.appendChild(o);
}
function setBiome(b) { biome = b; biomeSel.value = b; buildTexPalette(); draw(); }
biomeSel.onchange = () => setBiome(biomeSel.value);

document.getElementById('size').onchange = e => {
  const n = parseInt(e.target.value, 10);
  if (n === N) return;
  if (n < N && !confirm('Shrinking to 32x32 keeps only the top-left quarter. Continue?')) { e.target.value = String(N); return; }
  before = snapshot();
  const nT = [], nH = [], nP = [];
  for (let z = 0; z < n; z++) {
    nT.push([]); nH.push([]); nP.push([]);
    for (let x = 0; x < n; x++) {
      const keep = z < N && x < N;
      nT[z].push(keep ? T[z][x] : '#'); nH[z].push(keep ? Hh[z][x] : 2); nP[z].push(keep ? Pn[z][x] : null);
    }
  }
  T = nT; Hh = nH; Pn = nP;
  objects = objects.filter(o => o.x + (o.w || 1) <= n && o.z + (o.h || 1) <= n);
  N = n; resizeGrid();
  undoStack.push(before); redoStack.length = 0; before = null;
  draw();
};

document.getElementById('new').onclick = () => {
  if (!confirm('Start a new hideaway? Unsaved changes are kept in Undo.')) return;
  before = snapshot();
  N = 32; blank(32); resizeGrid();
  document.getElementById('name').value = 'hideaway_' + biome;
  extra = {};
  undoStack.push(before); redoStack.length = 0; before = null;
  draw();
};

document.getElementById('name').addEventListener('input', draw);
document.getElementById('save').onclick = () => {
  const d = toFile();
  const blob = new Blob([JSON.stringify(d, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = d.name + '.json'; a.click();
  URL.revokeObjectURL(a.href);
};

function openData(d, fallbackName) {
  const n = Array.isArray(d.tiles) ? d.tiles.length : 0;
  if ((n !== 32 && n !== 64) || d.tiles.some(r => r.length !== n)) { alert('Not a 32x32 or 64x64 hideaway file'); return false; }
  extra = Object.assign({}, d);
  for (const k of ['tiles', 'name', 'biome', 'palette', 'heights', 'paint', 'objects']) delete extra[k];
  biome = BIOMES[d.biome] ? d.biome : 'grassland';
  biomeSel.value = biome;
  fromFile(d);
  N = n; resizeGrid();
  document.getElementById('name').value = d.name || fallbackName || 'hideaway';
  buildTexPalette();
  draw();
  return true;
}

document.getElementById('open').onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  f.text().then(t => {
    before = snapshot();
    if (openData(JSON.parse(t), f.name.replace(/\.json$/, ''))) { undoStack.push(before); redoStack.length = 0; }
    before = null;
  });
  e.target.value = '';
};

buildObjPalette();
let start = null;
try { start = JSON.parse(load('ugHideawayEditor2') || 'null'); } catch (e) { start = null; }
if (!(start && openData(start))) {
  N = 32; blank(32); resizeGrid();
  document.getElementById('name').value = 'hideaway_grassland';
  buildTexPalette();
  draw();
}
setTool('.');
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {
  const view = document.getElementById('view');
  const canvas = document.getElementById('view3d');
  if (!window.THREE) {
    document.getElementById('viewHint').textContent = 'The 3D view needs an internet connection to load three.js.';
    return;
  }
  function Group() { return { pos: [], uv: [], col: [] }; }
  function push(g, p, uv, c) { g.pos.push(p[0], p[2], -p[1]); g.uv.push(uv[0], uv[1]); g.col.push(c[0], c[1], c[2]); }

  const fallback = {};
  function piece(sig) {
    if (KIT.pieces[sig]) return KIT.pieces[sig].tris;
    if (fallback[sig] === undefined) {
      let best = null;
      for (const cand of Object.keys(KIT.pieces)) {
        if (cand[4] !== sig[4]) continue;
        let score = 0;
        for (let i = 0; i < 9; i++) score += WEIGHTS[i] * Math.abs(+cand[i] - +sig[i]);
        if (!best || score < best[0]) best = [score, cand];
      }
      fallback[sig] = best ? best[1] : null;
    }
    return fallback[sig] ? KIT.pieces[fallback[sig]].tris : [];
  }

  function transformedSig(sig, m) {
    const out = new Array(9);
    for (let i = 0; i < 9; i++) {
      const dx = i % 3 - 1, dy = Math.floor(i / 3) - 1;
      const tx = m[0] * dx + m[1] * dy, ty = m[2] * dx + m[3] * dy;
      out[(ty + 1) * 3 + tx + 1] = sig[i];
    }
    return out.join('');
  }
  function untransform(tris, m) {
    const det = m[0] * m[3] - m[1] * m[2];
    const ia = m[3] / det, ib = -m[1] / det, ic = -m[2] / det, id = m[0] / det;
    return tris.map(t => {
      let p = t.p.map(q => { const gx = q[0] - 8, gy = -(q[1] - 8); return [ia * gx + ib * gy + 8, -(ic * gx + id * gy) + 8, q[2]]; });
      let uv = t.uv, c = t.c;
      if (det < 0) { p = [p[0], p[2], p[1]]; uv = [uv[0], uv[2], uv[1]]; c = [c[0], c[2], c[1]]; }
      return { m: t.m, p, uv, c };
    });
  }
  const waterCache = {};
  function waterPiece(sig, kit) {
    const ck = kit + sig;
    if (waterCache[ck] !== undefined) return waterCache[ck];
    const pieces = WATER_KIT.kits[kit].pieces;
    let best = null;
    for (const m of SYMMETRIES) {
      const t = transformedSig(sig, m);
      if (pieces[t] && (!best || pieces[t].count > pieces[best[0]].count)) best = [t, m];
    }
    if (!best) {
      let score = null;
      for (const cand of Object.keys(pieces)) {
        if (cand[4] !== sig[4]) continue;
        let s = 0;
        for (let i = 0; i < 9; i++) if (cand[i] !== sig[i]) s += WEIGHTS[i];
        if (score === null || s < score) { score = s; best = [cand, SYMMETRIES[0]]; }
      }
    }
    return (waterCache[ck] = best ? untransform(pieces[best[0]].tris, best[1]) : []);
  }

  function buildTerrain() {
    const lv = levels(), L = lv.L, SL = lv.slope;
    const isWater = (x, z) => inside(x, z) && T[z][x] === '~' && L[z][x] === 0 && !SL[z][x];
    function waterSig(x, z) {
      if ((T[z][x] !== '.' && T[z][x] !== '~') || L[z][x] !== 0 || SL[z][x]) return null;
      let sig = '';
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        if (inside(x + dx, z + dy) && L[z + dy][x + dx] !== 0) return null;
        sig += isWater(x + dx, z + dy) ? 'w' : 'l';
      }
      return sig.includes('w') ? sig : null;
    }
    function nearestPaint(x, z, kind) {
      if (T[z][x] === kind && Pn[z][x]) return Pn[z][x];
      for (let k = 1; k < 5; k++) for (let dy = -k; dy <= k; dy++) for (let dx = -k; dx <= k; dx++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== k || !inside(x + dx, z + dy)) continue;
        if (T[z + dy][x + dx] === kind && Pn[z + dy][x + dx]) return Pn[z + dy][x + dx];
      }
      return kind === '~' ? '@liquid' : '@floor';
    }
    const info = (x, z) => inside(x, z) ? [L[z][x], SL[z][x]] : null;
    const same = (a, b) => a && a[0] === b[0] && a[1] === b[1];
    function code(x, z) {
      const level = L[z][x], slope = SL[z][x];
      let centre, o;
      if (slope) {
        const base = level - 1;
        let lowFlat = false;
        for (const [dx, dy] of NB) if ((dx || dy) && same(info(x + dx, z + dy), [base, false])) lowFlat = true;
        [centre, o] = lowFlat ? [1, base] : [2, base - 1];
      } else { centre = 0; o = level; }
      let sig = '';
      for (const [dx, dy] of NB) {
        if (!dx && !dy) { sig += centre; continue; }
        const n = info(x + dx, z + dy);
        if (!n) { sig += '3'; continue; }
        const rel = n[0] - o;
        let v;
        if (n[1]) v = Math.max(0, Math.min(3, rel));
        else if (rel <= 0) v = 0;
        else if (rel === 1) v = centre !== 2 ? 2 : 1;
        else v = 3;
        sig += v;
      }
      return [sig, o];
    }
    function paintAt(x, z, level) {
      if (same(info(x, z), [level, false]) && Pn[z][x]) return Pn[z][x];
      for (let k = 1; k < 5; k++) for (let dy = -k; dy <= k; dy++) for (let dx = -k; dx <= k; dx++) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) !== k) continue;
        if (same(info(x + dx, z + dy), [level, false]) && Pn[z + dy][x + dx]) return Pn[z + dy][x + dx];
      }
      return Pn[z][x] || '@floor';
    }
    const b = BIOMES[biome], walls = 'walls_' + b.walls + '/';
    const matPath = m => WALL_TEXTURES.includes(m) ? walls + m : (m === 'dun_dhole' || m === 'dun_ent2') ? m : texPath(m);
    const tiles = [];
    for (let z = 0; z < N; z++) {
      tiles.push([]);
      for (let x = 0; x < N; x++) {
        const t = T[z][x], level = L[z][x], slope = SL[z][x];
        const out = [];
        const wsig = waterSig(x, z);
        if (wsig) {
          const liquid = nearestPaint(x, z, '~'), lname = nameOf(liquid);
          const kit = WATER_KIT.kits[lname] ? lname : 'sea';
          for (const tr of waterPiece(wsig, kit)) {
            let path, world = false;
            if (tr.m === 'floor') { path = texPath(nearestPaint(x, z, '.')); world = true; }
            else if (tr.m === 'water') { path = texPath(liquid); world = true; }
            else { path = 'floors/' + tr.m; world = tr.m === 'puddle_b'; }
            const shade = (tr.m === 'water' || tr.m === 'puddle_b') ? 1 : 0.81;
            out.push({ path, p: tr.p, uv: tr.uv, c: tr.c.map(c => c.map(v => v * shade)), w: world });
          }
        } else if (!(!slope && (t === '#' || t === 'X') && !Pn[z][x])) {
          const [sig, o] = code(x, z);
          const topPaint = (t === '#' || t === 'X') ? Pn[z][x] : null;
          const edge = edgeFor(x, z, lv);
          for (const tr of piece(sig)) {
            const zs = tr.p.map(p => p[2]);
            const flat = Math.max(...zs) - Math.min(...zs) < 0.01;
            let path, cols = tr.c, world = false;
            let uv = tr.uv;
            if (BASE_FLOORS.includes(tr.m) && Math.max(...zs) < 1 && edge && edge.fill) { path = texPath(edge.fill); world = true; }
            else if (BASE_FLOORS.includes(tr.m) && Math.max(...zs) < 1 && edge) { path = edge.sheet; uv = tr.p.map(p => edgeUV(edge.corners, p[0], p[1])); }
            else if (BASE_FLOORS.includes(tr.m) && Math.max(...zs) < 1) { path = texPath(paintAt(x, z, o)); world = true; }
            else if (flat && (TOP_FLOORS.includes(tr.m) || BASE_FLOORS.includes(tr.m)) && topPaint && Math.abs(o * STOREY + zs[0] - level * STOREY) < 0.5) {
              path = texPath(topPaint); world = true; cols = [[0.81, 0.81, 0.81], [0.81, 0.81, 0.81], [0.81, 0.81, 0.81]];
            } else if (BASE_FLOORS.includes(tr.m)) path = walls + 'dun_floor';
            else if (tr.m === 'black') { path = walls + 'dun_floor2'; cols = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]; }
            else path = matPath(tr.m);
            out.push({ path, p: tr.p.map(p => [p[0], p[1], p[2] + o * STOREY]), uv, c: cols, w: world });
          }
        }
        tiles[z].push(out);
      }
    }
    for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
      if (T[z][x] !== 'X') continue;
      const f = exitFront(x, z);
      if (!f) continue;
      const st = KIT.doors[FRONT_TO_DOOR[f[0] + ',' + f[1]]];
      for (const cell of st.cells) {
        const xx = x + cell.dx, zz = z + cell.dy;
        if (!inside(xx, zz)) continue;
        const out = [];
        for (const tr of cell.tris) {
          if (tr.m === 'black') continue;
          if (BASE_FLOORS.includes(tr.m) && Math.max(...tr.p.map(p => p[2])) < 1) out.push({ path: texPath(paintAt(xx, zz, 0)), p: tr.p, uv: tr.uv, c: tr.c, w: true });
          else out.push({ path: matPath(tr.m), p: tr.p, uv: tr.uv, c: tr.c, w: false });
        }
        tiles[zz][xx] = out;
      }
    }
    const groups = {}, half = N * 8;
    for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
      const x0 = -half + 16 * x, y0 = half - 16 * (z + 1), gx0 = 16 * x, gy0 = 16 * (N - z - 1);
      for (const tr of tiles[z][x]) {
        const g = groups[tr.path] || (groups[tr.path] = Group());
        const sz = HSIZE[tr.path] || [16, 16];
        for (let k = 0; k < 3; k++) {
          const p = tr.p[k];
          const uv = tr.w ? [(gx0 + p[0]) / sz[0], (gy0 + p[1]) / sz[1]] : tr.uv[k];
          push(g, [x0 + p[0], y0 + p[1], p[2]], uv, tr.c[k]);
        }
      }
    }
    return { groups, L };
  }

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x26232a);
  const camera = new THREE.PerspectiveCamera(30, 1, 10, 8000);
  const loader = new THREE.TextureLoader();
  const mats = {};
  function mat(src) {
    if (!mats[src]) {
      const t = loader.load(src, () => render());
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.magFilter = THREE.NearestFilter;
      t.minFilter = THREE.NearestFilter;
      const blend = src === HTEX['floors/' + WATER_KIT.bank];
      const see = TEX_ALPHA[src];
      if (see) t.format = THREE.RGBFormat;
      mats[src] = new THREE.MeshBasicMaterial({ map: t, vertexColors: true, side: THREE.DoubleSide, alphaTest: blend ? 0.02 : (see ? 0 : 0.1), transparent: blend || !!see, opacity: see || 1, depthWrite: !(blend || see) });
    }
    return mats[src];
  }
  const plain = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide });
  let meshes = [];

  const cam = { theta: 0, phi: 0.95, dist: 1250, tx: 0, tz: 0 };
  function resetCam() { cam.theta = 0; cam.phi = 0.95; cam.dist = 1250 * N / 32; cam.tx = 0; cam.tz = 0; }
  window.resetView3d = () => { resetCam(); last = ''; window.schedule3d(); };
  function placeCamera() {
    const sp = Math.sin(cam.phi), cp = Math.cos(cam.phi);
    camera.position.set(cam.tx + cam.dist * sp * Math.sin(cam.theta), cam.dist * cp, cam.tz + cam.dist * sp * Math.cos(cam.theta));
    camera.lookAt(cam.tx, 0, cam.tz);
  }
  function resize() {
    const w = canvas.clientWidth || 640, h = canvas.clientHeight || 640;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  function render() { placeCamera(); renderer.render(scene, camera); }

  function addGroup(g, material, matrix) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(g.pos, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(g.uv, 2));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(g.col, 3));
    const mesh = new THREE.Mesh(geo, material);
    if (matrix) mesh.applyMatrix4(matrix);
    scene.add(mesh);
    meshes.push(mesh);
  }

  function rebuild() {
    for (const m of meshes) { scene.remove(m); m.geometry.dispose(); }
    meshes = [];
    const built = buildTerrain();
    for (const [path, g] of Object.entries(built.groups)) addGroup(g, HTEX[path] ? mat(HTEX[path]) : plain);
    const half = N * 8;
    for (const o of objects) {
      const p = PROPS[o.key];
      const w = o.w || 1, h = o.h || 1;
      const cx = -half + 16 * (o.x + w / 2), cy = half - 16 * (o.z + h / 2), cz = built.L[o.z][o.x] * STOREY;
      const a = (o.rot || 0) * Math.PI / 2, ca = Math.round(Math.cos(a)), sa = Math.round(Math.sin(a));
      if (p && p.mesh) {
        for (const g of p.mesh) {
          const grp = Group();
          for (let i = 0, k = 0; i < g.pos.length; i += 3, k++) {
            const x = g.pos[i], y = g.pos[i + 1];
            push(grp, [cx + x * ca - y * sa, cy + x * sa + y * ca, cz + g.pos[i + 2]], [g.uv[2 * k], g.uv[2 * k + 1]], [g.col[3 * k], g.col[3 * k + 1], g.col[3 * k + 2]]);
          }
          addGroup(grp, g.img ? mat(g.img) : plain);
        }
      } else {
        const box = new THREE.Mesh(new THREE.BoxGeometry(16 * w - 2, 24, 16 * h - 2), new THREE.MeshBasicMaterial({ color: 0xe0a458, wireframe: true }));
        box.position.set(cx, cz + 12, -cy);
        scene.add(box); meshes.push(box);
      }
    }
    render();
  }

  let last = '', timer = null;
  window.schedule3d = () => {
    if (view.hidden || !T.length) return;
    const snap = biome + snapshot();
    if (snap === last) return;
    last = snap;
    clearTimeout(timer);
    timer = setTimeout(rebuild, 120);
  };

  let drag = null;
  canvas.addEventListener('contextmenu', e => e.preventDefault());
  canvas.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey }; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', e => {
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    drag.x = e.clientX; drag.y = e.clientY;
    if (drag.pan) {
      const k = cam.dist / 600, c = Math.cos(cam.theta), s = Math.sin(cam.theta);
      cam.tx -= (dx * c + dy * s) * k;
      cam.tz -= (-dx * s + dy * c) * k;
    } else {
      cam.theta -= dx * 0.008;
      cam.phi = Math.max(0.05, Math.min(1.5, cam.phi - dy * 0.008));
    }
    render();
  });
  canvas.addEventListener('pointerup', () => { drag = null; });
  canvas.addEventListener('wheel', e => { e.preventDefault(); cam.dist = Math.max(150, Math.min(6000, cam.dist * Math.exp(e.deltaY * 0.001))); render(); }, { passive: false });

  document.getElementById('resetView').onclick = () => { resetCam(); render(); };
  document.getElementById('toggle3d').onclick = function () {
    view.hidden = !view.hidden;
    this.classList.toggle('on', !view.hidden);
    try { localStorage.setItem('ugHideawayEditor3d', view.hidden ? '0' : '1'); } catch (e) {}
    if (!view.hidden) { resize(); last = ''; window.schedule3d(); }
  };
  let pref = null;
  try { pref = localStorage.getItem('ugHideawayEditor3d'); } catch (e) {}
  if (pref === '0') { view.hidden = true; document.getElementById('toggle3d').classList.remove('on'); }
  window.addEventListener('resize', () => { resize(); render(); });
  resize();
  resetCam();
  window.schedule3d();
})();
</script>
</body>
</html>
'''

out = (html.replace('__BIOMES__', json.dumps(biomes)).replace('__HTEX__', json.dumps(tex)).replace('__HSIZE__', json.dumps(sizes))
       .replace('__FLOORS__', json.dumps(floors)).replace('__PROPS__', json.dumps(props, separators=(',', ':')))
       .replace('__KIT__', json.dumps(kit, separators=(',', ':'))).replace('__EDGES__', json.dumps(edges, separators=(',', ':')))
       .replace('__WATER__', json.dumps(water_kit, separators=(',', ':'))).replace('__ALPHA__', json.dumps(alpha)))
open(os.path.join(HERE, 'hideaway_editor.html'), 'w', encoding='utf-8').write(out)
print('wrote hideaway_editor.html with %d textures and %d objects' % (len(floors), len(props)))
