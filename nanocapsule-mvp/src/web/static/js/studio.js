// ───────────────────────── Estado ─────────────────────────
let stage, capsidComp = null, enzymeReps = [], spinning = false;
const $ = id => document.getElementById(id);

function setStatus(msg, kind='') {
  const el = $('status'); el.className = 'status ' + kind;
  el.innerHTML = (kind === 'load' ? '<span class="spinner"></span>' : '') + msg;
}

// ───────────────────────── NGL ─────────────────────────
function initNGL() {
  stage = new NGL.Stage('viewport', { backgroundColor: '#ffffff' });
  // Fondo blanco + iluminación suave.
  stage.setParameters({ lightIntensity: 0.9, ambientIntensity: 0.45, ambientColor: 0xffffff });
  window.addEventListener('resize', () => stage.handleResize());
}

async function renderPDB(source, isUrl) {
  clearSphere();
  clearBox();
  stage.removeAllComponents();
  capsidComp = null; enzymeReps = [];
  const comp = await stage.loadFile(source, { ext: 'pdb' });
  capsidComp = comp;
  // Cápside = modelo 0: superficie translúcida coloreada POR CADENA + cartoon tenue.
  comp.addRepresentation('surface', { sele:'/0', colorScheme:'chainid', opacity:0.28, side:'front' });
  comp.addRepresentation('cartoon', { sele:'/0', colorScheme:'chainid', opacity:0.12 });
  // Enzimas = modelos 1..N: cada una con un color propio (modelindex).
  enzymeReps.push(comp.addRepresentation('cartoon', { sele:'not /0', colorScheme:'modelindex', colorScale:'rainbow', opacity:1.0 }));
  enzymeReps.push(comp.addRepresentation('ball+stick', { sele:'(not /0) and hetero and not water', colorScheme:'modelindex', colorScale:'rainbow' }));
  comp.autoView();
  applyOpacity();
  if ($('showSphere').checked) drawSphere(+$('radius').value);
  if ($('showBox').checked && mdBoxData) drawBox(mdBoxData);
}

function applyOpacity() {
  if (!capsidComp) return;
  const op = +$('opacity').value / 100;
  capsidComp.eachRepresentation(r => {
    if (r.name === 'surface') r.setParameters({ opacity: op });
  });
}

// ── Esfera de radio interno (imita el pseudoátomo que PyMOL expande) ──
let radiusComp = null, radiusAnim = null;

function clearSphere() {
  if (radiusAnim) { cancelAnimationFrame(radiusAnim); radiusAnim = null; }
  if (radiusComp) { try { stage.removeComponent(radiusComp); } catch (e) {} radiusComp = null; }
}

function buildSphere(radius) {
  if (!capsidComp) return null;
  const c = capsidComp.structure.getView(new NGL.Selection('/0')).center; // centroide real de la cápside
  const shape = new NGL.Shape('radiusSphere');
  const col = [1.0, 0.22, 0.05];                    // rojo-naranja
  const tube = Math.max(radius * 0.008, 0.4);       // grosor del alambre
  const RINGS = 7, SEG = 44, MER = 12, MSEG = 26;
  const P = (theta, phi) => [                        // punto en la esfera (origen local)
    radius * Math.sin(theta) * Math.cos(phi),
    radius * Math.cos(theta),
    radius * Math.sin(theta) * Math.sin(phi)
  ];
  for (let i = 1; i <= RINGS; i++) {                 // paralelos
    const th = Math.PI * i / (RINGS + 1);
    for (let k = 0; k < SEG; k++) {
      shape.addCylinder(P(th, 2*Math.PI*k/SEG), P(th, 2*Math.PI*(k+1)/SEG), col, tube);
    }
  }
  for (let m = 0; m < MER; m++) {                    // meridianos
    const phi = 2*Math.PI*m/MER;
    for (let k = 0; k < MSEG; k++) {
      shape.addCylinder(P(Math.PI*k/MSEG, phi), P(Math.PI*(k+1)/MSEG, phi), col, tube);
    }
  }
  const comp = stage.addComponentFromObject(shape);
  comp.addRepresentation('buffer', { opacity: 0.6, side: 'double', disablePicking: true });
  comp.setPosition([c.x, c.y, c.z]);                 // centrada en la cápside
  return comp;
}

function drawSphere(radius) {          // estática, al radio actual
  clearSphere();
  if (!$('showSphere').checked || !capsidComp) return;
  radiusComp = buildSphere(radius);
  if (radiusComp) radiusComp.setScale(1);
  stage.viewer.requestRender();
}

function growSphere(radius) {          // animada: 0 → radio (como PyMOL)
  clearSphere();
  if (!capsidComp) return;
  $('showSphere').checked = true;
  radiusComp = buildSphere(radius);
  if (!radiusComp) return;
  let t0 = null; const dur = 1400;
  function frame(now) {
    if (t0 === null) t0 = now;
    const p = Math.min((now - t0) / dur, 1);
    const e = 1 - Math.pow(1 - p, 3);               // easeOut
    radiusComp.setScale(Math.max(e, 0.001));
    setStatus('Expandiendo esfera… ' + (radius * e).toFixed(1) + ' Å', 'load');
    stage.viewer.requestRender();
    if (p < 1) { radiusAnim = requestAnimationFrame(frame); }
    else { radiusAnim = null; setStatus('Radio interno: ' + radius.toFixed(1) + ' Å', 'ok'); }
  }
  radiusAnim = requestAnimationFrame(frame);
}

