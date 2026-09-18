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

