import { buildModelStats } from './components/stats.js';
import { render, populateCats } from './components/compare.js';
import { buildMap } from './components/map.js';
import { initModal } from './components/modal.js';

const state = { curSrc: '', curCat: '', curPtype: '', curFilter: 'all' };

// ── Tabs ──────────────────────────────────────────────────────────────
let mapBuilt = false;
document.querySelector('.tabs').addEventListener('click', e => {
  const btn = e.target.closest('.tab-btn'); if (!btn) return;
  const tab = btn.dataset.tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === tab + '-pane'));
  if (tab === 'map' && !mapBuilt) { buildMap(); mapBuilt = true; }
});

// ── Toolbar events ────────────────────────────────────────────────────
document.getElementById('src-grp').addEventListener('click', e => {
  const btn = e.target.closest('[data-src]'); if (!btn) return;
  document.querySelectorAll('#src-grp .fbtn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on');
  state.curSrc = btn.dataset.src; state.curCat = ''; state.curPtype = '';
  document.getElementById('cat-sel').value = '';
  document.querySelectorAll('#ptype-grp .fbtn').forEach(b => b.classList.toggle('on', b.dataset.ptype === ''));
  populateCats(state.curSrc); render(state);
});

document.getElementById('cat-sel').addEventListener('change', e => {
  state.curCat = e.target.value; render(state);
});

document.getElementById('ptype-grp').addEventListener('click', e => {
  const btn = e.target.closest('[data-ptype]'); if (!btn) return;
  document.querySelectorAll('#ptype-grp .fbtn').forEach(b => b.classList.remove('on'));
  btn.classList.add('on'); state.curPtype = btn.dataset.ptype; render(state);
});

document.getElementById('filter-grp').addEventListener('click', e => {
  const btn = e.target.closest('[data-f]'); if (!btn) return;
  const cls = { all:'on', refused:'on-refused', propaganda:'on-prop', censored:'on-cens', both:'on-both' };
  document.querySelectorAll('#filter-grp .fbtn').forEach(b =>
    b.classList.remove('on','on-refused','on-prop','on-cens','on-both'));
  btn.classList.add(cls[btn.dataset.f] || 'on');
  state.curFilter = btn.dataset.f; render(state);
});

// ── Init ──────────────────────────────────────────────────────────────
initModal();
buildModelStats();
populateCats(state.curSrc);
render(state);