// ── Box de simulación (Preparador DM) ──
let boxComp = null, mdBoxData = null, mdBoxCapsid = null;

function clearBox() {
  if (boxComp) { try { stage.removeComponent(boxComp); } catch (e) {} boxComp = null; }
}

async function fetchBox() {
  const capsid = $('capsid').value;
  if (mdBoxData && mdBoxCapsid === capsid) return mdBoxData;
  const d = await (await fetch('/api/md/box?capsid=' + encodeURIComponent(capsid))).json();
  if (d.error) throw new Error(d.error);
  mdBoxData = d; mdBoxCapsid = capsid; return d;
}

function drawBox(d) {
  clearBox();
  if (!$('showBox').checked || !d) return;
  const h = d.box_half, c = d.center;
  const shape = new NGL.Shape('mdbox');
  const col = [0.15, 0.55, 0.95], tube = Math.max(h * 0.006, 0.6);
  const v = [[-h,-h,-h],[h,-h,-h],[h,h,-h],[-h,h,-h],[-h,-h,h],[h,-h,h],[h,h,h],[-h,h,h]];
  [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]
    .forEach(([a, b]) => shape.addCylinder(v[a], v[b], col, tube));
  boxComp = stage.addComponentFromObject(shape);
  boxComp.addRepresentation('buffer', { opacity: 0.6, disablePicking: true });
  boxComp.setPosition(c);
  stage.viewer.requestRender();
}

async function toggleBox() {
  if (!$('showBox').checked) { clearBox(); return; }
  try { drawBox(await fetchBox()); }
  catch (e) { setStatus('Error box: ' + e, 'err'); $('showBox').checked = false; }
}

async function prepareDM() {
  const capsid = $('capsid').value;
  const n = +$('nSub').value, smiles = $('smiles').value.trim();
  setStatus('Preparando archivos DM…', 'load');
  try {
    const d = await (await fetch('/api/md/prepare', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capsid, n_substrate: n, smiles })
    })).json();
    if (d.error) throw new Error(d.error);
    mdBoxData = { center: d.center, box_half: d.box_half }; mdBoxCapsid = capsid;
    $('showBox').checked = true; drawBox(mdBoxData);
    $('dm-out').style.display = 'block';
    $('dm-out').textContent =
      `# BOX  ${d.box_size} × ${d.box_size} × ${d.box_size} Å   (half ${d.box_half})\n` +
      `# centro  ${d.center.join(', ')}\n# sustratos  ${d.n_substrate}` +
      (d.smiles ? `\n# SMILES  ${d.smiles}` : '') +
      `\n\n===== packmol_input.inp =====\n${d.packmol_input}\n` +
      `\n===== gensystem.leap =====\n${d.leap_input}`;
    setStatus('Archivos DM preparados · box ' + d.box_size + ' Å.', 'ok');
  } catch (e) { setStatus('Error DM: ' + e, 'err'); }
}

// ───────────────────────── API ─────────────────────────
async function loadLibrary() {
  try {
    const r = await fetch('/api/library/combinations');
    const data = await r.json();
    fillSelect('capsid', data.capsides);
    fillSelect('enzyme', data.enzymes);
    fillSelect('poreCapsid', data.capsides);
    $('engine-badge').textContent = 'PACKMOL LISTO';
    $('engine-badge').style.background = 'var(--green)';
    $('hdr-sub').textContent = `${data.capsides.length} cápsides · ${data.enzymes.length} enzimas · ${data.total_combinations} combinaciones`;
  } catch (e) {
    $('engine-badge').textContent = 'SIN BACKEND';
    setStatus('No se pudo contactar el backend: ' + e, 'err');
  }
}
function fillSelect(id, items) {
  const s = $(id); s.innerHTML = '';
  items.forEach(it => { const o = document.createElement('option'); o.value = it; o.textContent = it; s.appendChild(o); });
}

// ───────────────────────── Biblioteca ─────────────────────────
const fmt = n => (n == null ? '—' : Number(n).toLocaleString('es'));
const fmt1 = n => (n == null ? '—' : Number(n).toFixed(1));

async function loadLibraryDetail() {
  try {
    const d = await (await fetch('/api/library/detail')).json();
    if (d.error) throw new Error(d.error);
    renderCaps(d.capsides);
    renderEnz(d.enzymes);
  } catch (e) {
    $('tb-caps').innerHTML = `<tr><td colspan="7">Error: ${e}</td></tr>`;
  }
}

function renderCaps(caps) {
  $('tb-caps').innerHTML = caps.map(c => `
    <tr data-capsid="${c.name}">
      <td class="name">${c.name}</td>
      <td><span class="pill">${c.t_number}</span></td>
      <td class="pdb">${c.pdb}</td>
      <td class="num">${fmt(c.atoms)}</td>
      <td class="num">${fmt(c.chains)}</td>
      <td class="num">${c.radius == null ? '—' : fmt1(c.radius)}</td>
      <td class="num"><button class="selbtn">Usar →</button></td>
    </tr>`).join('');
  $('tb-caps').querySelectorAll('tr').forEach(tr =>
    tr.addEventListener('click', () => useStructure('capsid', tr.dataset.capsid)));
}

