import base64
import io
import json
import struct

from PIL import Image

R = '/mnt/c/cygwin/home/Matt/SourPlatinum/'
A = R + 'sourplatinum/tools/underground_layout_editor_assets/'

d = open(R + 'res/field/maps/data/map_data_649.bin', 'rb').read()
p = d[16:16 + struct.unpack_from('<I', d, 0)[0]]
base_bits = ''.join('1' if struct.unpack_from('<H', p, 2 * i)[0] & 0x8000 else '0' for i in range(1024))

sheet = Image.open(A + 'single_tunnel_tiles.png').convert('RGB')


def tile(x, y):
    buf = io.BytesIO()
    sheet.crop((x, y, x + 32, y + 32)).save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


images = {
    'small': tile(33, 29),
    'big0': tile(12, 91),
    'big1': tile(51, 91),
    'big2': tile(12, 130),
    'big3': tile(51, 130),
}

html = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Underground Layout Editor</title>
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
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.4 system-ui, sans-serif; }
header { padding: 12px 16px; border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
header h1 { font-size: 16px; margin: 0 12px 0 0; }
button, label.btn { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: 6px; padding: 6px 10px; cursor: pointer; font: inherit; }
button:hover, label.btn:hover { border-color: var(--accent); }
button.on { border-color: var(--accent); color: var(--accent); }
.sep { width: 1px; align-self: stretch; background: var(--line); margin: 0 4px; }
main { display: flex; gap: 16px; padding: 16px; align-items: flex-start; flex-wrap: wrap; }
#grid { image-rendering: pixelated; cursor: crosshair; background: #000; max-width: 100%; }
#info { background: var(--panel); padding: 10px 14px; border-radius: 8px; color: var(--muted); width: 320px; }
#info b { color: var(--text); }
#status { min-height: 1.4em; color: var(--text); }
.bad { color: var(--bad); }
</style>
</head>
<body>
<header>
  <h1>Underground Layout Editor</h1>
  <button data-tool="tunnel" class="on">Tunnel</button>
  <button data-tool="small">Small hideaway</button>
  <button data-tool="big">Big hideaway</button>
  <button data-tool="erase">Erase</button>
  <span class="sep"></span>
  <button id="undo">Undo</button>
  <button id="clear">Clear all</button>
  <button id="save">Save layout file</button>
  <label class="btn">Open layout file<input id="open" type="file" accept=".json" hidden></label>
</header>
<main>
  <canvas id="grid"></canvas>
  <div id="info">
    <div id="status"></div>
    <p><b>Tunnel:</b> drag from square to square to draw a tunnel. Corners and junctions shape themselves. Dragging into a hideaway gives it a door on that side.</p>
    <p><b>Small hideaway:</b> click a square to turn it into a small hideaway, or back into a tunnel.</p>
    <p><b>Big hideaway:</b> click to place one. It covers 2 by 2 squares.</p>
    <p><b>Erase:</b> click or drag to turn squares back into rock. Right-click also erases with any tool.</p>
    <p>The top two rows and the left column hold the secret base rooms.</p>
    <p>Each square is one map block of 32 by 32 tiles. Tunnels are 5 tiles wide.</p>
  </div>
</main>
<script>
const BASE = '__BASE__';
const IMG = __IMAGES__;
const N = 15, T = 32, S = 2, C = T * S;
const WALL = '#3a281e', FLOOR = '#d6ba8c';
const DIRS = { n: [0, -1, 's'], e: [1, 0, 'w'], s: [0, 1, 'n'], w: [-1, 0, 'e'] };
const A0 = 13, A1 = 18;

const img = {};
let pending = 0;
for (const k in IMG) { img[k] = new Image(); pending++; img[k].onload = () => { if (--pending === 0) draw(); }; img[k].src = IMG[k]; }

function empty() { return { t: '.', n: 0, e: 0, s: 0, w: 0, q: 0 }; }
let cells = [];
for (let z = 0; z < N; z++) { cells.push([]); for (let x = 0; x < N; x++) cells[z].push(empty()); }
let tool = 'tunnel';
const history = [];

const cv = document.getElementById('grid');
cv.width = N * C; cv.height = N * C;
const ctx = cv.getContext('2d');

function isBase(x, z) { return z < 2 || x === 0; }
function inside(x, z) { return x >= 0 && z >= 0 && x < N && z < N && !isBase(x, z); }

function drawCell(x, z) {
  const c = cells[z][x], ox = x * C, oy = z * C;
  ctx.fillStyle = WALL; ctx.fillRect(ox, oy, C, C);
  if (isBase(x, z)) {
    ctx.fillStyle = '#7d6f9c';
    for (let i = 0; i < 1024; i++) if (BASE[i] === '0') ctx.fillRect(ox + (i % T) * S, oy + Math.floor(i / T) * S, S, S);
    return;
  }
  if (c.t === '.') return;
  ctx.imageSmoothingEnabled = false;
  if (c.t === 'S') ctx.drawImage(img.small, ox, oy, C, C);
  else if (c.t === 'B') ctx.drawImage(img['big' + c.q], ox, oy, C, C);
  ctx.fillStyle = FLOOR;
  if (c.t === 'T') ctx.fillRect(ox + A0 * S, oy + A0 * S, (A1 - A0) * S, (A1 - A0) * S);
  const reach = c.t === 'T' ? A0 : 3;
  if (c.n) ctx.fillRect(ox + A0 * S, oy, (A1 - A0) * S, reach * S);
  if (c.s) ctx.fillRect(ox + A0 * S, oy + (T - reach) * S, (A1 - A0) * S, reach * S);
  if (c.w) ctx.fillRect(ox, oy + A0 * S, reach * S, (A1 - A0) * S);
  if (c.e) ctx.fillRect(ox + (T - reach) * S, oy + A0 * S, reach * S, (A1 - A0) * S);
}

function regions() {
  const seen = new Set(); let n = 0;
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) {
    if (cells[z][x].t === '.' || seen.has(z * N + x)) continue;
    n++;
    const st = [[x, z]]; seen.add(z * N + x);
    while (st.length) {
      const [a, b] = st.pop(), c = cells[b][a];
      const nb = [];
      for (const d in DIRS) if (c[d]) nb.push([a + DIRS[d][0], b + DIRS[d][1]]);
      if (c.t === 'B') for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const X = a + dx, Z = b + dz;
        if (inside(X, Z) && cells[Z][X].t === 'B' && cells[Z][X].id === c.id) nb.push([X, Z]);
      }
      for (const [X, Z] of nb) if (inside(X, Z) && !seen.has(Z * N + X)) { seen.add(Z * N + X); st.push([X, Z]); }
    }
  }
  return n;
}

