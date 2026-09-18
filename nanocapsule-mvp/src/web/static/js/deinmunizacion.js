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

