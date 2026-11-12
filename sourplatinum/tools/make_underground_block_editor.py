import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKS = os.path.join(HERE, 'underground_block_editor_assets', 'blocks')


def key(name):
    parts = name.split('_')
    return (int(parts[1]), len(parts))


blocks = {}
for fn in sorted(os.listdir(BLOCKS), key=lambda f: key(os.path.splitext(f)[0])):
    if fn.endswith('.json'):
        data = json.load(open(os.path.join(BLOCKS, fn)))
        blocks[data['name']] = data['tiles']

textures = {}
for name in ('ug_floor', 'ug_map_wall', 'ug_wall_stem'):
    raw = open(os.path.join(HERE, 'underground_block_editor_assets', name + '.png'), 'rb').read()
    textures[name] = 'data:image/png;base64,' + base64.b64encode(raw).decode()

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Underground Block Editor</title>
<style>
:root {
  --bg: #1d1b1a;
  --panel: #2a2725;
  --text: #ece6df;
  --muted: #a99f95;
  --accent: #e0a458;
  --bad: #e5484d;
  --ok: #46a758;
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
#view[hidden] { display: none; }
#side { display: flex; flex-direction: column; gap: 12px; width: 380px; max-width: 100%; }
.panel { background: var(--panel); padding: 10px 12px; border-radius: 8px; }
.panel h2 { font-size: 13px; margin: 0 0 8px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
.tools { display: flex; gap: 6px; flex-wrap: wrap; }
.swatch { display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
#status { min-height: 1.4em; }
#warnings { color: var(--bad); }
code { background: #00000055; padding: 1px 4px; border-radius: 4px; }
p { margin: 6px 0; color: var(--muted); }
p b { color: var(--text); }
</style>
</head>
<body>
<header>
  <h1>Underground Block Editor</h1>
  <select id="blockSelect"></select>
  <input type="text" id="name" size="16" title="Block name">
  <button id="undo">Undo</button>
  <button id="redo">Redo</button>
  <button id="save">Save block file</button>
  <label class="btn">Open block file<input id="open" type="file" accept=".json" hidden></label>
  <button id="toggle3d" class="on">3D view</button>
  <button id="resetView">Reset camera</button>
</header>
<main>
  <canvas id="grid"></canvas>
  <div id="view"><canvas id="view3d"></canvas><div id="viewHint">Drag to orbit &middot; right-drag to pan &middot; scroll to zoom</div></div>
  <div id="side">
    <div class="panel">
      <h2>Paint</h2>
      <div class="tools">
        <button data-tool="." class="on"><span class="swatch" style="background:#d6ba8c"></span>Floor (1)</button>
        <button data-tool="#"><span class="swatch" style="background:#3a281e"></span>Rock (2)</button>
        <button data-tool="D"><span class="swatch" style="background:#000;border:1px solid #b5713f"></span>Door (3)</button>
      </div>
      <p>Drag to paint. Hold <b>Shift</b> while dragging to fill a rectangle. Right-click a tile to pick up its type.</p>
    </div>
    <div class="panel">
      <h2>Block</h2>
      <div id="status"></div>
      <div id="warnings"></div>
    </div>
    <div class="panel">
      <h2>Building the model</h2>
      <p><b>Floor</b> tiles are walkable tunnel. The walls, rails and corners are added around them automatically.</p>
      <p><b>Door</b> tiles go in the rock right next to one floor tile. The doorway is two tiles wide, centred on the door tile, and the door tile is the warp.</p>
      <p>Save the block file, then drag it onto <code>build_underground_block.bat</code> in the tools folder. It writes <code>NAME_map_data.bin</code> next to the block file: the finished block (collision plus model) ready to use as a <code>map_data</code> file. The <code>.imd</code> and <code>.nsbmd</code> model files are written too.</p>
    </div>
  </div>
</main>
<script>
const BLOCKS = __BLOCKS__;
const N = 32, S = 20;
const COLORS = { '.': '#d6ba8c', '#': '#3a281e', 'D': '#000000' };
const cv = document.getElementById('grid');
cv.width = N * S; cv.height = N * S;
const ctx = cv.getContext('2d');
let grid = null, tool = '.', painting = false, rectStart = null, hover = null, before = null;
const undoStack = [], redoStack = [];

function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

function setGrid(tiles, name) {
  grid = tiles.map(r => r.split(''));
  document.getElementById('name').value = name;
  undoStack.length = 0; redoStack.length = 0;
  draw();
}

function snapshot() { return grid.map(r => r.join('')); }

function isFloor(x, z) {
  x = Math.max(0, Math.min(N - 1, x)); z = Math.max(0, Math.min(N - 1, z));
  return grid[z][x] === '.';
}

function doorProblems() {
  const bad = [];
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    if (grid[z][x] !== 'D') continue;
    const n = [[0, 1], [0, -1], [1, 0], [-1, 0]].filter(([dx, dz]) => {
      const xx = x + dx, zz = z + dz;
      return xx >= 0 && zz >= 0 && xx < N && zz < N && grid[zz][xx] === '.';
    }).length;
    if (n !== 1) bad.push([x, z, n]);
  }
  return bad;
}

function doorFacing(x, z) {
  for (const [dx, dz] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const xx = x + dx, zz = z + dz;
    if (xx >= 0 && zz >= 0 && xx < N && zz < N && grid[zz][xx] === '.') return [dx, dz];
  }
  return null;
}

function draw() {
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    ctx.fillStyle = COLORS[grid[z][x]] || '#f0f';
    ctx.fillRect(x * S, z * S, S, S);
  }
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    if (grid[z][x] !== 'D') continue;
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(x * S + 2, z * S + 2, S - 4, S - 4);
    const f = doorFacing(x, z);
    ctx.fillStyle = '#b5713f';
    if (f && f[0] === 0) {
      const y = f[1] > 0 ? (z + 1) * S - 4 : z * S;
      ctx.fillRect(x * S - S / 2 - 2, y, 4, 4);
      ctx.fillRect(x * S + S + S / 2 - 2, y, 4, 4);
      ctx.fillStyle = '#000';
      ctx.fillRect(x * S - S / 2 + 2, f[1] > 0 ? (z + 1) * S - 3 : z * S, S * 2 - 4, 3);
    } else if (f) {
      const xx = f[0] > 0 ? (x + 1) * S - 4 : x * S;
      ctx.fillRect(xx, z * S - S / 2 - 2, 4, 4);
      ctx.fillRect(xx, z * S + S + S / 2 - 2, 4, 4);
      ctx.fillStyle = '#000';
      ctx.fillRect(f[0] > 0 ? (x + 1) * S - 3 : x * S, z * S - S / 2 + 2, 3, S * 2 - 4);
    }
  }
  ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1;
  for (let i = 0; i <= N; i++) {
    ctx.beginPath(); ctx.moveTo(i * S + 0.5, 0); ctx.lineTo(i * S + 0.5, N * S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * S + 0.5); ctx.lineTo(N * S, i * S + 0.5); ctx.stroke();
  }
  ctx.strokeStyle = 'rgba(255,255,255,0.35)';
  for (let i = 0; i <= N; i += 8) {
    ctx.beginPath(); ctx.moveTo(i * S + 0.5, 0); ctx.lineTo(i * S + 0.5, N * S); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * S + 0.5); ctx.lineTo(N * S, i * S + 0.5); ctx.stroke();
  }
  const bad = doorProblems();
  ctx.strokeStyle = '#e5484d'; ctx.lineWidth = 2;
  for (const [x, z] of bad) ctx.strokeRect(x * S + 1, z * S + 1, S - 2, S - 2);
  if (rectStart && hover) {
    const [x0, z0, x1, z1] = rectBounds(rectStart, hover);
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(x0 * S + 1, z0 * S + 1, (x1 - x0 + 1) * S - 2, (z1 - z0 + 1) * S - 2);
  } else if (hover) {
    ctx.strokeStyle = '#e0a458'; ctx.lineWidth = 2;
    ctx.strokeRect(hover[0] * S + 1, hover[1] * S + 1, S - 2, S - 2);
  }
  const counts = { '.': 0, '#': 0, 'D': 0 };
  grid.flat().forEach(c => counts[c] = (counts[c] || 0) + 1);
  document.getElementById('status').innerHTML = counts['.'] + ' floor, ' + counts['#'] + ' rock, ' + counts['D'] + ' door tile(s)' + (hover ? ' &middot; tile ' + hover[0] + ', ' + hover[1] : '');
  document.getElementById('warnings').textContent = bad.length ? bad.length + ' door(s) need exactly one floor tile next to them (marked red).' : '';
  store('ugBlockEditor', JSON.stringify({ name: document.getElementById('name').value, tiles: snapshot() }));
  if (window.schedule3d) window.schedule3d();
}

