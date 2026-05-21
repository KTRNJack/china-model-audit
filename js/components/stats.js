import { FAMILIES } from '../utils.js';

export function buildModelStats() {
  const container = document.getElementById('model-comparison');
  const semData = DATA.filter(r => r._src === 'semantic');

  const stats = {};
  FAMILIES.forEach(f => {
    const entries = semData.filter(r => r.responses[f.key]);
    if (!entries.length) return;
    const total = entries.length;
    const refused    = entries.filter(r => r.responses[f.key]?.label === 'REFUSED').length;
    const propaganda = entries.filter(r => r.responses[f.key]?.label === 'PROPAGANDA').length;
    const deflected  = entries.filter(r => r.responses[f.key]?.label === 'DEFLECTED').length;
    const censored   = entries.filter(r => r.censored[f.key]).length;
    const answered   = entries.filter(r => r.responses[f.key]?.label === 'ANSWERED').length;
    stats[f.key] = {
      total, refused, propaganda, deflected, censored, answered,
      score: Math.round((refused + propaganda + deflected) / total * 100),
    };
  });

  const keys = Object.keys(stats);
  if (!keys.length) { container.innerHTML = ''; return; }

  const maxR = Math.max(...keys.map(k => stats[k].refused));
  const maxP = Math.max(...keys.map(k => stats[k].propaganda));
  const maxC = Math.max(...keys.map(k => stats[k].censored));

  const topOf = fn => [...keys].sort((a,b) => fn(b) - fn(a))[0];
  const avgScore = Math.round(keys.reduce((s,k) => s + stats[k].score, 0) / keys.length);
  const summaryHtml = `<div class="stat-summary">
    <span class="stat-summary-item">平均審查率：<strong>${avgScore}%</strong></span>
    <span class="stat-summary-item">最常拒答：<strong>${META.models[topOf(k=>stats[k].refused)]?.name || '—'}</strong></span>
    <span class="stat-summary-item">宣傳最多：<strong>${META.models[topOf(k=>stats[k].propaganda)]?.name || '—'}</strong></span>
    <span class="stat-summary-item">最開放：<strong>${META.models[topOf(k=>stats[k].answered)]?.name || '—'}</strong></span>
  </div>`;

  const sortedFamilies = FAMILIES.filter(f => stats[f.key])
    .sort((a, b) => stats[b.key].score - stats[a.key].score);

  const rows = sortedFamilies.map(f => {
    const s = stats[f.key];
    const m = META.models[f.key];
    const pct = n => Math.round(n / s.total * 100);
    const bar = (n, max, color) => `
      <div class="stat-cell">
        <span class="stat-n" style="color:${color}">${n}</span>
        <div class="stat-bar"><div style="width:${max ? Math.round(n/max*100) : 0}%;background:${color}"></div></div>
        <span class="stat-p">${pct(n)}%</span>
      </div>`;
    const scoreColor = s.score >= 60 ? 'var(--refused)' : s.score >= 30 ? 'var(--deflected)' : 'var(--answered)';
    return `<tr>
      <td><div class="stat-model-cell">
        <span class="dot" style="background:${m.dot}"></span>
        <span>${m.name}</span>
      </div></td>
      <td class="stat-score-cell"><span class="stat-score-badge" style="--sc:${scoreColor}">${s.score}%</span></td>
      <td>${bar(s.refused,    maxR, 'var(--refused)')}</td>
      <td>${bar(s.propaganda, maxP, 'var(--propaganda)')}</td>
      <td>${bar(s.censored,   maxC, 'var(--deflected)')}</td>
      <td class="stat-answered-cell">${s.answered}<span class="stat-pct-sm">${pct(s.answered)}%</span></td>
    </tr>`;
  }).join('');

  container.innerHTML = `${summaryHtml}
    <table class="stat-table">
      <thead><tr>
        <th>模型（語意測試）</th>
        <th title="拒答 + 宣傳 + 迴避 占比">審查率 ↓</th>
        <th>🚫 拒答</th>
        <th>📢 宣傳</th>
        <th>⚠️ 審查確認</th>
        <th>✅ 正常作答</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}
