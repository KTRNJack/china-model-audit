export const esc = s => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

export const LABEL = { REFUSED:'🚫 拒答', ANSWERED:'✅ 已答', DEFLECTED:'↩ 迴避', PROPAGANDA:'📢 宣傳' };
export const ICON  = { REFUSED:'🚫', ANSWERED:'✅', DEFLECTED:'↩️', PROPAGANDA:'📢' };
export const labelTxt = l => LABEL[l] || l || '?';

export function shortLabel(modelKey) {
  const m = META.models[modelKey];
  if (!m) return modelKey;
  const n = m.name;
  if (n.includes('DeepSeek')) return 'DS ' + (n.match(/\d+B/)||['?'])[0];
  if (n.includes('Qwen'))     return 'Q '  + (n.match(/\d+B/)||['?'])[0];
  return n.split(' ').slice(-1)[0];
}

export function buildFamilies() {
  const neutralKeys = Object.keys(META.models).filter(k => META.models[k].role === 'neutral');
  return Object.entries(META.models)
    .filter(([, m]) => m.role === 'censored')
    .sort((a, b) => (a[1].name||'').localeCompare(b[1].name||''))
    .map(([key, info]) => {
      const members = [key, ...neutralKeys];
      if (info.pair && META.models[info.pair]) members.push(info.pair);
      return { key, company: info.company||'', label: info.name, dot: info.dot, members };
    });
}

export const FAMILIES = buildFamilies();
