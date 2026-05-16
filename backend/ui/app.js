const API_BASE = '/api/v1';
const AGENTS = ['researcher', 'developer', 'designer', 'marketer', 'finance', 'support'];

function getToken() {
  let t = localStorage.getItem('ab_token');
  if (!t) {
    t = prompt('Masukkan API Key (ab_...):');
    if (t) localStorage.setItem('ab_token', t);
  }
  return t;
}

async function api(path, opts = {}) {
  const token = getToken();
  if (!token) return null;
  const headers = { 'Authorization': 'Bearer ' + token, ...opts.headers };
  if (opts.body && typeof opts.body === 'object') {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const res = await fetch(API_BASE + path, { ...opts, headers });
  if (res.status === 401) { localStorage.removeItem('ab_token'); return null; }
  return res.json();
}

async function loadStats() {
  try {
    const [agents, businesses, settings] = await Promise.all([
      api('/agents'),
      api('/businesses/'),
      api('/settings/status'),
    ]);
    if (!agents) return;
    updateModel(agents.model, settings);
    updateStatCards(agents, businesses);
    updateAgentCards(agents);
    updateActivity(settings);
  } catch (e) {
    console.error('Poll failed:', e);
  }
}

function updateModel(model, settings) {
  const badge = document.getElementById('model-badge');
  if (!badge) return;
  const tier = model ? model.tier : '?';
  const name = model ? model.name : '—';
  badge.textContent = name + ' (' + tier + ')';

  const ar = settings && settings.agent_recommendations;
  if (ar) {
    const warnEl = document.getElementById('stat-warn');
    if (warnEl) {
      const num = warnEl.querySelector('.stat-num');
      if (num) num.textContent = ar.warning_count || 0;
    }
  }
}

function updateStatCards(agents, businesses) {
  const biz = Array.isArray(businesses) ? businesses : [];
  document.getElementById('stat-biz').textContent = biz.length;
  document.getElementById('stat-active').textContent = biz.filter(b => b.status === 'operating').length;

  const pending = agents && agents.agents ? agents.agents.filter(a => a.status === 'suboptimal').length : 0;
  document.getElementById('stat-pending').textContent = pending;
}

function updateAgentCards(agents) {
  if (!agents || !agents.agents) return;
  for (const a of agents.agents) {
    const dot = document.getElementById('dot-' + a.name);
    const task = document.getElementById('task-' + a.name);
    const tier = document.getElementById('tier-' + a.name);
    const card = document.querySelector(`.agent-card[data-agent="${a.name}"]`);
    if (!dot) continue;

    if (a.status === 'optimal') {
      dot.className = 'dot working';
      if (task) task.textContent = a.model_override ? 'overridden' : 'optimal';
    } else if (a.status === 'suboptimal') {
      dot.className = 'dot done';
      if (task) task.textContent = 'suboptimal';
      if (card) card.classList.add('warn-card');
    } else {
      dot.className = 'dot idle';
      if (task) task.textContent = '—';
    }
    if (tier) tier.textContent = 'cur: ' + a.current_tier + ' | min: ' + a.min_tier;
  }
}

let activityCache = [];
function updateActivity(settings) {
  const log = document.getElementById('activity-log');
  if (!log) return;

  const ar = settings && settings.agent_recommendations;
  if (!ar) return;

  const now = new Date();
  const time = now.toTimeString().slice(0, 8);

  let entries = [];
  for (const w of (ar.agents_suboptimal || [])) {
    entries.push({ time, text: '⚠ ' + w.label + ': ' + (w.warning || 'suboptimal').slice(0, 60) });
  }
  const agentNames = ['Market Researcher', 'Software Engineer', 'Brand Designer', 'Marketing', 'Finance', 'Support'];
  const activities = ['Menganalisis data...', 'Menulis kode...', 'Mendesain UI...', 'Menyusun campaign...', 'Menghitung proyeksi...', 'Memproses tiket...'];
  const r = Math.floor(Math.random() * agentNames.length);
  entries.push({ time, text: agentNames[r] + ': ' + activities[r] });

  activityCache = [...entries.slice(-10), ...activityCache].slice(0, 20);

  log.innerHTML = activityCache.map(e =>
    '<div class="log-entry">[' + e.time + ']  ' + escapeHtml(e.text) + '</div>'
  ).join('');
  log.scrollTop = log.scrollHeight;
}

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function openDetail(name) {
  window.location.href = '/ui/agents/' + name;
}

async function loadDetail(name) {
  const agents = await api('/agents/' + name);
  if (!agents) return;

  document.getElementById('detail-name').textContent = agents.label;
  document.getElementById('detail-desc').textContent = agents.description;
  document.getElementById('detail-min-tier').textContent = agents.min_tier;
  document.getElementById('detail-cur-tier').textContent = agents.current_tier;
  document.getElementById('detail-warning').textContent = agents.warning || '—';

  const statusEl = document.getElementById('detail-status');
  statusEl.textContent = agents.status;
  statusEl.className = 'detail-status-badge ' + agents.status;

  const emojiMap = { researcher: '📊', developer: '💻', designer: '🎨', marketer: '📣', finance: '💰', support: '🎧' };
  document.getElementById('detail-emoji').textContent = emojiMap[name] || '🤖';

  document.getElementById('chk-enabled').checked = agents.enabled;
  document.getElementById('input-model').value = agents.model_override || '';
  document.getElementById('input-temp').value = agents.temperature;

  document.getElementById('page-title').textContent = '⚙️ ' + agents.label;
}

async function saveConfig() {
  const name = document.getElementById('detail-name').textContent.toLowerCase().replace(/\s+/g, '');
  const agentName = AGENTS.find(a => name.includes(a)) || document.querySelector('.back-link').getAttribute('href').split('/').pop();
  const path = window.location.pathname;
  const aname = path.split('/').pop();

  const data = {
    enabled: document.getElementById('chk-enabled').checked,
    model_override: document.getElementById('input-model').value || null,
    temperature: parseFloat(document.getElementById('input-temp').value) || 0.7,
  };

  const result = await api('/agents/' + aname + '/config', { method: 'PUT', body: data });
  const toast = document.getElementById('toast');
  if (result && result.name) {
    toast.textContent = '✅ Disimpan!';
    toast.className = 'toast show success';
    if (result.current_tier) document.getElementById('detail-cur-tier').textContent = result.current_tier;
    if (result.status) {
      const se = document.getElementById('detail-status');
      se.textContent = result.status;
      se.className = 'detail-status-badge ' + result.status;
    }
  } else {
    toast.textContent = '❌ Gagal menyimpan';
    toast.className = 'toast show error';
  }
  setTimeout(() => { toast.className = 'toast'; }, 2000);
}

function switchTab(tab) {
  if (tab === 'dashboard') { window.location.href = '/ui/dashboard'; }
  if (tab === 'detail') { window.location.href = '/ui/agents/researcher'; }
  if (tab === 'agents') { window.location.href = '/ui/agents/researcher'; }
}
document.addEventListener('keydown', e => {
  if (e.key === 'q' || e.key === 'Q') window.close();
  if (e.key === '1') window.location.href = '/ui/dashboard';
  if (e.key === '2') window.location.href = '/ui/agents/researcher';
  if (e.key === '3') window.location.href = '/ui/agents/researcher';
});

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('office-grid')) {
    loadStats();
    setInterval(loadStats, 3000);
  }
});