function renderEnz(enz) {
  $('tb-enz').innerHTML = enz.map(e => `
    <tr data-enzyme="${e.name}">
      <td class="name">${e.name}</td>
      <td class="pdb">${e.pdb}</td>
      <td>${e.rol === 'terapéutica' ? '<span class="pill tx">terapéutica</span>' : e.rol}</td>
      <td>${e.enfermedad}</td>
      <td class="num">${fmt(e.atoms)}</td>
      <td class="num">${fmt(e.chains)}</td>
      <td class="num">${fmt1(e.rg)}</td>
      <td class="num">${fmt(e.volume)}</td>
      <td class="num"><button class="selbtn">Usar →</button></td>
    </tr>`).join('');
  $('tb-enz').querySelectorAll('tr').forEach(tr =>
    tr.addEventListener('click', () => useStructure('enzyme', tr.dataset.enzyme)));
}

function useStructure(kind, name) {
  $(kind).value = name;           // fija cápside o enzima en los selectores del Studio
  showView('studio');
  doPreview();                    // vista 3D inmediata
}

function showView(v) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === v));
  $('view-biblioteca').style.display = (v === 'biblioteca') ? '' : 'none';
  $('view-studio').style.display     = (v === 'studio') ? 'grid' : 'none';
  $('view-pore').style.display       = (v === 'pore') ? '' : 'none';
  $('view-deimmuno').style.display   = (v === 'deimmuno') ? '' : 'none';
  if (v === 'studio' && stage) stage.handleResize();   // el visor se creó oculto
  if (v === 'pore') { doPore(); loadChannels(); loadHoleStructures(); }
  if (v === 'deimmuno') loadDeimmuno();
  $('view-md').style.display = (v === 'md') ? '' : 'none';
  if (v === 'md') initMD();
}

// ───────────────────────── Análisis MD ─────────────────────────
let chMD, mdExamples = [], mdData = [], mdIdx = 0, mdTimer = null, mdMeta = {}, mdStep = 1;

async function initMD() {
  if (!chMD) await loadMDExamples();
  else chMD.resize();
}

async function loadMDExamples() {
  try {
    const d = await (await fetch('/api/md/examples')).json();
    if (d.error) throw new Error(d.error);
    mdExamples = d.examples;
    $('md-examples').innerHTML = mdExamples.map((e, i) =>
      `<button class="mdex" data-i="${i}">${e.name}<div class="mdex-d" style="font-size:9px;color:var(--text3);font-family:var(--mono)">${e.desc}</div></button>`).join('');
    $('md-examples').querySelectorAll('.mdex').forEach(b =>
      b.addEventListener('click', () => loadExample(+b.dataset.i)));
    createMDChart();
    loadExample(0);
  } catch (e) { $('md-note').textContent = 'Error: ' + e; }
}

function createMDChart() {
  chMD = new Chart($('chMD'), {
    type: 'line',
    data: { datasets: [{ data: [], borderColor: '#2e8b57', borderWidth: 2, pointRadius: 0, tension: .2, fill: false }] },
    options: {
      animation: false, parsing: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { type: 'linear', title: { display: true, text: 'Frame', font: { family: 'Courier New', size: 10 } }, ticks: { font: { family: 'Courier New', size: 9 } } },
        y: { title: { display: true, text: 'RMSD (Å)', font: { family: 'Courier New', size: 10 } }, ticks: { font: { family: 'Courier New', size: 9 } } }
      }
    }
  });
}

function loadExample(i) {
  const ex = (typeof i === 'number') ? mdExamples[i] : i;   // índice o objeto (archivo subido)
  stopMD();
  mdMeta = ex; mdData = ex.points; mdIdx = 0;
  mdStep = Math.max(1, Math.ceil(mdData.length / 150));
  document.querySelectorAll('.mdex').forEach((b, k) => b.classList.toggle('active', k === i));
  $('md-title').innerHTML = `${ex.name.toUpperCase()} · ${ex.ylabel} <span style="font-family:var(--mono);font-size:9px;color:var(--text3);text-transform:none;letter-spacing:0">(ilustrativo)</span>`;
  $('md-caption').textContent = `${ex.desc} · ${ex.anchor}`;
  chMD.data.datasets[0].borderColor = ex.color || '#000';
  chMD.options.scales.x.title.text = ex.xlabel || 'Frame';
  chMD.options.scales.y.title.text = ex.ylabel || 'Valor';
  chMD.data.datasets[0].data = [];
  chMD.update('none');
  setMDStats(0);
  playMD();
}

function setMDStats(i) {
  const p = mdData[Math.max(0, i - 1)] || { y: 0 };
  $('md-frame').textContent = i;
  $('md-time').textContent = (i * 0.001).toFixed(3) + ' ns';
  $('md-val').textContent = (p.y == null ? '—' : Number(p.y).toLocaleString('es'));
}

function playMD() {
  if (mdTimer || !mdData.length) return;
  $('md-state').textContent = 'REPRODUCIENDO';
  mdTimer = setInterval(() => {
    if (mdIdx >= mdData.length) { stopMD(); $('md-state').textContent = 'LISTO'; return; }
    mdIdx = Math.min(mdData.length, mdIdx + mdStep);
    chMD.data.datasets[0].data = mdData.slice(0, mdIdx);
    chMD.update('none');
    setMDStats(mdIdx);
  }, 30);
}
function stopMD() { if (mdTimer) { clearInterval(mdTimer); mdTimer = null; } }
function pauseMD() { stopMD(); $('md-state').textContent = 'PAUSA'; }
function resetMD() { stopMD(); mdIdx = 0; chMD.data.datasets[0].data = []; chMD.update('none'); setMDStats(0); $('md-state').textContent = 'LISTO'; }

