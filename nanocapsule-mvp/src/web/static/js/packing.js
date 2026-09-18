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
