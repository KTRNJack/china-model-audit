import { esc, LABEL, ICON, labelTxt, shortLabel, FAMILIES } from '../utils.js';

const RESP_LIMIT = 300;

function isCensored(r)    { return Object.values(r.censored||{}).some(Boolean); }
function isRefused(r)     { return Object.entries(META.models).some(([m,i]) => i.role==='censored' && r.responses[m]?.label==='REFUSED'); }
function isPropaganda(r)  { return Object.entries(META.models).some(([m,i]) => i.role==='censored' && r.responses[m]?.label==='PROPAGANDA'); }
function isBothAnswered(r){ return Object.entries(META.models).some(([m,i]) => i.role==='censored' && i.pair && r.responses[m]?.label==='ANSWERED' && r.responses[i.pair]?.label==='ANSWERED'); }

function divergeSummary(r) {
  const fams = FAMILIES.filter(f => r.responses[f.key]);
  if (!fams.length) return '';
  const labels = fams.map(f => r.responses[f.key].label);
  if (new Set(labels).size === 1) {
    const l = labels[0];
    return `全 ${ICON[l]||''} ${labelTxt(l).replace(/^[^\s]+\s/,'')}`;
  }
  return fams.map(f => `${shortLabel(f.key)} ${ICON[r.responses[f.key].label]||'?'}`).join(' · ');
}

function renderPane(side, m) {
  if (!side) return '';
  const thinkHtml = side.thinking
    ? `<details class="think"><summary>🧠 思考過程</summary><div class="think-body">${esc(side.thinking)}</div></details>`
    : '';
  const resp = side.response || '';
  const isLong = resp.length > RESP_LIMIT;
  const displayText = isLong ? resp.slice(0, RESP_LIMIT) : resp;
  const fullBtn = isLong
    ? `<div class="resp-truncated">…（共 ${resp.length.toLocaleString()} 字）</div>
       <button class="btn-fulltext" onclick="openRespModal(this)"
         data-full="${esc(resp)}" data-title="${esc(m.name)}">查看全文 →</button>`
    : '';
  return `<div class="response-pane">
    <div class="pane-label">
      <span class="dot" style="background:${m.dot}"></span>
      <span>${m.name}</span>
      <span class="badge ${side.label}">${labelTxt(side.label)}</span>
    </div>
    <div class="resp-text">${esc(displayText) || '（無回應）'}</div>
    ${fullBtn}${thinkHtml}
  </div>`;
}

export function populateCats(curSrc) {
  const base = curSrc ? DATA.filter(r => r._src === curSrc) : DATA;
  const cats = [...new Set(base.map(r => r.category).filter(Boolean))].sort();
  const sel = document.getElementById('cat-sel');
  sel.innerHTML = '<option value="">全部</option>';
  cats.forEach(c => { const o = document.createElement('option'); o.value = c; o.textContent = c; sel.appendChild(o); });
}

export function render(state) {
  const { curSrc, curCat, curPtype, curFilter } = state;
  const mainEl = document.getElementById('main');
  const noEl   = document.getElementById('no-results');

  const results = DATA.filter(r => {
    if (curSrc   && r._src       !== curSrc)   return false;
    if (curCat   && r.category   !== curCat)   return false;
    if (curPtype && r.probe_type !== curPtype) return false;
    if (curFilter === 'refused')    return isRefused(r);
    if (curFilter === 'propaganda') return isPropaganda(r);
    if (curFilter === 'censored')   return isCensored(r);
    if (curFilter === 'both')       return isBothAnswered(r);
    return true;
  });

  const hasPtype = results.some(r => r.probe_type);
  document.getElementById('ptype-section').classList.toggle('hidden', !hasPtype);

  mainEl.innerHTML = '';
  if (!results.length) { noEl.style.display = 'block'; return; }
  noEl.style.display = 'none';

  const ptypeLabel = { word:'單詞', sentence:'句子', english:'EN', japanese:'JP' };
  const byCat = {};
  results.forEach(r => { const k = r.category || '（未分類）'; (byCat[k] = byCat[k]||[]).push(r); });

  Object.entries(byCat).forEach(([cat, items]) => {
    const h = document.createElement('div');
    h.className = 'cat-hdr'; h.textContent = cat; mainEl.appendChild(h);

    items.forEach(r => {
      const card = document.createElement('div');
      card.className = 'card' + (isCensored(r) ? ' censored' : '');

      const activeFams = FAMILIES.filter(f => f.members.some(m => r.responses[m]));
      const multiFamily = activeFams.length > 1;
      const ptypeBadge = r.probe_type
        ? `<span class="ptype-badge ptype-${r.probe_type}">${ptypeLabel[r.probe_type]||r.probe_type}</span>` : '';

      const hdr = document.createElement('div');
      hdr.className = 'card-hdr';
      hdr.innerHTML = `<span class="chevron">▶</span>
        <span class="question">${esc(r.question)}</span>
        <div class="card-meta">
          ${divergeSummary(r) ? `<span class="diverge-line">${divergeSummary(r)}</span>` : ''}
          <div class="badges">${ptypeBadge}</div>
        </div>`;

      const body = document.createElement('div');
      body.className = 'card-body';
      let bodyHtml = '';

      if (multiFamily) {
        bodyHtml += `<div class="family-tabs">` + activeFams.map((f, i) => {
          const icon = ICON[r.responses[f.key]?.label] || '';
          return `<button class="ftab${i===0?' active':''}" data-fkey="${f.key}">
            <span class="dot" style="background:${f.dot}"></span>
            <span>${esc(shortLabel(f.key))}</span>
            ${icon ? `<span>${icon}</span>` : ''}
          </button>`;
        }).join('') + `</div>`;
      }

      activeFams.forEach((f, i) => {
        const shown = !multiFamily || i === 0;
        const presentMembers = f.members.filter(m => r.responses[m]);
        bodyHtml += `<div class="family-pane" data-fkey="${f.key}"${shown ? '' : ' style="display:none"'}>
          <div class="response-grid" style="grid-template-columns:repeat(${presentMembers.length},1fr)">
            ${presentMembers.map(m => renderPane(r.responses[m], META.models[m])).join('')}
          </div>
          ${r.censored[f.key] ? '<div class="cens-banner">⚠️ 審查確認：原版拒答／迴避，去審查版正常作答</div>' : ''}
        </div>`;
      });

      body.innerHTML = bodyHtml;
      hdr.addEventListener('click', () => {
        const open = body.classList.toggle('open');
        hdr.classList.toggle('open', open);
      });
      body.addEventListener('click', e => {
        const ftab = e.target.closest('.ftab');
        if (!ftab) return;
        e.stopPropagation();
        const fkey = ftab.dataset.fkey;
        body.querySelectorAll('.ftab').forEach(t => t.classList.toggle('active', t.dataset.fkey === fkey));
        body.querySelectorAll('.family-pane').forEach(p => { p.style.display = p.dataset.fkey === fkey ? '' : 'none'; });
      });

      card.appendChild(hdr); card.appendChild(body); mainEl.appendChild(card);
    });
  });
}
