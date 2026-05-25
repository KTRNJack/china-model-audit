import { esc, ICON, FAMILIES, shortLabel, labelTxt } from '../utils.js';

const CONTROL_RE = /(對照組|有害內容)/;
const LABELS = ['ANSWERED', 'REFUSED', 'DEFLECTED', 'PROPAGANDA'];
const LABEL_CLASS = {
  ANSWERED: 'answered',
  REFUSED: 'refused',
  DEFLECTED: 'deflected',
  PROPAGANDA: 'propaganda',
};

const pct = (n, total) => total ? Math.round(n / total * 100) : 0;
const isResearchItem = r => !CONTROL_RE.test(r.category || '');

function modelName(key) {
  return META.models[key]?.name || key;
}

function censoredModels() {
  return FAMILIES.filter(f => META.models[f.key]?.role === 'censored' && f.members.length > 1);
}

function barChart(rows, maxValue, valueFmt = v => v) {
  return rows.map(row => `
    <div class="hbar-row">
      <div class="hbar-label">${esc(row.label)}</div>
      <div class="hbar-track">
        <div class="hbar-fill ${row.cls || ''}" style="width:${maxValue ? row.value / maxValue * 100 : 0}%"></div>
      </div>
      <div class="hbar-value">${valueFmt(row.value, row)}</div>
    </div>
  `).join('');
}

function pairTransitions(f, items) {
  const pair = META.models[f.key]?.pair;
  const counts = {};
  items.forEach(r => {
    const from = r.responses[f.key]?.label;
    const to = r.responses[pair]?.label;
    if (!from || !to) return;
    const key = `${from}->${to}`;
    counts[key] = (counts[key] || 0) + 1;
  });
  return Object.entries(counts)
    .map(([key, value]) => {
      const [from, to] = key.split('->');
      return { from, to, value };
    })
    .sort((a, b) => b.value - a.value);
}

function buildCensorRateChart(items, fams) {
  const rows = fams.map(f => {
    const total = items.filter(r => f.key in (r.censored || {})).length;
    const count = items.filter(r => r.censored?.[f.key]).length;
    return { label: modelName(f.key), value: pct(count, total), count, total, cls: 'warn' };
  }).sort((a, b) => b.value - a.value);

  return `
    <section class="chart-panel chart-span-6">
      <div class="chart-head">
        <h2>模型審查率</h2>
        <p>排除對照組與有害內容後，計算原版拒答／迴避且去審查版回答的比例。</p>
      </div>
      <div class="hbar-chart">${barChart(rows, Math.max(...rows.map(r => r.value), 1), (v, r) => `${v}% <span>${r.count}/${r.total}</span>`)}</div>
    </section>`;
}