function draw() {
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) drawCell(x, z);
  ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.lineWidth = 1;
  for (let i = 0; i <= N; i++) {
    ctx.beginPath(); ctx.moveTo(i * C + 0.5, 0); ctx.lineTo(i * C + 0.5, N * C); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * C + 0.5); ctx.lineTo(N * C, i * C + 0.5); ctx.stroke();
  }
  const flat = cells.flat();
  const small = flat.filter(c => c.t === 'S').length, big = flat.filter(c => c.t === 'B' && c.q === 0).length;
  const tun = flat.filter(c => c.t === 'T').length, reg = regions();
  document.getElementById('status').textContent = tun + ' tunnel squares, ' + small + ' small and ' + big + ' big hideaways, ' + reg + ' separate area' + (reg === 1 ? '' : 's');
}

function snapshot() { history.push(JSON.stringify(cells)); if (history.length > 200) history.shift(); }

function eraseCell(x, z) {
  if (!inside(x, z)) return;
  const c = cells[z][x];
  if (c.t === 'B') {
    const id = c.id;
    for (let b = 0; b < N; b++) for (let a = 0; a < N; a++) if (cells[b][a].t === 'B' && cells[b][a].id === id) clearOne(a, b);
  } else clearOne(x, z);
}
function clearOne(x, z) {
  for (const d in DIRS) {
    const X = x + DIRS[d][0], Z = z + DIRS[d][1];
    if (X >= 0 && Z >= 0 && X < N && Z < N) cells[Z][X][DIRS[d][2]] = 0;
  }
  cells[z][x] = empty();
}

function connect(x0, z0, x1, z1) {
  if (!inside(x0, z0) || !inside(x1, z1)) return;
  const dx = x1 - x0, dz = z1 - z0;
  if (Math.abs(dx) + Math.abs(dz) !== 1) return;
  const d = dx === 1 ? 'e' : dx === -1 ? 'w' : dz === 1 ? 's' : 'n';
  const a = cells[z0][x0], b = cells[z1][x1];
  if (a.t === 'B' && b.t === 'B' && a.id === b.id) return;
  if (a.t === '.') a.t = 'T';
  if (b.t === '.') b.t = 'T';
  a[d] = 1; b[DIRS[d][2]] = 1;
}