function parseMDFile(text, name) {
  const pts = [];
  text.split(/\r?\n/).forEach(line => {
    line = line.trim();
    if (!line || line.startsWith('#') || line.startsWith('@')) return;
    const parts = line.split(/\s+/);
    const x = parseFloat(parts[0]), y = parseFloat(parts[1]);
    if (!isNaN(x) && !isNaN(y)) pts.push({ x, y });
  });
  if (!pts.length) { $('md-state').textContent = 'ARCHIVO VACÍO'; return; }
  loadExample({ name, desc: 'archivo subido', xlabel: 'Frame', ylabel: 'Valor', anchor: pts.length + ' puntos', color: '#000', points: pts });
}

// ───────────────────────── De-inmunización ─────────────────────────
let chDeimmuno;
const CAT_COL = { pasa: '#2e8b57', no_silencia: '#BA7517', rompe: '#FF2600', wt: '#666' };
const CAT_LBL = { pasa: 'pasa ambos', no_silencia: 'no silencia', rompe: 'rompe la cápside', wt: 'WT' };

async function loadDeimmuno() {
  try {
    const d = await (await fetch('/api/deimmuno/data')).json();
    if (d.error) throw new Error(d.error);
    $('tb-anclas').innerHTML = d.anclas.map(a =>
      `<tr><td class="name">${a.puerta}</td><td>${a.herramienta}</td><td class="pdb">${a.ancla}</td></tr>`).join('');
    $('d-anchor').textContent = `${d.anchor.name} · ${d.anchor.source}`;
    renderDeimmuno(d);
  } catch (e) { $('deimmuno-status').textContent = 'Error: ' + e; }
}

function renderDeimmuno(d) {
  const cats = ['pasa', 'no_silencia', 'rompe', 'wt'];
  const datasets = cats.map(c => ({
    label: CAT_LBL[c],
    data: d.mutants.filter(m => m.cat === c).map(m => ({ x: m.dmhc, y: m.ddg, name: m.name })),
    backgroundColor: CAT_COL[c],
    borderColor: c === 'wt' ? '#000' : 'transparent', borderWidth: 1,
    pointRadius: c === 'wt' ? 8 : 6, pointHoverRadius: 9,
    pointStyle: c === 'wt' ? 'rectRot' : 'circle',
  }));

  // Plugin: sombrea la DIANA (x<0, y<0) y etiqueta R312Q y WT.
  const dianaPlugin = {
    id: 'diana',
    beforeDatasetsDraw(chart) {
      const { ctx, scales } = chart;
      const x0 = scales.x.getPixelForValue(0), y0 = scales.y.getPixelForValue(0);
      ctx.save();
      ctx.fillStyle = 'rgba(46,139,87,0.10)';
      ctx.fillRect(scales.x.left, y0, x0 - scales.x.left, scales.y.bottom - y0);
      ctx.strokeStyle = 'rgba(46,139,87,0.5)'; ctx.setLineDash([5, 4]); ctx.lineWidth = 1;
      ctx.strokeRect(scales.x.left, y0, x0 - scales.x.left, scales.y.bottom - y0);
      ctx.fillStyle = 'rgba(46,139,87,0.85)'; ctx.font = 'bold 11px "Courier New"'; ctx.setLineDash([]);
      ctx.fillText('DIANA', scales.x.left + 10, y0 + 18);
      ctx.restore();
    },
    afterDatasetsDraw(chart) {
      const { ctx, scales } = chart;
      ctx.save(); ctx.font = 'bold 10px "Courier New"'; ctx.fillStyle = '#000';
      d.mutants.filter(m => m.name === 'R312Q' || m.name === 'WT').forEach(m => {
        ctx.fillText(m.name, scales.x.getPixelForValue(m.dmhc) + 9, scales.y.getPixelForValue(m.ddg) + 3);
      });
      ctx.restore();
    }
  };

  chDeimmuno && chDeimmuno.destroy();
  chDeimmuno = new Chart($('chDeimmuno'), {
    type: 'scatter',
    data: { datasets },
    options: {
      plugins: {
        legend: { labels: { font: { family: 'Courier New', size: 10 }, usePointStyle: true } },
        tooltip: { callbacks: { label: c => `${c.raw.name} (ΔMHC ${c.raw.x}, ΔΔG ${c.raw.y})` } }
      },
      scales: {
        x: { title: { display: true, text: '← silencia · ΔMHC · más visible →', font: { family: 'Courier New', size: 10 } },
             grid: { color: cx => cx.tick.value === 0 ? '#000' : 'rgba(0,0,0,0.08)' }, ticks: { font: { family: 'Courier New', size: 9 } } },
        y: { title: { display: true, text: '← estabiliza · ΔΔG · rompe →', font: { family: 'Courier New', size: 10 } },
             grid: { color: cx => cx.tick.value === 0 ? '#000' : 'rgba(0,0,0,0.08)' }, ticks: { font: { family: 'Courier New', size: 9 } } }
      }
    },
    plugins: [dianaPlugin]
  });
}