function rectBounds(a, b) {
  return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];
}

function tileAt(e) {
  const r = cv.getBoundingClientRect();
  const x = Math.floor((e.clientX - r.left) / r.width * N), z = Math.floor((e.clientY - r.top) / r.height * N);
  return x >= 0 && z >= 0 && x < N && z < N ? [x, z] : null;
}

function commit() {
  if (before && before.join('') !== snapshot().join('')) { undoStack.push(before); redoStack.length = 0; }
  before = null;
}

cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('pointerdown', e => {
  const t = tileAt(e); if (!t) return;
  if (e.button === 2) { setTool(grid[t[1]][t[0]]); return; }
  before = snapshot();
  cv.setPointerCapture(e.pointerId);
  if (e.shiftKey) { rectStart = t; hover = t; draw(); return; }
  painting = t; grid[t[1]][t[0]] = tool; draw();
});
cv.addEventListener('pointermove', e => {
  const t = tileAt(e); hover = t;
  if (painting && t) {
    const [ax, az] = painting, steps = Math.max(Math.abs(t[0] - ax), Math.abs(t[1] - az), 1);
    for (let i = 0; i <= steps; i++) {
      const x = Math.round(ax + (t[0] - ax) * i / steps), z = Math.round(az + (t[1] - az) * i / steps);
      grid[z][x] = tool;
    }
    painting = t;
  }
  draw();
});
cv.addEventListener('pointerup', e => {
  if (rectStart && hover) {
    const [x0, z0, x1, z1] = rectBounds(rectStart, hover);
    for (let z = z0; z <= z1; z++) for (let x = x0; x <= x1; x++) grid[z][x] = tool;
  }
  painting = false; rectStart = null; commit(); draw();
});
cv.addEventListener('pointerleave', () => { if (!painting && !rectStart) { hover = null; draw(); } });

