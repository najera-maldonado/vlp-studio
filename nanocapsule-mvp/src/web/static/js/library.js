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