// ───────────────────────── Pac-Pore ─────────────────────────
let chPore, poreSubstrates = [], poreStage = null;

async function loadChannels() {
  try {
    const d = await (await fetch('/api/pore/channels')).json();
    const s = $('poreChannel'); s.innerHTML = '';
    if (!d.channels || !d.channels.length) {
      s.innerHTML = '<option value="">(sin canales HOLE calculados)</option>';
      return;
    }
    d.channels.forEach(c => { const o = document.createElement('option'); o.value = c.id; o.textContent = c.id; s.appendChild(o); });
  } catch (e) { $('channel-caption').textContent = 'Error: ' + e; }
}

async function showChannel() {
  const id = $('poreChannel').value;
  if (!id) { $('channel-caption').textContent = 'No hay canales HOLE calculados aún (se generan con "Correr HOLE").'; return; }
  if (!poreStage) {
    poreStage = new NGL.Stage('poreViewport', { backgroundColor: '#ffffff' });
    poreStage.setParameters({ lightIntensity: 1.0, ambientIntensity: 0.5 });
    window.addEventListener('resize', () => poreStage.handleResize());
  }
  $('channel-caption').textContent = 'Cargando canal ' + id + '…';
  poreStage.removeAllComponents();
  const comp = await poreStage.loadFile('/api/pore/channel?id=' + encodeURIComponent(id), { ext: 'pdb' });
  comp.addRepresentation('spacefill', { radiusType: 'bfactor', colorScheme: 'bfactor', colorScale: 'RdYlBu' });
  comp.autoView();
  poreStage.handleResize();
  $('channel-caption').textContent = 'Canal ' + id + ' · esferas HOLE por radio (azul ancho → rojo constricción).';
}

async function loadPoreConfig() {
  try {
    const d = await (await fetch('/api/pore/config')).json();
    fillSelect('poreAxis', d.axes);
    poreSubstrates = d.substrates;
    const s = $('poreSub'); s.innerHTML = '';
    d.substrates.forEach(su => {
      const o = document.createElement('option');
      o.value = su.name; o.textContent = `${su.name} · ${su.disease} (${su.radius} Å)`;
      s.appendChild(o);
    });
    if ($('view-pore').style.display !== 'none') doPore();
  } catch (e) { $('pore-status').textContent = 'Error cargando config: ' + e; }
}

async function resolveSubstrate() {
  const smiles = $('poreSmiles').value.trim();
  if (smiles) {
    const s = await (await fetch('/api/pore/section', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ smiles })
    })).json();
    if (s.error) throw new Error(s.error);
    return { name: 'SMILES', radius: s.radius };
  }
  return poreSubstrates.find(x => x.name === $('poreSub').value) || { radius: 0 };
}

async function doPore() {
  const capsid = $('poreCapsid').value, axis = $('poreAxis').value;
  if (!capsid || !poreSubstrates.length) return;
  try {
    const sub = await resolveSubstrate();
    const d = await (await fetch('/api/pore/profile', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capsid, axis })
    })).json();
    if (d.error) throw new Error(d.error);
    $('pore-badge').textContent = '(ilustrativo)';
    renderPore(d, sub);
    $('pore-status').className = 'status';
    $('pore-status').textContent = (sub.name === 'SMILES')
      ? 'Sustrato SMILES · sección real ' + sub.radius + ' Å · perfil ilustrativo (usa "Correr HOLE" para el real).'
      : 'Perfil ilustrativo — usa "Correr HOLE" para datos reales.';
  } catch (e) { $('pore-status').textContent = 'Error: ' + e; }
}

async function runScreen() {
  const st = $('holeStructure').value;
  if (!st) return;
  $('btnCribar').disabled = true;
  $('pore-status').className = 'status load';
  $('pore-status').innerHTML = '<span class="spinner"></span>Cribando mutantes (PyMOL + HOLE)… ~10 s';
  try {
    const sub = await resolveSubstrate();
    const d = await (await fetch('/api/pore/screen', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ structure: st, substrate_radius: sub.radius })
    })).json();
    if (d.error) throw new Error(d.error);
    $('tb-cribado').innerHTML = d.mutants.map(m =>
      `<tr data-ch="${m.channel_id}">
        <td class="name">${m.name}</td><td>${m.mutations}</td>
        <td class="num">${m.pore_min.toFixed(2)} Å</td>
        <td class="num">${m.delta >= 0 ? '+' : ''}${m.delta.toFixed(2)}</td>
        <td>${m.passes ? '<span class="pill tx">PASA</span>' : 'ocluido'}</td>
      </tr>`).join('');
    $('tb-cribado').querySelectorAll('tr').forEach(tr => tr.addEventListener('click', async () => {
      await loadChannels(); $('poreChannel').value = tr.dataset.ch; showChannel();
    }));
    $('cribado-out').style.display = 'block';
    const best = d.mutants[0];
    $('pore-status').className = 'status ok';
    $('pore-status').textContent =
      `Cribado: WT ${d.wt_min} Å → mejor ${best.name} ${best.pore_min} Å (Δ${best.delta >= 0 ? '+' : ''}${best.delta}). ` +
      `Residuos del poro: ${d.pore_residues.map(r => r.pos + r.resn[0]).join(', ')}.`;
  } catch (e) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'Error cribado: ' + e; }
  finally { $('btnCribar').disabled = false; }
}

