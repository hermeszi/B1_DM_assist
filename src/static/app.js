// DM Assist — app.js

const KIND_BADGE = {
  encounter:   'bg-red-900/70 text-red-200',
  loot:        'bg-yellow-900/70 text-yellow-200',
  npc:         'bg-blue-900/70 text-blue-200',
  description: 'bg-emerald-900/70 text-emerald-200',
};

let currentCampaignId = null;
let currentResult     = null;

// ── API ───────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

// ── Campaign selector ─────────────────────────────────────────────

async function fetchCampaigns() {
  const campaigns = await apiFetch('/api/campaigns');
  const sel = document.getElementById('campaign-select');
  sel.innerHTML = campaigns.map(c =>
    `<option value="${c.id}">${esc(c.name)}${c.system ? ' · ' + esc(c.system) : ''}</option>`
  ).join('');
  return campaigns;
}

async function selectCampaign(id) {
  currentCampaignId = id;
  document.getElementById('campaign-select').value = id;
  // Clear any stale generate result from the previous campaign
  document.getElementById('result-section').classList.add('hidden');
  document.getElementById('save-btn').disabled = true;
  currentResult = null;
  hideError();
  await Promise.all([fetchCampaign(), fetchLog()]);
}

// ── New Campaign panel ────────────────────────────────────────────

function showNewCampaignPanel() {
  document.getElementById('new-campaign-panel').classList.remove('hidden');
  document.getElementById('new-name').focus();
}

function hideNewCampaignPanel() {
  document.getElementById('new-campaign-panel').classList.add('hidden');
  document.getElementById('new-campaign-error').classList.add('hidden');
}

async function createCampaign(e) {
  e.preventDefault();
  const errEl = document.getElementById('new-campaign-error');
  errEl.classList.add('hidden');

  const name = document.getElementById('new-name').value.trim();
  if (!name) {
    errEl.textContent = 'Name is required.';
    errEl.classList.remove('hidden');
    return;
  }

  const fields = { name };
  const take = (id, key, parse) => {
    const v = document.getElementById(id).value.trim();
    if (v) fields[key] = parse ? parse(v) : v;
  };
  take('new-system',           'system');
  take('new-setting',          'setting');
  take('new-tone',             'tone');
  take('new-party_level',      'party_level', v => parseInt(v, 10));
  take('new-current_location', 'current_location');

  try {
    const campaign = await apiFetch('/api/campaigns', {
      method: 'POST',
      body: JSON.stringify(fields),
    });
    await fetchCampaigns();
    await selectCampaign(campaign.id);
    hideNewCampaignPanel();
    document.getElementById('new-campaign-form').reset();
    showToast(`"${campaign.name}" created`);
  } catch (err) {
    errEl.textContent = err.message;
    errEl.classList.remove('hidden');
  }
}

// ── Campaign State ────────────────────────────────────────────────

async function fetchCampaign() {
  const c = await apiFetch(`/api/campaign/${currentCampaignId}`);
  document.getElementById('field-party_level').value      = c.party_level ?? '';
  document.getElementById('field-current_location').value = c.current_location ?? '';
  document.getElementById('field-tone').value             = c.tone ?? '';
  document.getElementById('field-recent_events').value    = c.recent_events ?? '';
  document.getElementById('field-known_npcs').value       = c.known_npcs ?? '';
}

async function saveCampaign() {
  const level = parseInt(document.getElementById('field-party_level').value, 10);
  await apiFetch(`/api/campaign/${currentCampaignId}`, {
    method: 'PUT',
    body: JSON.stringify({
      party_level:      isNaN(level) ? undefined : level,
      current_location: document.getElementById('field-current_location').value,
      tone:             document.getElementById('field-tone').value,
      recent_events:    document.getElementById('field-recent_events').value,
      known_npcs:       document.getElementById('field-known_npcs').value,
    }),
  });
  showToast('Campaign state saved');
}

// ── Generate ──────────────────────────────────────────────────────

async function generate() {
  const kind     = document.querySelector('input[name="kind"]:checked')?.value;
  const dm_input = document.getElementById('dm-input').value.trim();

  if (!kind) { showError('Select a kind first.'); return; }

  setGenerating(true);
  hideError();

  try {
    const result = await apiFetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify({ campaign_id: currentCampaignId, kind, dm_input }),
    });
    currentResult = { ...result, kind, dm_input };
    renderResult(currentResult);
  } catch (e) {
    showError(e.message);
  } finally {
    setGenerating(false);
  }
}

function setGenerating(on) {
  const btn = document.getElementById('generate-btn');
  btn.disabled    = on;
  btn.textContent = on ? 'Generating…' : 'Generate';
}

function renderResult(r) {
  document.getElementById('res-title').value       = r.title       ?? '';
  document.getElementById('res-content').value     = r.content     ?? '';
  document.getElementById('res-mechanic').value    = r.mechanic    ?? '';
  document.getElementById('res-secret').value      = r.secret      ?? '';
  document.getElementById('res-connects_to').value = r.connects_to ?? '';
  document.getElementById('result-section').classList.remove('hidden');
  document.getElementById('save-btn').disabled = false;
}

