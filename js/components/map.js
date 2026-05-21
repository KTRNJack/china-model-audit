import { esc, ICON, labelTxt } from '../utils.js';

export function buildMap() {
  const rows = DATA.filter(r => r._src === 'semantic');
  const censoredModels = Object.entries(META.models)
    .filter(([, info]) => info.role === 'censored')
    .sort((a, b) => {
      const co = (a[1].company||'').localeCompare(b[1].company||'');
      return co !== 0 ? co : (a[1].name||'').localeCompare(b[1].name||'');
    });

  if (!censoredModels.length || !rows.length) {
    document.getElementById('map-container').innerHTML = '<p style="color:var(--muted);padding:20px">尚無資料</p>';
    return;
  }

  function consistency(r) {
    const labels = censoredModels.map(([m]) => r.responses[m]?.label).filter(Boolean);
    if (!labels.length) return { text: '—', cls: '' };
    if (new Set(labels).size === 1) return { text: '全一致', cls: '' };
    const byCompany = {};
    censoredModels.forEach(([m, info]) => {
      if (!r.responses[m]) return;
      const co = info.company || '?';
      (byCompany[co] = byCompany[co] || new Set()).add(r.responses[m].label);
    });
    const internalConsist = Object.values(byCompany).every(s => s.size === 1);
    if (internalConsist && Object.keys(byCompany).length > 1) return { text: '家族分歧', cls: 'consist-fam' };
    return { text: '各異', cls: 'consist-diff' };
  }

  let prevCo = null;
  const colHeaders = censoredModels.map(([, m]) => {
    const isNew = m.company !== prevCo && prevCo !== null;
    prevCo = m.company;
    const sz = (m.name.match(/\d+B/)||[''])[0];
    const base = m.name.replace(/\s*\d+B\s*/g,'').trim();
    return `<th${isNew ? ' class="fam-sep"' : ''}>
      <div class="col-hdr">
        <span class="co">${m.company||''}</span>
        <span class="mn"><span class="dot" style="background:${m.dot}"></span>${base}<span class="col-sz">${sz}</span></span>
      </div>
    </th>`;
  });

  const thead = `<thead><tr>
    <th class="q-col">題目</th>
    ${colHeaders.join('')}
    <th style="min-width:68px;font-size:.68rem;color:var(--muted)">一致性</th>
  </tr></thead>`;

  const byCat = {};
  rows.forEach(r => { const k = r.category || '（未分類）'; (byCat[k] = byCat[k]||[]).push(r); });

  let tbody = '<tbody>';
  Object.entries(byCat).forEach(([cat, items]) => {
    tbody += `<tr class="cat-row"><td colspan="${censoredModels.length + 2}">${cat}</td></tr>`;
    items.forEach(r => {
      const c = consistency(r);
      tbody += `<tr><td class="q-cell">${esc(r.question)}</td>`;
      prevCo = null;
      censoredModels.forEach(([model, info]) => {
        const isNew = info.company !== prevCo && prevCo !== null;
        prevCo = info.company;
        const resp = r.responses[model];
        const cls = (resp ? resp.label : 'NONE') + (isNew ? ' fam-sep' : '');
        tbody += `<td class="map-cell ${cls}" title="${resp ? labelTxt(resp.label) : '無資料'}">${resp ? (ICON[resp.label]||'?') : '—'}</td>`;
      });
      tbody += `<td class="consist-cell ${c.cls}">${c.text}</td></tr>`;
    });
  });
  tbody += '</tbody>';

  document.getElementById('map-container').innerHTML =
    `<table class="map-table">${thead}${tbody}</table>`;
}