function appendCribadoRow(m, wtMin, subRadius) {
  const delta = (m.delta != null) ? (m.delta >= 0 ? '+' : '') + m.delta.toFixed(2) : '—';
  const passes = (subRadius != null) && m.pore_min >= subRadius;
  const tr = document.createElement('tr');
  tr.dataset.ch = m.channel_id;
  tr.innerHTML = `<td class="name">${m.name}</td><td>${m.mutations}</td>
    <td class="num">${m.pore_min.toFixed(2)} Å</td><td class="num">${delta}</td>
    <td>${passes ? '<span class="pill tx">PASA</span>' : 'ocluido'}</td>`;
  tr.addEventListener('click', async () => { await loadChannels(); $('poreChannel').value = tr.dataset.ch; showChannel(); });
  $('tb-cribado').prepend(tr);
  $('cribado-out').style.display = 'block';
}

async function runManualMutant() {
  const st = $('holeStructure').value, raw = $('manualMut').value.trim();
  if (!st || !raw) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'Escribe las mutaciones, ej: 84:TRP, 145:ASP'; return; }
  const mutations = {};
  raw.split(',').forEach(p => { const [pos, aa] = p.split(':').map(s => s.trim()); if (pos && aa) mutations[pos] = aa.toUpperCase(); });
  $('btnManualMut').disabled = true;
  $('pore-status').className = 'status load';
  $('pore-status').innerHTML = '<span class="spinner"></span>Generando y evaluando mutante manual (PyMOL + HOLE)…';
  try {
    const m = await (await fetch('/api/pore/mutant', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ structure: st, mutations })
    })).json();
    if (m.error) throw new Error(m.error);
    const sub = await resolveSubstrate();
    appendCribadoRow(m, null, sub.radius);
    await loadChannels(); $('poreChannel').value = m.channel_id; showChannel();
    $('pore-status').className = 'status ok';
    $('pore-status').textContent = `Mutante manual ${m.mutations}: radio mín ${m.pore_min} Å` +
      (m.delta != null ? ` (Δ${m.delta >= 0 ? '+' : ''}${m.delta} vs WT)` : '') +
      (m.pore_min >= sub.radius ? ' → PASA' : ' → ocluido') + '.';
  } catch (e) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'Error mutante: ' + e; }
  finally { $('btnManualMut').disabled = false; }
}

let chDock;
async function runDock() {
  const st = $('holeStructure').value, smiles = $('poreSmiles').value.trim();
  if (!st) return;
  if (!smiles) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'El docking necesita un SMILES de sustrato.'; return; }
  $('btnDock').disabled = true;
  $('pore-status').className = 'status load';
  $('pore-status').innerHTML = '<span class="spinner"></span>Docking (obabel + vina) en WT y mutantes… ~30 s';
  try {
    const d = await (await fetch('/api/pore/dock', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ structure: st, smiles })
    })).json();
    if (d.error) throw new Error(d.error);
    renderDock(d);
    $('pore-status').className = 'status ok';
    $('pore-status').textContent = `Docking: correlación radio–afinidad r=${d.correlation}. ` +
      (d.correlation > 0.3 ? 'Abrir el poro debilita la unión.' : d.correlation < -0.3 ? 'Abrir el poro refuerza la unión.' : 'Sin correlación clara.');
  } catch (e) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'Error docking: ' + e; }
  finally { $('btnDock').disabled = false; }
}

function renderDock(d) {
  $('dock-out').style.display = 'block';
  const pts = d.points.map(p => ({ x: p.pore_min, y: p.affinity, name: p.name }));
  const colors = d.points.map(p => p.name === 'WT' ? '#378ADD' : '#FF2600');
  const labelPlugin = {
    id: 'ptlabels',
    afterDatasetsDraw(chart) {
      const { ctx, scales } = chart;
      ctx.save(); ctx.font = 'bold 9px "Courier New"'; ctx.fillStyle = '#000';
      pts.forEach(p => ctx.fillText(p.name, scales.x.getPixelForValue(p.x) + 8, scales.y.getPixelForValue(p.y) + 3));
      ctx.restore();
    }
  };
  chDock && chDock.destroy();
  chDock = new Chart($('chDock'), {
    type: 'scatter',
    data: { datasets: [{ data: pts, backgroundColor: colors, pointRadius: 7, pointHoverRadius: 9 }] },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: c => `${c.raw.name}: poro ${c.raw.x} Å · ${c.raw.y} kcal/mol` } }
      },
      scales: {
        x: { title: { display: true, text: 'radio mín del poro (Å)', font: { family: 'Courier New', size: 10 } }, ticks: { font: { family: 'Courier New', size: 9 } } },
        y: { title: { display: true, text: 'afinidad de unión (kcal/mol)', font: { family: 'Courier New', size: 10 } }, ticks: { font: { family: 'Courier New', size: 9 } } }
      }
    },
    plugins: [labelPlugin]
  });
  $('dock-caption').textContent = `Sustrato: sección ${d.section} Å · Pearson r=${d.correlation} · ${d.points.length} puntos (azul=WT, rojo=mutantes).`;
}

async function loadHoleStructures() {
  try {
    const d = await (await fetch('/api/pore/structures')).json();
    const s = $('holeStructure'); s.innerHTML = '';
    (d.structures || []).forEach(x => { const o = document.createElement('option'); o.value = x.key; o.textContent = x.key; s.appendChild(o); });
  } catch (e) {}
}