function setTool(t) {
  tool = t;
  document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('on', b.dataset.tool === t));
}
document.querySelectorAll('[data-tool]').forEach(b => b.addEventListener('click', () => setTool(b.dataset.tool)));
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === '1') setTool('.');
  if (e.key === '2') setTool('#');
  if (e.key === '3') setTool('D');
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z') { e.preventDefault(); e.shiftKey ? redo() : undo(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); }
});

function undo() { if (!undoStack.length) return; redoStack.push(snapshot()); grid = undoStack.pop().map(r => r.split('')); draw(); }
function redo() { if (!redoStack.length) return; undoStack.push(snapshot()); grid = redoStack.pop().map(r => r.split('')); draw(); }
document.getElementById('undo').onclick = undo;
document.getElementById('redo').onclick = redo;

const sel = document.getElementById('blockSelect');
for (const name of Object.keys(BLOCKS)) {
  const o = document.createElement('option');
  o.value = name; o.textContent = name.replace('block_', 'Block ').replace('_H', ' H');
  sel.appendChild(o);
}
sel.onchange = () => setGrid(BLOCKS[sel.value], sel.value);

document.getElementById('name').addEventListener('input', draw);

document.getElementById('save').onclick = () => {
  const name = (document.getElementById('name').value || 'block').replace(/[^A-Za-z0-9_-]/g, '_');
  const blob = new Blob([JSON.stringify({ name, tiles: snapshot() }, null, 1)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name + '.json'; a.click();
  URL.revokeObjectURL(a.href);
};

document.getElementById('open').onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  f.text().then(t => {
    const d = JSON.parse(t);
    if (!Array.isArray(d.tiles) || d.tiles.length !== N || d.tiles.some(r => r.length !== N)) { alert('Not a 32x32 block file'); return; }
    setGrid(d.tiles, d.name || f.name.replace(/\.json$/, ''));
  });
  e.target.value = '';
};

const saved = load('ugBlockEditor');
let start = null;
try { start = saved ? JSON.parse(saved) : null; } catch (e) { start = null; }
if (start && Array.isArray(start.tiles) && start.tiles.length === N) {
  setGrid(start.tiles, start.name || 'block');
  if (BLOCKS[start.name]) sel.value = start.name;
} else {
  sel.value = 'block_656_H';
  setGrid(BLOCKS['block_656_H'], 'block_656_H');
}
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function () {
  const TEX = __TEXTURES__;
  const view = document.getElementById('view');
  const canvas = document.getElementById('view3d');
  if (!window.THREE) {
    document.getElementById('viewHint').textContent = 'The 3D view needs an internet connection to load three.js.';
    return;
  }
  const T = 16, HALF = 256, TOP = 58, FZ = -2, MZ = 16;
  const RAIL_LO = 36.9, RAIL_HI = 47.6, RAIL_T = 6;
  const DOOR_W = 32, DOOR_H = 30, BEAM_W = 6, BEAM_TOP = 36, BEAM_OUT = 4;
  const PROF = { N: [14.6, 33.8], S: [18.7, 45.9], W: [14.8, 37.9], E: [14.8, 37.9] };
  const RAIL_OFF = { N: 4.8, S: 2.9, W: 5.9, E: 5.9 };
  const DIRS = { N: [0, 1], S: [0, -1], E: [1, 0], W: [-1, 0] };

  function elev(n, e) {
    const [up, tot] = PROF[n], lo = tot - up;
    if (e <= 0) return FZ;
    if (e < lo) return FZ + (MZ - FZ) * e / lo;
    if (e < tot) return MZ + (TOP - MZ) * (e - lo) / up;
    return TOP;
  }
  function inv(n, z) {
    const [up, tot] = PROF[n], lo = tot - up;
    if (z <= FZ) return 0;
    if (z <= MZ) return lo * (z - FZ) / (MZ - FZ);
    return lo + up * Math.min(1, (z - MZ) / (TOP - MZ));
  }
  function railE(n) { const tot = PROF[n][1], o = RAIL_OFF[n]; return [tot - o - RAIL_T, tot - o]; }
  function fl(tx, tz) {
    tx = Math.max(0, Math.min(31, tx)); tz = Math.max(0, Math.min(31, tz));
    return grid[tz][tx] === '.';
  }
  function rect(tx, tz) { return [-HALF + T * tx, -HALF + T * (tx + 1), HALF - T * (tz + 1), HALF - T * tz]; }

  function height(x, y) {
    const tx = Math.floor((x + HALF) / T), tz = Math.floor((HALF - y) / T);
    let best = TOP;
    for (let dz = -3; dz <= 3; dz++) for (let dx = -3; dx <= 3; dx++) {
      if (!fl(tx + dx, tz + dz)) continue;
      const [x0, x1, y0, y1] = rect(tx + dx, tz + dz);
      const zx = x > x1 ? elev('E', x - x1) : (x < x0 ? elev('W', x0 - x) : FZ);
      const zy = y > y1 ? elev('N', y - y1) : (y < y0 ? elev('S', y0 - y) : FZ);
      const g = Math.max(zx, zy);
      if (g < best) best = g;
    }
    return best;
  }

  function knots() {
    const xs = [-HALF, HALF], ys = [-HALF, HALF];
    for (let tz = 0; tz < 32; tz++) for (let tx = -1; tx < 32; tx++) {
      const a = fl(tx, tz), b = fl(tx + 1, tz);
      if (a === b) continue;
      const xb = -HALF + T * (tx + 1), n = a ? 'E' : 'W', s = a ? 1 : -1, [up, tot] = PROF[n];
      xs.push(xb, xb + s * (tot - up), xb + s * tot);
      if (n === 'W') xs.push(xb + 16);
    }
    for (let tx = 0; tx < 32; tx++) for (let tz = -1; tz < 32; tz++) {
      const a = fl(tx, tz), b = fl(tx, tz + 1);
      if (a === b) continue;
      const yb = HALF - T * (tz + 1), n = a ? 'S' : 'N', s = a ? -1 : 1, [up, tot] = PROF[n];
      ys.push(yb, yb + s * (tot - up), yb + s * tot);
      if (n === 'N') ys.push(yb - 16);
    }
    const clean = v => {
      const out = [];
      v.filter(a => a >= -HALF - 1e-6 && a <= HALF + 1e-6).sort((a, b) => a - b).forEach(a => {
        if (!out.length || a - out[out.length - 1] > 0.05) out.push(a);
      });
      return out;
    };
    return [clean(xs), clean(ys)];
  }

  function Group() { return { pos: [], uv: [], col: [] }; }
  function push(g, p, uv, c) {
    g.pos.push(p[0], p[2], -p[1]);
    g.uv.push(uv[0], uv[1]);
    g.col.push(c[0], c[1], c[2]);
  }
  function tri(g, a, b, c) { push(g, a[0], a[1], a[2]); push(g, b[0], b[1], b[2]); push(g, c[0], c[1], c[2]); }
  function quad(g, a, b, c, d) { tri(g, a, b, c); tri(g, a, c, d); }

  function wallDistance(x, y, dx, dy) {
    const tx = Math.floor((x + HALF) / T), tz = Math.floor((HALF - y) / T);
    for (let k = 0; k < 3; k++) {
      const nx = tx + dx * k, nz = tz - dy * k;
      if (!fl(nx, nz)) {
        const [x0, x1, y0, y1] = rect(nx, nz);
        if (dx > 0) return x0 - x;
        if (dx < 0) return x - x1;
        if (dy > 0) return y0 - y;
        return y1 - y;
      }
    }
    return 64;
  }
  function floorShade(x, y) {
    const west = Math.max(0, 1 - Math.max(0, wallDistance(x, y, -1, 0)) / 16);
    const north = Math.max(0, 1 - Math.max(0, wallDistance(x, y, 0, 1)) / 16);
    return 1 - 0.19 * Math.max(west, north) - 0.04 * Math.min(west, north);
  }
  function wallName(n) {
    if (Math.abs(n[0]) >= Math.abs(n[1])) return n[0] > 0 ? 'W' : 'E';
    return n[1] > 0 ? 'S' : 'N';
  }

  function terrain(floorG, wallG) {
    const [xs, ys] = knots();
    const cache = new Map();
    const h = (x, y) => {
      const k = x.toFixed(3) + ',' + y.toFixed(3);
      let v = cache.get(k);
      if (v === undefined) { v = height(x, y); cache.set(k, v); }
      return v;
    };
    const emit = (p) => {
      const zs = p.map(q => q[2]);
      const mn = Math.min(...zs), mx = Math.max(...zs);
      if (mx - mn < 0.05 && Math.abs(mn - FZ) < 0.05) {
        {
          const cx = (p[0][0] + p[1][0] + p[2][0]) / 3, cy = (p[0][1] + p[1][1] + p[2][1]) / 3;
          tri(floorG, ...p.map(q => { const s = floorShade(q[0] + (cx - q[0]) * 0.001, q[1] + (cy - q[1]) * 0.001); return [q, [q[0] / 64, q[1] / 64], [s, s, s]]; }));
        }
        return;
      }
      if (mx - mn < 0.05 && Math.abs(mn - TOP) < 0.05) {
        tri(wallG, ...p.map(q => [q, [0, 0], [0, 0, 0]]));
        return;
      }
      const u = [p[1][0] - p[0][0], p[1][1] - p[0][1], p[1][2] - p[0][2]];
      const v = [p[2][0] - p[0][0], p[2][1] - p[0][1], p[2][2] - p[0][2]];
      let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
      if (n[2] < 0) n = n.map(a => -a);
      const name = wallName(n);
      tri(wallG, ...p.map(q => {
        const along = (name === 'N' || name === 'S') ? q[0] : q[1];
        const shade = q[2] < MZ ? 0.75 : 1.0;
        return [q, [along / 64, 0.25 + 0.75 * (q[2] - FZ) / (TOP - FZ)], [shade, shade, shade]];
      }));
    };
    for (let i = 0; i < xs.length - 1; i++) for (let j = 0; j < ys.length - 1; j++) {
      const x0 = xs[i], x1 = xs[i + 1], y0 = ys[j], y1 = ys[j + 1];
      const p00 = [x0, y0, h(x0, y0)], p10 = [x1, y0, h(x1, y0)], p01 = [x0, y1, h(x0, y1)], p11 = [x1, y1, h(x1, y1)];
      const hc = height((x0 + x1) / 2, (y0 + y1) / 2);
      if (Math.abs((p00[2] + p11[2]) / 2 - hc) <= Math.abs((p10[2] + p01[2]) / 2 - hc)) {
        emit([p00, p10, p11]); emit([p00, p11, p01]);
      } else {
        emit([p00, p10, p01]); emit([p10, p11, p01]);
      }
    }
  }

  function chains() {
    const edges = [];
    for (let tz = 0; tz < 32; tz++) for (let tx = -1; tx < 32; tx++) {
      const a = fl(tx, tz), b = fl(tx + 1, tz);
      if (a === b) continue;
      const xb = -HALF + T * (tx + 1);
      edges.push([[xb, HALF - T * (tz + 1)], [xb, HALF - T * tz], a ? 'E' : 'W']);
    }
    for (let tx = 0; tx < 32; tx++) for (let tz = -1; tz < 32; tz++) {
      const a = fl(tx, tz), b = fl(tx, tz + 1);
      if (a === b) continue;
      const yb = HALF - T * (tz + 1);
      edges.push([[-HALF + T * tx, yb], [-HALF + T * (tx + 1), yb], a ? 'S' : 'N']);
    }
    const key = p => p[0] + ',' + p[1];
    const adj = new Map();
    edges.forEach((e, i) => {
      for (const p of [e[0], e[1]]) { const k = key(p); if (!adj.has(k)) adj.set(k, []); adj.get(k).push(i); }
    });
    const used = new Set(), out = [];
    const walk = (e, pt) => {
      const ch = [];
      while (e !== null && !used.has(e)) {
        used.add(e);
        const [p, q, n] = edges[e];
        const nxt = key(pt) === key(p) ? q : p;
        ch.push([pt, nxt, n]);
        const c = (adj.get(key(nxt)) || []).filter(k => !used.has(k));
        if (c.length === 1) e = c[0];
        else if (c.length > 1) { const perp = c.filter(k => edges[k][2] !== n); e = perp.length ? perp[0] : c[0]; }
        else e = null;
        pt = nxt;
      }
      return ch;
    };
    for (const [k, lst] of adj) {
      if (lst.length === 1 && !used.has(lst[0])) {
        const [p, q] = edges[lst[0]];
        out.push([walk(lst[0], key(p) === k ? p : q), false]);
      }
    }
    edges.forEach((e, i) => {
      if (used.has(i)) return;
      const ch = walk(i, e[0]);
      out.push([ch, ch.length > 0 && key(ch[ch.length - 1][1]) === key(ch[0][0])]);
    });
    return out;
  }

  function offset(chain, closed, which) {
    let m = [];
    for (const [p, q, n] of chain) {
      if (m.length && m[m.length - 1][2] === n) m[m.length - 1] = [m[m.length - 1][0], q, n];
      else m.push([p, q, n]);
    }
    if (closed && m.length > 1 && m[0][2] === m[m.length - 1][2]) {
      m[0] = [m[m.length - 1][0], m[0][1], m[0][2]];
      m.pop();
    }
    const line = s => {
      const [p, , n] = s, e = railE(n)[which], d = DIRS[n];
      return (n === 'E' || n === 'W') ? ['x', p[0] + d[0] * e] : ['y', p[1] + d[1] * e];
    };
    let pts = [];
    if (!closed) {
      const [p] = m[0], [ax, v] = line(m[0]);
      pts.push(ax === 'x' ? [v, p[1]] : [p[0], v]);
    }
    const cnt = m.length - (closed ? 0 : 1);
    for (let i = 0; i < cnt; i++) {
      const a = m[i], b = m[(i + 1) % m.length], la = line(a), lb = line(b);
      if (la[0] === lb[0]) { const p = a[1]; pts.push(la[0] === 'x' ? [la[1], p[1]] : [p[0], la[1]]); continue; }
      pts.push([la[0] === 'x' ? la[1] : lb[1], la[0] === 'y' ? la[1] : lb[1]]);
    }
    if (!closed) {
      const [, q] = m[m.length - 1], [ax, v] = line(m[m.length - 1]);
      pts.push(ax === 'x' ? [v, q[1]] : [q[0], v]);
    } else {
      pts.push(pts[0]);
    }
    return pts;
  }

  function rails(g) {
    const W = [0.85, 0.85, 0.85], D = [0.6, 0.6, 0.6];
    for (const [ch, closed] of chains()) {
      if (!ch.length) continue;
      const a = offset(ch, closed, 0), b = offset(ch, closed, 1);
      let s = 0;
      for (let i = 0; i < a.length - 1; i++) {
        const seg = Math.hypot(a[i + 1][0] - a[i][0], a[i + 1][1] - a[i][1]);
        const s0 = s / 64, s1 = (s + seg) / 64;
        quad(g, [[...a[i], RAIL_HI], [0, s0], W], [[...a[i + 1], RAIL_HI], [0, s1], W],
             [[...b[i + 1], RAIL_HI], [1, s1], W], [[...b[i], RAIL_HI], [1, s0], W]);
        for (const [p, c] of [[a, W], [b, D]]) {
          quad(g, [[...p[i], RAIL_LO], [0, s0], c], [[...p[i + 1], RAIL_LO], [0, s1], c],
               [[...p[i + 1], RAIL_HI], [1, s1], c], [[...p[i], RAIL_HI], [1, s0], c]);
        }
        s += seg;
      }
    }
  }

  function doors(wallG, railG) {
    const BLACK = [0, 0, 0], WOOD = [0.85, 0.85, 0.85];
    for (let tz = 0; tz < 32; tz++) for (let tx = 0; tx < 32; tx++) {
      if (grid[tz][tx] !== 'D') continue;
      for (const [name, dx, dz] of [['N', 0, 1], ['S', 0, -1], ['E', -1, 0], ['W', 1, 0]]) {
        const xx = tx + dx, zz = tz + dz;
        if (xx < 0 || zz < 0 || xx > 31 || zz > 31 || grid[zz][xx] !== '.') continue;
        const [x0, x1, y0, y1] = rect(tx, tz);
        let Wf, uc;
        if (name === 'N') { Wf = (u, e, z) => [u, y0 + e, z]; uc = (x0 + x1) / 2; }
        else if (name === 'S') { Wf = (u, e, z) => [u, y1 - e, z]; uc = (x0 + x1) / 2; }
        else if (name === 'E') { Wf = (u, e, z) => [x0 + e, u, z]; uc = (y0 + y1) / 2; }
        else { Wf = (u, e, z) => [x1 - e, u, z]; uc = (y0 + y1) / 2; }
        const d0 = uc - DOOR_W / 2, d1 = uc + DOOR_W / 2;
        const z = [0, 0], lv = [FZ, MZ, DOOR_H];
        for (let k = 0; k < 2; k++) {
          const ea = inv(name, lv[k]) - 0.6, eb = inv(name, lv[k + 1]) - 0.6;
          quad(wallG, [Wf(d0, ea, lv[k]), z, BLACK], [Wf(d1, ea, lv[k]), z, BLACK], [Wf(d1, eb, lv[k + 1]), z, BLACK], [Wf(d0, eb, lv[k + 1]), z, BLACK]);
        }
        break;
      }
    }
  }

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x26232a);
  const camera = new THREE.PerspectiveCamera(30, 1, 10, 5000);
  const loader = new THREE.TextureLoader();
  function mat(src) {
    const t = loader.load(src, () => render());
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.NearestFilter;
    t.minFilter = THREE.NearestFilter;
    return new THREE.MeshBasicMaterial({ map: t, vertexColors: true, side: THREE.DoubleSide, alphaTest: 0.1 });
  }
  const mats = { floor: mat(TEX.ug_floor), wall: mat(TEX.ug_map_wall), rail: mat(TEX.ug_wall_stem) };
  let meshes = [];

  const cam = { theta: 0, phi: 0.95, dist: 1250, tx: 0, tz: 0 };
  function resetCam() { cam.theta = 0; cam.phi = 0.95; cam.dist = 1250; cam.tx = 0; cam.tz = 0; }
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

  function rebuild() {
    for (const m of meshes) { scene.remove(m); m.geometry.dispose(); }
    meshes = [];
    const fG = Group(), wG = Group(), rG = Group();
    terrain(fG, wG);
    rails(rG);
    doors(wG, rG);
    for (const [g, m] of [[fG, mats.floor], [wG, mats.wall], [rG, mats.rail]]) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(g.pos, 3));
      geo.setAttribute('uv', new THREE.Float32BufferAttribute(g.uv, 2));
      geo.setAttribute('color', new THREE.Float32BufferAttribute(g.col, 3));
      const mesh = new THREE.Mesh(geo, m);
      scene.add(mesh);
      meshes.push(mesh);
    }
    render();
  }

  let last = '', timer = null;
  window.schedule3d = () => {
    if (view.hidden || !grid) return;
    const snap = grid.map(r => r.join('')).join('');
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
  canvas.addEventListener('wheel', e => { e.preventDefault(); cam.dist = Math.max(150, Math.min(2500, cam.dist * Math.exp(e.deltaY * 0.001))); render(); }, { passive: false });

  document.getElementById('resetView').onclick = () => { resetCam(); render(); };
  document.getElementById('toggle3d').onclick = function () {
    view.hidden = !view.hidden;
    this.classList.toggle('on', !view.hidden);
    try { localStorage.setItem('ugBlockEditor3d', view.hidden ? '0' : '1'); } catch (e) {}
    if (!view.hidden) { resize(); last = ''; window.schedule3d(); }
  };
  let pref = null;
  try { pref = localStorage.getItem('ugBlockEditor3d'); } catch (e) {}
  if (pref === '0') { view.hidden = true; document.getElementById('toggle3d').classList.remove('on'); }
  window.addEventListener('resize', () => { resize(); render(); });
  resize();
  window.schedule3d();
})();
</script>
</body>
</html>
'''

out = html.replace('__BLOCKS__', json.dumps(blocks, separators=(',', ':'))).replace('__TEXTURES__', json.dumps(textures))
open(os.path.join(HERE, 'underground_block_editor.html'), 'w', encoding='utf-8').write(out)
print('wrote underground_block_editor.html with', len(blocks), 'blocks')
