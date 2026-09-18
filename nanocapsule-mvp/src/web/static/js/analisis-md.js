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