async function runHole() {
  const st = $('holeStructure').value;
  if (!st) return;
  $('btnRunHole').disabled = true;
  $('pore-status').className = 'status load';
  $('pore-status').innerHTML = '<span class="spinner"></span>Corriendo HOLE sobre ' + st + '… (~20 s)';
  try {
    const d = await (await fetch('/api/pore/run_hole', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ structure: st })
    })).json();
    if (d.error) throw new Error(d.error);
    const sub = await resolveSubstrate();
    $('pore-badge').textContent = '(HOLE real · ' + st + ')';
    renderPore(d, sub);
    $('pore-status').className = 'status ok';
    $('pore-status').textContent = 'HOLE real · ' + st + ' · radio mín ' + d.pore_min + ' Å.';
    await loadChannels();
    $('poreChannel').value = d.channel_id;
    showChannel();
  } catch (e) { $('pore-status').className = 'status err'; $('pore-status').textContent = 'Error HOLE: ' + e; }
  finally { $('btnRunHole').disabled = false; }
}

function renderPore(d, sub) {
  const pass = d.pore_min >= sub.radius;
  const subLabel = sub.name === 'SMILES' ? 'SMILES (sección real)' : $('poreSub').value;
  $('p-min').textContent   = d.pore_min.toFixed(1) + ' Å';
  $('p-sub').textContent   = sub.radius.toFixed(1) + ' Å';
  $('p-state').textContent = pass ? 'PASA' : 'OCLUIDO';
  $('p-state').className    = 'v ' + (pass ? '' : 'accent');
  $('pore-caption').textContent =
    `Poro nativo mín ${d.pore_min} Å · ${subLabel} ${sub.radius} Å · ${pass ? 'PASA' : 'NO PASA'}`;

  const thr = d.positions.map(() => sub.radius);
  const dot = d.positions.map((x, i) => i === d.min_index ? d.radius[i] : null);
  chPore && chPore.destroy();
  chPore = new Chart($('chPore'), {
    type: 'line',
    data: { labels: d.positions, datasets: [
      { label: 'Radio del poro', data: d.radius, borderColor: '#000', borderWidth: 2, tension: .35, pointRadius: 0, fill: false },
      { label: 'Radio del sustrato', data: thr, borderColor: '#FF2600', borderDash: [6, 4], borderWidth: 1.5, pointRadius: 0, fill: false },
      { label: 'Constricción', data: dot, borderColor: 'transparent', backgroundColor: '#FF2600',
        pointRadius: d.positions.map((x, i) => i === d.min_index ? 6 : 0) }
    ]},
    options: {
      plugins: { legend: { labels: { font: { family: 'Courier New', size: 10 } } } },
      scales: {
        x: { title: { display: true, text: 'posición a lo largo del eje', font: { family: 'Courier New', size: 9 } }, ticks: { display: false } },
        y: { title: { display: true, text: 'radio (Å)', font: { family: 'Courier New', size: 9 } }, beginAtZero: true, suggestedMax: 6, ticks: { font: { family: 'Courier New', size: 9 } } }
      }
    }
  });
}

async function doPreview() {
  const capsid = $('capsid').value, enzyme = $('enzyme').value;
  if (!capsid || !enzyme) return;
  setStatus('Generando preview de ' + $('nEnz').value + ' enzimas…', 'load');
  try {
    const r = await fetch('/api/preview/enzymes', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ capsid, enzyme, n_enzymes:+$('nEnz').value, radius:+$('radius').value, save_file:false })
    });
    if (!r.ok) throw new Error((await r.json()).error || r.status);
    const text = await r.text();
    await renderPDB(new Blob([text], { type:'text/plain' }), false);
    setStatus('Preview cargado: ' + $('nEnz').value + ' enzimas (colocación aleatoria).', 'ok');
  } catch (e) { setStatus('Error en preview: ' + e, 'err'); }
}

async function doSubstrate() {
  const capsid = $('capsid').value;
  if (!capsid) return;
  const n = +$('nSub').value;
  const smiles = $('smiles').value.trim();
  setStatus((smiles ? 'Generando sustrato del SMILES y colocándolo…' : 'Colocando sustrato alrededor de ' + capsid + '…'), 'load');
  try {
    const r = await fetch('/api/preview/substrate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capsid, n, smiles })
    });
    if (!r.ok) throw new Error((await r.json()).error || r.status);
    const text = await r.text();
    const actual = (text.match(/^MODEL/gm) || []).length;
    await renderPDB(new Blob([text], { type: 'text/plain' }), false);
    setStatus('Sustrato colocado alrededor de la cápside (' + actual + '/' + n + ' copias' + (smiles ? ', desde SMILES' : '') + ').', 'ok');
  } catch (e) { setStatus('Error sustrato: ' + e, 'err'); }
}

async function doRadius() {
  const capsid = $('capsid').value;
  setStatus('Calculando radio interno con PyMOL…', 'load');
  try {
    const r = await fetch('/api/capsid/radius', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ capsid })
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || r.status);
    $('radius').value = Math.round(d.internal_radius);
    growSphere(d.internal_radius);
  } catch (e) { setStatus('Error radio: ' + e, 'err'); }
}

