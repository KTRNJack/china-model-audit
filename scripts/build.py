#!/usr/bin/env python3
"""
build.py — 把資料內嵌進 index.html，產出可獨立開啟的純 HTML 頁面
用法：python3 scripts/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

SOURCES = [
    ("semantic", ROOT / "data" / "data_2026-05-20_23-18_v3_three_way.json"),
    ("words",    ROOT / "data" / "words_deepseek-r1-7b_2026-05-20.json"),
]

def load_all():
    all_results = []
    for src_key, path in SOURCES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for r in data["results"]:
            r["_src"] = src_key
        all_results.extend(data["results"])
    return all_results

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepSeek-R1 7B 審查機制分析</title>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a;
    --border: #2d3148; --text: #e2e8f0; --muted: #8892a4;
    --refused: #ef4444; --refused-bg: rgba(239,68,68,0.1);
    --answered: #22c55e; --answered-bg: rgba(34,197,94,0.1);
    --deflected: #f59e0b; --deflected-bg: rgba(245,158,11,0.1);
    --accent: #6366f1; --thinking: #818cf8; --thinking-bg: rgba(129,140,248,0.06);
    --propaganda: #a855f7; --propaganda-bg: rgba(168,85,247,0.1);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; line-height: 1.6; }

  header { border-bottom: 1px solid var(--border); padding: 24px 32px; }
  header h1 { font-size: 1.4rem; font-weight: 700; }
  header p { color: var(--muted); font-size: 0.875rem; margin-top: 4px; }
  .method-note { margin-top: 8px; font-size: 0.78rem; color: var(--muted); background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 8px 14px; display: inline-block; }
  .method-note strong { color: var(--text); }

  .model-bar { display: flex; gap: 24px; flex-wrap: wrap; padding: 12px 32px; background: var(--surface); border-bottom: 1px solid var(--border); }
  .model-tag { font-size: 0.8rem; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
  .dot-orig { background: #818cf8; } .dot-neutral { background: #94a3b8; } .dot-ablit { background: #34d399; }

  .stats { display: flex; gap: 16px; padding: 16px 32px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .stat { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 20px; min-width: 120px; }
  .stat .num { font-size: 1.6rem; font-weight: 700; }
  .stat .lbl { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
  .stat.refused .num { color: var(--refused); } .stat.answered .num { color: var(--answered); }
  .stat.diff .num { color: var(--deflected); } .stat.prop .num { color: var(--propaganda); }

  .toolbar { display: flex; gap: 10px; align-items: center; padding: 14px 32px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }
  .toolbar-label { font-size: 0.8rem; color: var(--muted); white-space: nowrap; }
  .toolbar select { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 5px 10px; border-radius: 6px; font-size: 0.85rem; cursor: pointer; }
  .toolbar-sep { width: 1px; height: 24px; background: var(--border); flex-shrink: 0; margin: 0 4px; }
  .btn-group { display: flex; gap: 4px; flex-wrap: wrap; }
  .fbtn { padding: 5px 12px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--muted); font-size: 0.8rem; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
  .fbtn:hover { border-color: var(--accent); color: var(--text); }
  .fbtn.active          { background: var(--accent);          border-color: var(--accent);          color: white; }
  .fbtn.active-refused  { background: var(--refused-bg);      border-color: var(--refused);          color: var(--refused); }
  .fbtn.active-prop     { background: var(--propaganda-bg);   border-color: var(--propaganda);       color: var(--propaganda); }
  .fbtn.active-censored { background: rgba(245,158,11,0.15);  border-color: var(--deflected);        color: var(--deflected); }
  .fbtn.active-answered { background: var(--answered-bg);     border-color: var(--answered);         color: var(--answered); }

  #ptype-section { display: flex; align-items: center; gap: 10px; }
  #ptype-section.hidden { display: none; }

  main { padding: 24px 32px; max-width: 1400px; }
  #no-results { text-align: center; color: var(--muted); padding: 60px 32px; display: none; }

  .category-header { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); margin: 32px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
  .category-header:first-child { margin-top: 0; }

  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; margin-bottom: 12px; overflow: hidden; }
  .card-header { padding: 14px 18px; display: flex; align-items: flex-start; gap: 12px; cursor: pointer; }
  .card-header:hover { background: rgba(255,255,255,0.02); }
  .question { font-size: 0.95rem; flex: 1; }
  .badges { display: flex; gap: 8px; flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end; }
  .badge { font-size: 0.72rem; font-weight: 600; padding: 3px 8px; border-radius: 4px; white-space: nowrap; }
  .badge.REFUSED    { background: var(--refused-bg);    color: var(--refused);    border: 1px solid rgba(239,68,68,0.3); }
  .badge.ANSWERED   { background: var(--answered-bg);   color: var(--answered);   border: 1px solid rgba(34,197,94,0.3); }
  .badge.DEFLECTED  { background: var(--deflected-bg);  color: var(--deflected);  border: 1px solid rgba(245,158,11,0.3); }
  .badge.PROPAGANDA { background: var(--propaganda-bg); color: var(--propaganda); border: 1px solid rgba(168,85,247,0.3); }

  .card-body { display: none; border-top: 1px solid var(--border); }
  .card-body.open { display: block; }
  .response-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; }
  .response-grid.two-col { grid-template-columns: 1fr 1fr; }
  .response-pane { padding: 16px 18px; font-size: 0.85rem; line-height: 1.7; border-right: 1px solid var(--border); }
  .response-pane:last-child { border-right: none; }
  .pane-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
  .response-content { white-space: pre-wrap; word-break: break-word; }

  .thinking-block { margin-top: 12px; border-top: 1px solid var(--border); padding-top: 10px; }
  .thinking-block summary { font-size: 0.72rem; color: var(--thinking); cursor: pointer; user-select: none; list-style: none; display: flex; align-items: center; gap: 6px; }
  .thinking-block summary::-webkit-details-marker { display: none; }
  .thinking-block summary::before { content: "▶"; font-size: 0.6rem; transition: transform 0.2s; }
  .thinking-block[open] summary::before { transform: rotate(90deg); }
  .thinking-content { margin-top: 8px; font-size: 0.8rem; color: var(--muted); white-space: pre-wrap; word-break: break-word; background: var(--thinking-bg); border-left: 2px solid var(--thinking); padding: 8px 12px; border-radius: 0 4px 4px 0; }

  .censored-banner { background: rgba(245,158,11,0.08); border-top: 1px solid rgba(245,158,11,0.2); padding: 8px 18px; font-size: 0.75rem; color: var(--deflected); }
  .card.has-diff { border-left: 3px solid var(--deflected); }
  .chevron { color: var(--muted); font-size: 0.85rem; transition: transform 0.2s; flex-shrink: 0; margin-top: 2px; }
  .card-header.expanded .chevron { transform: rotate(90deg); }

  .ptype-badge { font-size: 0.68rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; white-space: nowrap; border: 1px solid; flex-shrink: 0; }
  .ptype-word     { color: #a78bfa; border-color: rgba(167,139,250,0.4); background: rgba(167,139,250,0.1); }
  .ptype-sentence { color: #38bdf8; border-color: rgba(56,189,248,0.4);  background: rgba(56,189,248,0.1); }
  .ptype-english  { color: #fb923c; border-color: rgba(251,146,60,0.4);  background: rgba(251,146,60,0.1); }
  .ptype-japanese { color: #f472b6; border-color: rgba(244,114,182,0.4); background: rgba(244,114,182,0.1); }

  @media (max-width: 768px) {
    .response-grid, .response-grid.two-col { grid-template-columns: 1fr; }
    header, .toolbar, .stats, main, .model-bar, #no-results { padding-left: 16px; padding-right: 16px; }
  }
</style>
</head>
<body>

<header>
  <h1>DeepSeek-R1 7B 審查機制分析</h1>
  <p>比較原版模型（有審查訓練）與去審查版（Abliterated）對敏感問題的回應差異</p>
  <div class="method-note">
    <strong>方法論：</strong>「審查確認」= 原版拒答／迴避，且去審查版正常作答。兩者皆拒答（如真正有害內容）不計入審查差異。
  </div>
</header>

<div class="model-bar">
  <div class="model-tag"><span class="dot dot-orig"></span>原版：deepseek-r1:7b</div>
  <div class="model-tag"><span class="dot dot-neutral"></span>中立參照：llama3.1:8b（語意測試）</div>
  <div class="model-tag"><span class="dot dot-ablit"></span>去審查：deepseek-r1-7b-abliterated</div>
</div>

<div class="stats">
  <div class="stat"><div class="num" id="s-total">__TOTAL__</div><div class="lbl">總題目</div></div>
  <div class="stat refused"><div class="num" id="s-refused">__REFUSED__</div><div class="lbl">原版拒答</div></div>
  <div class="stat prop"><div class="num" id="s-propaganda">__PROPAGANDA__</div><div class="lbl">原版宣傳</div></div>
  <div class="stat diff"><div class="num" id="s-censored">__CENSORED__</div><div class="lbl">審查確認</div></div>
  <div class="stat answered"><div class="num" id="s-both">__BOTH__</div><div class="lbl">兩者皆答</div></div>
</div>

<div class="toolbar">
  <span class="toolbar-label">來源：</span>
  <div class="btn-group" id="src-group">
    <button class="fbtn active" data-src="">全部</button>
    <button class="fbtn" data-src="semantic">語意測試</button>
    <button class="fbtn" data-src="words">詞彙觸發</button>
  </div>

  <div class="toolbar-sep"></div>
  <span class="toolbar-label">類別：</span>
  <select id="cat-sel"><option value="">全部</option></select>

  <div id="ptype-section" class="hidden">
    <div class="toolbar-sep"></div>
    <span class="toolbar-label">類型：</span>
    <div class="btn-group" id="ptype-group">
      <button class="fbtn active" data-ptype="">全部</button>
      <button class="fbtn" data-ptype="word">單詞</button>
      <button class="fbtn" data-ptype="sentence">句子</button>
      <button class="fbtn" data-ptype="english">英文</button>
      <button class="fbtn" data-ptype="japanese">日文</button>
    </div>
  </div>

  <div class="toolbar-sep" style="margin-left:auto"></div>
  <div class="btn-group" id="result-group">
    <button class="fbtn active" data-filter="all">全部</button>
    <button class="fbtn" data-filter="refused">原版拒答</button>
    <button class="fbtn" data-filter="propaganda">原版宣傳</button>
    <button class="fbtn" data-filter="censored">審查確認</button>
    <button class="fbtn" data-filter="both">兩者皆答</button>
  </div>
</div>

<main id="main"></main>
<div id="no-results">沒有符合條件的結果</div>

<script>
const DATA = __DATA__;

let curSrc = '', curCat = '', curPtype = '', curFilter = 'all';
const mainEl      = document.getElementById('main');
const noResultsEl = document.getElementById('no-results');

function updateStats(results) {
  document.getElementById('s-total').textContent     = results.length;
  document.getElementById('s-refused').textContent   = results.filter(r => r.original.label === 'REFUSED').length;
  document.getElementById('s-propaganda').textContent= results.filter(r => r.original.label === 'PROPAGANDA').length;
  document.getElementById('s-censored').textContent  = results.filter(r => r.censored).length;
  document.getElementById('s-both').textContent      = results.filter(r =>
    r.original.label === 'ANSWERED' && r.abliterated.label === 'ANSWERED').length;
}

function getCats(src) {
  const base = src ? DATA.filter(r => r._src === src) : DATA;
  return [...new Set(base.map(r => r.category).filter(Boolean))].sort();
}

function populateCats(src) {
  const sel = document.getElementById('cat-sel');
  sel.innerHTML = '<option value="">全部</option>';
  getCats(src).forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c; sel.appendChild(o);
  });
}

function filtered() {
  return DATA.filter(r => {
    if (curSrc   && r._src       !== curSrc)   return false;
    if (curCat   && r.category   !== curCat)   return false;
    if (curPtype && r.probe_type !== curPtype) return false;
    if (curFilter === 'refused')    return r.original.label === 'REFUSED';
    if (curFilter === 'propaganda') return r.original.label === 'PROPAGANDA';
    if (curFilter === 'censored')   return r.censored;
    if (curFilter === 'both')       return r.original.label === 'ANSWERED' && r.abliterated.label === 'ANSWERED';
    return true;
  });
}

function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function labelText(l) {
  return {REFUSED:'🚫 拒答', ANSWERED:'✅ 已答', DEFLECTED:'↩ 迴避', PROPAGANDA:'📢 宣傳'}[l] || l || '?';
}

function renderPane(side, dotClass, title) {
  if (!side) return '';
  const thinkHTML = side.thinking
    ? `<details class="thinking-block"><summary>🧠 思考過程</summary><div class="thinking-content">${esc(side.thinking)}</div></details>`
    : '';
  return `<div class="response-pane">
    <div class="pane-label"><span class="dot ${dotClass}"></span>${title}
      <span class="badge ${side.label}">${labelText(side.label)}</span>
    </div>
    <div class="response-content">${esc(side.response) || '（無回應）'}</div>
    ${thinkHTML}
  </div>`;
}

function render() {
  const results = filtered();
  const hasPtype = results.some(r => r.probe_type);
  document.getElementById('ptype-section').classList.toggle('hidden', !hasPtype);
  updateStats(results);
  mainEl.innerHTML = '';
  if (!results.length) { noResultsEl.style.display = 'block'; return; }
  noResultsEl.style.display = 'none';

  const byCategory = {};
  results.forEach(r => { const k = r.category || '（未分類）'; (byCategory[k] = byCategory[k]||[]).push(r); });

  const ptypeLabels = {word:'單詞', sentence:'句子', english:'EN', japanese:'JP'};
  Object.entries(byCategory).forEach(([cat, items]) => {
    const h = document.createElement('div');
    h.className = 'category-header'; h.textContent = cat; mainEl.appendChild(h);

    items.forEach(r => {
      const card = document.createElement('div');
      card.className = 'card' + (r.censored ? ' has-diff' : '');
      const hasNeutral = !!r.neutral;
      const ptypeBadge = r.probe_type
        ? `<span class="ptype-badge ptype-${r.probe_type}">${ptypeLabels[r.probe_type]||r.probe_type}</span>`
        : '';

      const hdr = document.createElement('div');
      hdr.className = 'card-header';
      hdr.innerHTML = `<span class="chevron">▶</span>
        <span class="question">${esc(r.question)}</span>
        <div class="badges">
          ${ptypeBadge}
          <span class="badge ${r.original.label}" title="原版">原版 ${labelText(r.original.label)}</span>
          ${hasNeutral ? `<span class="badge ${r.neutral.label}" title="中立">中立 ${labelText(r.neutral.label)}</span>` : ''}
          <span class="badge ${r.abliterated.label}" title="去審查">去審查 ${labelText(r.abliterated.label)}</span>
        </div>`;

      const body = document.createElement('div');
      body.className = 'card-body';
      body.innerHTML = `
        <div class="response-grid${hasNeutral ? '' : ' two-col'}">
          ${renderPane(r.original,    'dot-orig',    '原版回應')}
          ${hasNeutral ? renderPane(r.neutral, 'dot-neutral', '中立參照') : ''}
          ${renderPane(r.abliterated, 'dot-ablit',   '去審查回應')}
        </div>
        ${r.censored ? '<div class="censored-banner">⚠️ 審查確認：原版拒答／迴避，去審查版正常作答</div>' : ''}`;

      hdr.addEventListener('click', () => {
        const open = body.classList.toggle('open');
        hdr.classList.toggle('expanded', open);
      });
      card.appendChild(hdr); card.appendChild(body); mainEl.appendChild(card);
    });
  });
}

// 事件綁定
document.getElementById('src-group').addEventListener('click', e => {
  const btn = e.target.closest('[data-src]'); if (!btn) return;
  document.querySelectorAll('#src-group .fbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  curSrc = btn.dataset.src; curCat = ''; curPtype = '';
  document.getElementById('cat-sel').value = '';
  document.querySelectorAll('#ptype-group .fbtn').forEach(b => b.classList.toggle('active', b.dataset.ptype === ''));
  populateCats(curSrc);
  render();
});

document.getElementById('cat-sel').addEventListener('change', e => { curCat = e.target.value; render(); });

document.getElementById('ptype-group').addEventListener('click', e => {
  const btn = e.target.closest('[data-ptype]'); if (!btn) return;
  document.querySelectorAll('#ptype-group .fbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active'); curPtype = btn.dataset.ptype; render();
});

document.getElementById('result-group').addEventListener('click', e => {
  const btn = e.target.closest('[data-filter]'); if (!btn) return;
  document.querySelectorAll('#result-group .fbtn').forEach(b =>
    b.classList.remove('active','active-refused','active-prop','active-censored','active-answered'));
  const cls = {refused:'active-refused', propaganda:'active-prop', censored:'active-censored', both:'active-answered'}[btn.dataset.filter] || 'active';
  btn.classList.add(cls); curFilter = btn.dataset.filter; render();
});

// 初始填充類別並渲染
populateCats('');
render();
</script>
</body>
</html>
"""

def build():
    all_results = load_all()

    stats = {
        "TOTAL": len(all_results),
        "REFUSED": sum(1 for r in all_results if r["original"]["label"] == "REFUSED"),
        "PROPAGANDA": sum(1 for r in all_results if r["original"]["label"] == "PROPAGANDA"),
        "CENSORED": sum(1 for r in all_results if r.get("censored")),
        "BOTH": sum(1 for r in all_results if r["original"]["label"] == "ANSWERED" and r["abliterated"]["label"] == "ANSWERED"),
    }

    data_json = json.dumps(all_results, ensure_ascii=False)

    html = TEMPLATE
    html = html.replace("__DATA__", data_json)
    for key, val in stats.items():
        html = html.replace(f"__{key}__", str(val))

    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"✅ index.html 已生成 ({len(html)//1024} KB, {len(all_results)} 筆資料)")
    print(f"   可直接用瀏覽器開啟：{out}")

if __name__ == "__main__":
    build()