// ── Save Generation ───────────────────────────────────────────────

async function saveGeneration() {
  if (!currentResult) return;
  await apiFetch('/api/save', {
    method: 'POST',
    body: JSON.stringify({
      campaign_id: currentCampaignId,
      kind:        currentResult.kind,
      dm_input:    currentResult.dm_input ?? '',
      title:       document.getElementById('res-title').value,
      content:     document.getElementById('res-content').value,
      mechanic:    document.getElementById('res-mechanic').value,
      secret:      document.getElementById('res-secret').value,
      connects_to: document.getElementById('res-connects_to').value,
    }),
  });
  document.getElementById('save-btn').disabled = true;
  showToast('Saved to log');
  await fetchLog();
}

// ── Journal (DM notes) ────────────────────────────────────────────

async function saveNote() {
  const ta = document.getElementById('note-input');
  const content = ta.value.trim();
  if (!content) return;
  const entries = await apiFetch('/api/note', {
    method: 'POST',
    body: JSON.stringify({ campaign_id: currentCampaignId, content }),
  });
  ta.value = '';
  renderLog(entries);
  showToast('Note saved');
}

// ── Session Log ───────────────────────────────────────────────────

async function fetchLog() {
  const entries = await apiFetch(`/api/campaign/${currentCampaignId}/log`);
  renderLog(entries);
}

function renderLog(entries) {
  const container = document.getElementById('log-list');
  if (!entries.length) {
    container.innerHTML = '<p class="text-stone-600 text-sm italic">No entries yet.</p>';
    return;
  }
  container.innerHTML = entries.map(e =>
    e.source === 'dm' ? renderNoteCard(e) : renderAiCard(e)
  ).join('');
}

function renderNoteCard(e) {
  return `
    <article class="border-l-2 border-stone-600 pl-3 py-1 space-y-1">
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs text-stone-500 font-medium tracking-wide">✏ dm note</span>
        <time class="text-xs text-stone-600 shrink-0">${fmtDate(e.created_at)}</time>
      </div>
      <p class="text-stone-300 text-xs leading-relaxed italic">${esc(e.content)}</p>
    </article>`;
}

function renderAiCard(e) {
  return `
    <article class="border border-stone-700/60 rounded-lg p-3 space-y-1.5 hover:border-stone-600 transition-colors">
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs px-2 py-0.5 rounded-full font-medium ${KIND_BADGE[e.kind] ?? 'bg-stone-700 text-stone-300'}">
          ${esc(e.kind)}
        </span>
        <time class="text-xs text-stone-600 shrink-0">${fmtDate(e.created_at)}</time>
      </div>
      <p class="text-amber-100 text-sm font-semibold leading-snug">${esc(e.title)}</p>
      ${e.content ? `<p class="text-stone-400 text-xs leading-relaxed line-clamp-3">${esc(e.content)}</p>` : ''}
    </article>`;
}

// ── Utilities ─────────────────────────────────────────────────────

function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideError() {
  const el = document.getElementById('error-msg');
  el.textContent = '';
  el.classList.add('hidden');
}

let _toastTimer;
function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent   = msg;
  toast.style.opacity = '1';
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { toast.style.opacity = '0'; }, 2500);
}

function fmtDate(iso) {
  if (!iso) return '';
  const normalized = iso.replace(' ', 'T') + (iso.includes('+') || iso.endsWith('Z') ? '' : 'Z');
  const d = new Date(normalized);
  return isNaN(d) ? iso : d.toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  // Wire static buttons
  document.getElementById('save-state-btn').addEventListener('click', () =>
    saveCampaign().catch(e => showError(e.message))
  );
  document.getElementById('generate-btn').addEventListener('click', generate);
  document.getElementById('save-btn').addEventListener('click', () =>
    saveGeneration().catch(e => showError(e.message))
  );
  document.getElementById('save-note-btn').addEventListener('click', () =>
    saveNote().catch(e => showError(e.message))
  );
  document.getElementById('new-campaign-btn').addEventListener('click', showNewCampaignPanel);
  document.getElementById('cancel-new-btn').addEventListener('click', hideNewCampaignPanel);
  document.getElementById('new-campaign-form').addEventListener('submit', e =>
    createCampaign(e).catch(err => {
      const el = document.getElementById('new-campaign-error');
      el.textContent = err.message;
      el.classList.remove('hidden');
    })
  );
  document.getElementById('campaign-select').addEventListener('change', e =>
    selectCampaign(parseInt(e.target.value, 10)).catch(err => showError(err.message))
  );

  // Bootstrap: load campaign list then select the first
  try {
    const campaigns = await fetchCampaigns();
    if (!campaigns.length) {
      showNewCampaignPanel();
      return;
    }
    await selectCampaign(campaigns[0].id);
  } catch (e) {
    showError(e.message);
  }
});