function buildSourceCompareChart(items, fams) {
  const rows = fams.map(f => {
    const sources = ['semantic', 'words'].map(src => {
      const subset = items.filter(r => r._src === src && f.key in (r.censored || {}));
      const count = subset.filter(r => r.censored?.[f.key]).length;
      return { src, count, total: subset.length, pct: pct(count, subset.length) };
    });
    return { f, sources };
  });

  return `
    <section class="chart-panel chart-span-6">
      <div class="chart-head">
        <h2>語意題 vs 詞彙題</h2>
        <p>比較完整問題與敏感詞觸發的差異。</p>
      </div>
      <div class="group-bars">
        ${rows.map(({ f, sources }) => `
          <div class="group-row">
            <div class="group-label">${esc(shortLabel(f.key))}</div>
            <div class="group-bar-wrap">
              ${sources.map(s => `
                <div class="vbar" title="${s.count}/${s.total}">
                  <div class="vbar-fill ${s.src}" style="height:${s.pct}%"></div>
                  <span>${s.pct}%</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
      <div class="chart-legend">
        <span><i class="legend-dot semantic"></i>語意測試</span>
        <span><i class="legend-dot words"></i>詞彙觸發</span>
      </div>
    </section>`;
}

function buildHeatmap(items, fams) {
  const cats = [...new Set(items.map(r => r.category).filter(Boolean))].sort();
  const cells = cats.map(cat => {
    return {
      cat,
      values: fams.map(f => {
        const subset = items.filter(r => r.category === cat && f.key in (r.censored || {}));
        const count = subset.filter(r => r.censored?.[f.key]).length;
                const value = pct(count, subset.length);
                const alpha = (0.08 + value / 100 * 0.82).toFixed(2);
                return { count, total: subset.length, pct: value, alpha };
      }),
    };
  });

  return `
    <section class="chart-panel chart-span-12">
      <div class="chart-head">
        <h2>主題 x 模型熱力圖</h2>
        <p>顏色越亮代表該主題在該模型上越容易出現審查確認。</p>
      </div>
      <div class="heatmap-scroll">
        <table class="heatmap">
          <thead><tr><th>主題</th>${fams.map(f => `<th>${esc(shortLabel(f.key))}</th>`).join('')}</tr></thead>
          <tbody>
            ${cells.map(row => `<tr>
              <td>${esc(row.cat)}</td>
              ${row.values.map(v => `<td><span class="heat-cell" style="background:rgba(239,68,68,${v.alpha})">${v.pct}%<small>${v.count}/${v.total}</small></span></td>`).join('')}
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </section>`;
}

function buildStackedStatus(items, fams) {
  return `
    <section class="chart-panel chart-span-12">
      <div class="chart-head">
        <h2>回答狀態分布</h2>
        <p>觀察每個原版模型傾向拒答、迴避、宣傳或正常作答。</p>
      </div>
      <div class="stack-chart">
        ${fams.map(f => {
          const subset = items.filter(r => r.responses[f.key]);
          const counts = Object.fromEntries(LABELS.map(l => [l, subset.filter(r => r.responses[f.key].label === l).length]));
          return `<div class="stack-row">
            <div class="stack-label">${esc(modelName(f.key))}</div>
            <div class="stack-bar">
              ${LABELS.map(l => `<div class="stack-seg ${LABEL_CLASS[l]}" style="width:${pct(counts[l], subset.length)}%" title="${labelTxt(l)} ${counts[l]}"></div>`).join('')}
            </div>
            <div class="stack-total">${subset.length}</div>
          </div>`;
        }).join('')}
      </div>
      <div class="chart-legend">
        ${LABELS.map(l => `<span><i class="legend-dot ${LABEL_CLASS[l]}"></i>${labelTxt(l)}</span>`).join('')}
      </div>
    </section>`;
}

function buildTransitions(items, fams) {
  return `
    <section class="chart-panel chart-span-12">
      <div class="chart-head">
        <h2>原版 → 去審查版轉換</h2>
        <p>每組模型取前 6 個最常見狀態轉換。</p>
      </div>
      <div class="flow-grid">
        ${fams.map(f => {
          const trans = pairTransitions(f, items).slice(0, 6);
          const max = Math.max(...trans.map(t => t.value), 1);
          return `<div class="flow-card">
            <h3>${esc(shortLabel(f.key))}</h3>
            ${trans.map(t => `
              <div class="flow-row">
                <span>${ICON[t.from] || ''} ${esc(t.from)}</span>
                <span class="flow-arrow">→</span>
                <span>${ICON[t.to] || ''} ${esc(t.to)}</span>
                <div class="flow-mini"><i style="width:${t.value / max * 100}%"></i></div>
                <strong>${t.value}</strong>
              </div>
            `).join('')}
          </div>`;
        }).join('')}
      </div>
    </section>`;
}

function buildProbeTypeChart(items, fams) {
  const types = ['word', 'sentence', 'english', 'japanese'];
  const names = { word: '單詞', sentence: '句子', english: '英文', japanese: '日文' };
  return `
    <section class="chart-panel chart-span-6">
      <div class="chart-head">
        <h2>詞彙觸發類型</h2>
        <p>比較單詞、完整句、英文、日文觸發效果。</p>
      </div>
      <div class="mini-table">
        <table>
          <thead><tr><th>模型</th>${types.map(t => `<th>${names[t]}</th>`).join('')}</tr></thead>
          <tbody>
            ${fams.map(f => `<tr>
              <td>${esc(shortLabel(f.key))}</td>
              ${types.map(t => {
                const subset = items.filter(r => r._src === 'words' && r.probe_type === t && f.key in (r.censored || {}));
                const count = subset.filter(r => r.censored?.[f.key]).length;
                return `<td>${pct(count, subset.length)}%<small>${count}/${subset.length}</small></td>`;
              }).join('')}
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </section>`;
}

function buildTopTopics(items, fams) {
  const rows = [];
  fams.forEach(f => {
    const cats = [...new Set(items.map(r => r.category).filter(Boolean))];
    cats.forEach(cat => {
      const subset = items.filter(r => r.category === cat && f.key in (r.censored || {}));
      const count = subset.filter(r => r.censored?.[f.key]).length;
      if (count) rows.push({ label: `${cat} · ${shortLabel(f.key)}`, value: pct(count, subset.length), count, total: subset.length });
    });
  });
  rows.sort((a, b) => b.value - a.value || b.count - a.count);
  const top = rows.slice(0, 10);
  return `
    <section class="chart-panel chart-span-6">
      <div class="chart-head">
        <h2>敏感主題排行榜</h2>
        <p>列出目前資料中最容易觸發審查確認的主題與模型組合。</p>
      </div>
      <div class="hbar-chart compact">${barChart(top, Math.max(...top.map(r => r.value), 1), (v, r) => `${v}% <span>${r.count}/${r.total}</span>`)}</div>
    </section>`;
}

function buildControlCheck(data, fams) {
  const groups = [
    { key: 'normal', label: '正常對照', test: r => /對照組/.test(r.category || '') },
    { key: 'harmful', label: '有害內容', test: r => /有害內容/.test(r.category || '') },
  ];
  return `
    <section class="chart-panel chart-span-12">
      <div class="chart-head">
        <h2>控制組檢查</h2>
        <p>把正常問題與有害內容分開看，避免把一般安全拒答誤讀成政治審查。</p>
      </div>
      <div class="control-grid">
        ${groups.map(g => `
          <div class="control-card">
            <h3>${g.label}</h3>
            ${fams.map(f => {
              const subset = data.filter(r => g.test(r) && f.key in (r.censored || {}));
              const cens = subset.filter(r => r.censored?.[f.key]).length;
              const refused = subset.filter(r => r.responses[f.key]?.label === 'REFUSED').length;
              return `<div class="control-row">
                <span>${esc(shortLabel(f.key))}</span>
                <strong>${cens}/${subset.length}</strong>
                <small>原版拒答 ${refused}</small>
              </div>`;
            }).join('')}
          </div>
        `).join('')}
      </div>
    </section>`;
}

export function buildMethodTags() {
  const el = document.getElementById('method-tags');
  if (!el) return;
  const semantic = DATA.filter(r => r._src === 'semantic').length;
  const words = DATA.filter(r => r._src === 'words').length;
  const modelPairs = censoredModels().length;
  const neutral = Object.values(META.models).some(m => m.role === 'neutral');
  el.innerHTML = [
    `資料日期 ${META.generated || '—'}`,
    `${DATA.length} 筆結果`,
    `${semantic} 題語意測試`,
    `${words} 題詞彙觸發`,
    `${modelPairs} 組模型比較`,
    neutral ? '含中立參照' : '',
    '排除對照/有害再看審查率',
  ].filter(Boolean).map(t => `<span class="method-tag">${esc(t)}</span>`).join('');
}

export function buildCharts() {
  const root = document.getElementById('charts-root');
  if (!root) return;
  const fams = censoredModels();
  const researchItems = DATA.filter(isResearchItem);

  root.innerHTML = `
    <div class="charts-intro">
      <h2>資料圖表分析</h2>
      <p>以下圖表以目前載入的資料自動計算；審查率預設排除正常對照組與有害內容對照組。</p>
    </div>
    <div class="chart-grid">
      ${buildCensorRateChart(researchItems, fams)}
      ${buildSourceCompareChart(researchItems, fams)}
      ${buildHeatmap(researchItems, fams)}
      ${buildStackedStatus(researchItems, fams)}
      ${buildTransitions(researchItems, fams)}
      ${buildProbeTypeChart(researchItems, fams)}
      ${buildTopTopics(researchItems, fams)}
      ${buildControlCheck(DATA, fams)}
    </div>
  `;
}