let nextBig = 1;
function placeBig(x, z) {
  for (const [dx, dz] of [[0, 0], [1, 0], [0, 1], [1, 1]]) if (!inside(x + dx, z + dz) || cells[z + dz][x + dx].t !== '.') return false;
  const id = Date.now() + nextBig++;
  [[0, 0], [1, 0], [0, 1], [1, 1]].forEach(([dx, dz], q) => { const c = empty(); c.t = 'B'; c.q = q; c.id = id; cells[z + dz][x + dx] = c; });
  return true;
}

function cellAt(ev) {
  const r = cv.getBoundingClientRect();
  return { x: Math.floor((ev.clientX - r.left) * (cv.width / r.width) / C), z: Math.floor((ev.clientY - r.top) * (cv.height / r.height) / C) };
}

let drag = null;
cv.addEventListener('contextmenu', ev => ev.preventDefault());
cv.addEventListener('mousedown', ev => {
  const { x, z } = cellAt(ev);
  if (!inside(x, z)) return;
  snapshot();
  if (ev.button === 2 || tool === 'erase') { drag = { erase: true }; eraseCell(x, z); draw(); return; }
  if (ev.button !== 0) return;
  if (tool === 'tunnel') { drag = { x, z }; if (cells[z][x].t === '.') cells[z][x].t = 'T'; }
  else if (tool === 'small') { const c = cells[z][x]; if (c.t === 'S') c.t = 'T'; else if (c.t !== 'B') c.t = 'S'; }
  else if (tool === 'big') { if (!placeBig(x, z)) flash('A big hideaway needs 2 by 2 empty squares.'); }
  draw();
});
cv.addEventListener('mousemove', ev => {
  if (!drag) return;
  const { x, z } = cellAt(ev);
  if (drag.erase) { eraseCell(x, z); draw(); return; }
  if (x === drag.x && z === drag.z) return;
  while (drag.x !== x || drag.z !== z) {
    const nx = drag.x + Math.sign(x - drag.x), nz = nx === drag.x ? drag.z + Math.sign(z - drag.z) : drag.z;
    if (!inside(nx, nz)) break;
    connect(drag.x, drag.z, nx, nz);
    drag.x = nx; drag.z = nz;
  }
  draw();
});
window.addEventListener('mouseup', () => { drag = null; });

function flash(msg) { const st = document.getElementById('status'); st.innerHTML = '<span class="bad">' + msg + '</span>'; setTimeout(draw, 1800); }

document.querySelectorAll('[data-tool]').forEach(b => b.onclick = () => {
  tool = b.dataset.tool;
  document.querySelectorAll('[data-tool]').forEach(o => o.classList.toggle('on', o === b));
});
document.getElementById('undo').onclick = () => { if (history.length) { cells = JSON.parse(history.pop()); draw(); } };
document.getElementById('clear').onclick = () => {
  if (!confirm('Clear the whole layout?')) return;
  snapshot();
  for (let z = 0; z < N; z++) for (let x = 0; x < N; x++) cells[z][x] = empty();
  draw();
};

function encode(c) {
  if (c.t === '.') return '.';
  const doors = ['n', 'e', 's', 'w'].filter(d => c[d]).join('').toUpperCase();
  return (c.t === 'B' ? 'B' + c.q + '#' + c.id : c.t) + ':' + doors;
}
function decode(s) {
  const c = empty();
  if (s === '.') return c;
  const [head, doors] = s.split(':');
  c.t = head[0];
  if (c.t === 'B') { c.q = parseInt(head[1], 10); c.id = head.split('#')[1]; }
  for (const d of (doors || '').toLowerCase()) c[d] = 1;
  return c;
}
document.getElementById('save').onclick = () => {
  const out = { format: 'single_tunnel_v1', size: N, cells: cells.map(r => r.map(encode)) };
  const blob = new Blob([JSON.stringify(out, null, 1) + '\n'], { type: 'application/json' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'underground_layout.json'; a.click();
  URL.revokeObjectURL(a.href);
};
document.getElementById('open').onchange = ev => {
  const f = ev.target.files[0]; if (!f) return;
  f.text().then(t => {
    try {
      const d = JSON.parse(t);
      if (d.format !== 'single_tunnel_v1' || d.cells.length !== N) throw new Error('not a single-tunnel layout file');
      snapshot(); cells = d.cells.map(r => r.map(decode)); draw();
    } catch (e) { flash('Could not open that file: ' + e.message); }
  });
  ev.target.value = '';
};

draw();
</script>
</body>
</html>
'''

html = html.replace('__BASE__', base_bits).replace('__IMAGES__', json.dumps(images))
open(R + 'sourplatinum/tools/underground_layout_editor_single_tunnel.html', 'w', encoding='utf-8').write(html)
print('ok', len(html))
