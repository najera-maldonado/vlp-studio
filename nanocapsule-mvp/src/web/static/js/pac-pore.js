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
    $('pore-badge').textContent = '';
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