async function doRun() {
  const capsid = $('capsid').value, enzyme = $('enzyme').value;
  const t0 = performance.now();
  setStatus('Ejecutando Packmol (' + $('nRep').value + ' réplicas). Esto tarda…', 'load');
  $('btnRun').disabled = true;
  try {
    const r = await fetch('/api/experiment/run', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ capsid, enzyme, n_replicas:+$('nRep').value, run_packing:true })
    });
    const d = await r.json();
    if (!r.ok || d.status === 'error') throw new Error(d.error || 'fallo');
    updateStats(d);
    const secs = ((performance.now() - t0) / 1000).toFixed(0);
    if (d.best_file) {
      setStatus(`Packing real OK: ${d.best_result} enzimas en ${secs}s. Cargando 3D…`, 'ok');
      await renderPDB('/api/result/pdb?path=' + encodeURIComponent(d.best_file), true);
    }
    setStatus(`Packing real OK: ${d.best_result} enzimas · ${d.n_replicas_success}/${d.n_replicas_total} réplicas · ${secs}s`, 'ok');
  } catch (e) { setStatus('Error packing: ' + e, 'err'); }
  finally { $('btnRun').disabled = false; }
}

// ───────────────────────── Charts ─────────────────────────
let chReplicas, chSummary;
function updateStats(d) {
  $('s-best').textContent = d.best_result ?? '—';
  $('s-mean').textContent = (d.mean ?? 0).toFixed(1);
  $('s-std').textContent  = (d.stdev ?? 0).toFixed(2);
  $('s-rep').textContent  = `${d.n_replicas_success}/${d.n_replicas_total}`;

  const reps = (d.all_results || []).map(x => ({ id:x.replica, n:x.n_packed || 0 }))
                                    .sort((a,b) => a.id - b.id);
  const labels = reps.map(x => 'R' + x.id), values = reps.map(x => x.n);

  chReplicas && chReplicas.destroy();
  chReplicas = new Chart($('chReplicas'), {
    type:'bar',
    data:{ labels, datasets:[{ label:'Enzimas por réplica', data:values, backgroundColor:'#FF2600' }] },
    options:{ plugins:{ legend:{ labels:{ font:{ family:'Courier New', size:10 } } } },
              scales:{ x:{ ticks:{ font:{ family:'Courier New', size:9 } } }, y:{ beginAtZero:true, ticks:{ font:{ family:'Courier New', size:9 } } } } }
  });

  chSummary && chSummary.destroy();
  chSummary = new Chart($('chSummary'), {
    type:'bar',
    data:{ labels:['Peor','Media','Mediana','Mejor'],
           datasets:[{ label:'Estadísticas', data:[d.worst||0, d.mean||0, d.median||0, d.best_result||0],
                       backgroundColor:['#378ADD','#7F77DD','#BA7517','#2e8b57'] }] },
    options:{ indexAxis:'y', plugins:{ legend:{ display:false } },
              scales:{ x:{ beginAtZero:true, ticks:{ font:{ family:'Courier New', size:9 } } }, y:{ ticks:{ font:{ family:'Courier New', size:9 } } } } }
  });
}

// ───────────────────────── Eventos ─────────────────────────
$('nEnz').addEventListener('input', e => $('nEnzVal').textContent = e.target.value);
$('nRep').addEventListener('input', e => $('nRepVal').textContent = e.target.value);
$('opacity').addEventListener('input', e => { $('opVal').textContent = e.target.value + '%'; applyOpacity(); });
$('clip').addEventListener('input', e => {
  $('clipVal').textContent = e.target.value + '%';
  if (stage) stage.setParameters({ clipNear: +e.target.value });
});
$('showSphere').addEventListener('change', () => drawSphere(+$('radius').value));
$('radius').addEventListener('input', e => { if ($('showSphere').checked) drawSphere(+e.target.value); });
$('btnPreview').addEventListener('click', doPreview);
$('btnSubstrate').addEventListener('click', doSubstrate);
$('smilesPreset').addEventListener('change', e => { if (e.target.value) $('smiles').value = e.target.value; });
$('nSub').addEventListener('input', e => $('nSubVal').textContent = e.target.value);
$('showBox').addEventListener('change', toggleBox);
$('btnPrepDM').addEventListener('click', prepareDM);
$('btnRadius').addEventListener('click', doRadius);
$('btnRun').addEventListener('click', doRun);
$('btnSpin').addEventListener('click', () => { spinning = !spinning; stage.setSpin(spinning); });
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => showView(t.dataset.view)));
$('btnPore').addEventListener('click', doPore);
['poreCapsid', 'poreAxis', 'poreSub'].forEach(id => $(id).addEventListener('change', doPore));
$('poreSmilesPreset').addEventListener('change', e => { if (e.target.value) { $('poreSmiles').value = e.target.value; doPore(); } });
$('btnChannel').addEventListener('click', showChannel);
$('btnRunHole').addEventListener('click', runHole);
$('btnCribar').addEventListener('click', runScreen);
$('btnManualMut').addEventListener('click', runManualMutant);
$('btnDock').addEventListener('click', runDock);
$('mdPlay').addEventListener('click', playMD);
$('mdPause').addEventListener('click', pauseMD);
$('mdReset').addEventListener('click', resetMD);
$('mdFile').addEventListener('change', e => {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = () => parseMDFile(r.result, f.name);
  r.readAsText(f);
});

// ───────────────────────── Init ─────────────────────────
initNGL();
loadLibrary();
loadLibraryDetail();
loadPoreConfig();
