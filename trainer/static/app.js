// Taiwanese Poker Trainer — single-page UI.
//
// Model:
//   placement: Map<slot-id, card-string | null>
//     slot-ids: hand-0..hand-6, top-0, mid-0, mid-1, bot-0..bot-3
//   dealtHand: string[] (the 7 cards currently in play; frozen until next deal)

const HAND_SLOT_IDS = ['hand-0','hand-1','hand-2','hand-3','hand-4','hand-5','hand-6'];
const TIER_SLOT_IDS = ['top-0','mid-0','mid-1','bot-0','bot-1','bot-2','bot-3'];
const ALL_SLOT_IDS = [...HAND_SLOT_IDS, ...TIER_SLOT_IDS];

const state = {
  dealtHand: [],
  placement: new Map(),  // slot-id -> card-string | null
  profileId: null,       // currently selected training profile
  profiles: [],          // {id, label} list from /api/profiles
};

// ---- Helpers ----

const SUIT_CHARS = { c: '♣', d: '♦', h: '♥', s: '♠' };

function cardIsRed(card) {
  return card[1] === 'h' || card[1] === 'd';
}

function renderCard(card, draggable = true) {
  const el = document.createElement('div');
  el.className = 'card' + (cardIsRed(card) ? ' red' : '');
  el.dataset.card = card;
  el.draggable = draggable;
  el.innerHTML = `<span class="rank">${card[0]}</span><span class="suit">${SUIT_CHARS[card[1]]}</span>`;

  el.addEventListener('dragstart', (ev) => {
    el.classList.add('dragging');
    ev.dataTransfer.setData('text/plain', card);
    ev.dataTransfer.effectAllowed = 'move';
  });
  el.addEventListener('dragend', () => el.classList.remove('dragging'));
  el.addEventListener('click', () => onCardClick(card));
  return el;
}

function findSlotOf(card) {
  for (const [sid, c] of state.placement.entries()) {
    if (c === card) return sid;
  }
  return null;
}

function firstEmptyHandSlot() {
  return HAND_SLOT_IDS.find(sid => state.placement.get(sid) === null) || null;
}

function firstEmptyTierSlot() {
  return TIER_SLOT_IDS.find(sid => state.placement.get(sid) === null) || null;
}

function moveCard(card, toSlotId) {
  const fromSlotId = findSlotOf(card);
  if (fromSlotId === toSlotId) return;
  const existing = state.placement.get(toSlotId);

  // Swap if the destination is already occupied, otherwise empty the source.
  if (existing && fromSlotId) {
    state.placement.set(fromSlotId, existing);
  } else if (fromSlotId) {
    state.placement.set(fromSlotId, null);
  }
  state.placement.set(toSlotId, card);
  render();
}

function clearTier(tier) {
  // tier in {'top', 'mid', 'bot'}. Move each card in that tier back to the
  // first empty hand slot.
  const affected = TIER_SLOT_IDS.filter(sid => sid.startsWith(tier));
  for (const sid of affected) {
    const c = state.placement.get(sid);
    if (c) {
      const dest = firstEmptyHandSlot();
      if (dest) state.placement.set(dest, c);
      state.placement.set(sid, null);
    }
  }
  render();
}

function clearAllTiers() {
  clearTier('top'); clearTier('mid'); clearTier('bot');
  hideResult();
}

// ---- Event handlers ----

function onCardClick(card) {
  // Click-to-fill: if the card is in the hand row, move it to the first
  // empty tier slot. If it's in a tier, move it back to the hand.
  const from = findSlotOf(card);
  if (!from) return;
  if (from.startsWith('hand-')) {
    const dest = firstEmptyTierSlot();
    if (dest) moveCard(card, dest);
  } else {
    const dest = firstEmptyHandSlot();
    if (dest) moveCard(card, dest);
  }
}

function wireDropTargets() {
  document.querySelectorAll('.slot').forEach(slotEl => {
    slotEl.addEventListener('dragover', (ev) => {
      ev.preventDefault();
      ev.dataTransfer.dropEffect = 'move';
      slotEl.classList.add('drop-hover');
    });
    slotEl.addEventListener('dragleave', () => slotEl.classList.remove('drop-hover'));
    slotEl.addEventListener('drop', (ev) => {
      ev.preventDefault();
      slotEl.classList.remove('drop-hover');
      const card = ev.dataTransfer.getData('text/plain');
      if (!card) return;
      moveCard(card, slotEl.dataset.slotId);
    });
  });
}

// ---- Rendering ----

function render() {
  ALL_SLOT_IDS.forEach(sid => {
    const slotEl = document.querySelector(`[data-slot-id="${sid}"]`);
    slotEl.innerHTML = '';
    const card = state.placement.get(sid);
    if (card) {
      slotEl.classList.add('filled');
      slotEl.appendChild(renderCard(card));
    } else {
      slotEl.classList.remove('filled');
    }
  });
  updateSubmitButton();
}

function updateSubmitButton() {
  const ok = TIER_SLOT_IDS.every(sid => state.placement.get(sid) !== null);
  document.getElementById('submit-btn').disabled = !ok;
  document.getElementById('compare-btn').disabled = !ok;
}

function hideResult() {
  document.getElementById('result').hidden = true;
  document.getElementById('compare-result').hidden = true;
}

function renderCardInline(card) {
  const cls = cardIsRed(card) ? 'red' : '';
  return `<span class="inline-card ${cls}" style="font-family: monospace;">${card[0]}${SUIT_CHARS[card[1]]}</span>`;
}

function setHeadline(isMatch, severity) {
  const h = document.getElementById('result-headline');
  h.classList.remove('good', 'warn', 'bad');
  if (isMatch) {
    h.textContent = '✓ Perfect — you matched the solver.';
    h.classList.add('good');
  } else if (severity === 'trivial') {
    h.textContent = '≈ Essentially tied with the solver.';
    h.classList.add('good');
  } else if (severity === 'minor') {
    h.textContent = 'Close — small EV miss.';
    h.classList.add('warn');
  } else if (severity === 'moderate') {
    h.textContent = 'Off — meaningful EV miss.';
    h.classList.add('warn');
  } else {
    h.textContent = 'Major miss — this hand has a much better setting.';
    h.classList.add('bad');
  }
}

function showResult(r) {
  document.getElementById('user-ev').textContent = (r.user.ev >= 0 ? '+' : '') + r.user.ev.toFixed(3);
  document.getElementById('best-ev').textContent = (r.best.ev >= 0 ? '+' : '') + r.best.ev.toFixed(3);
  document.getElementById('delta-ev').textContent = r.delta.toFixed(3);

  setHeadline(r.is_match, r.severity);
  document.getElementById('result-summary').textContent = r.summary;

  const cards = r.best.cards;
  document.getElementById('best-top').innerHTML = renderCardInline(cards[0]);
  document.getElementById('best-mid').innerHTML = cards.slice(1, 3).map(renderCardInline).join(' ');
  document.getElementById('best-bot').innerHTML = cards.slice(3, 7).map(renderCardInline).join(' ');

  const list = document.getElementById('findings-list');
  list.innerHTML = '';
  for (const f of r.findings) {
    const li = document.createElement('li');
    li.innerHTML = `<div class="finding-title">${f.title}</div><div class="finding-detail">${f.detail}</div>`;
    list.appendChild(li);
  }

  document.getElementById('result').hidden = false;
}

// ---- Network ----

async function loadProfiles() {
  const res = await fetch('/api/profiles');
  const data = await res.json();
  state.profiles = data.profiles;
  state.profileId = data.default;
  const sel = document.getElementById('profile-select');
  sel.innerHTML = '';
  for (const p of data.profiles) {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.label;
    if (p.id === data.default) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.addEventListener('change', () => {
    state.profileId = sel.value;
    hideResult();
  });
}

async function deal() {
  const res = await fetch('/api/deal');
  const data = await res.json();
  state.dealtHand = data.hand;
  state.placement.clear();
  HAND_SLOT_IDS.forEach((sid, i) => state.placement.set(sid, data.hand[i]));
  TIER_SLOT_IDS.forEach(sid => state.placement.set(sid, null));
  hideResult();
  setStatus('');
  render();
}

function setStatus(msg) {
  document.getElementById('status-line').textContent = msg;
}

async function submit() {
  const setting = TIER_SLOT_IDS.map(sid => state.placement.get(sid));
  setStatus('Scoring against selected profile… (~1s)');
  document.getElementById('submit-btn').disabled = true;
  document.getElementById('compare-btn').disabled = true;
  try {
    const res = await fetch('/api/score', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        hand: state.dealtHand,
        setting,
        profile_id: state.profileId,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus('Error: ' + (data.error || res.statusText));
      return;
    }
    showResult(data);
    setStatus(`Scored vs ${data.profile.label} (${data.samples} MC samples).`);
  } catch (e) {
    setStatus('Network error: ' + e);
  } finally {
    updateSubmitButton();
  }
}

async function compareAllProfiles() {
  const setting = TIER_SLOT_IDS.map(sid => state.placement.get(sid));
  setStatus('Scoring across all 4 profiles… (takes a few seconds)');
  document.getElementById('submit-btn').disabled = true;
  document.getElementById('compare-btn').disabled = true;
  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({hand: state.dealtHand, setting}),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus('Error: ' + (data.error || res.statusText));
      return;
    }
    showCompareResult(data);
    setStatus(`Compared across ${data.per_profile.length} profiles (${data.samples} MC samples each).`);
  } catch (e) {
    setStatus('Network error: ' + e);
  } finally {
    updateSubmitButton();
  }
}

function severityClassForDelta(delta) {
  const d = Math.abs(delta);
  if (d < 0.10) return 'delta-trivial';
  if (d < 0.50) return 'delta-minor';
  if (d < 2.00) return 'delta-moderate';
  return 'delta-major';
}

function renderMiniCard(card, big = false) {
  const cls = 'mini-card' + (big ? ' big' : '') + (cardIsRed(card) ? ' red' : '');
  return `<span class="${cls}"><span class="rank">${card[0]}</span><span class="suit">${SUIT_CHARS[card[1]]}</span></span>`;
}

function renderMiniArrangement(cards, big = false) {
  const cls = big ? 'big' : '';
  return `
    <div class="mini-tiers">
      <div class="mini-tier"><span class="tier-tag">top</span>${renderMiniCard(cards[0], big)}</div>
      <div class="mini-tier"><span class="tier-tag">mid</span>${cards.slice(1, 3).map(c => renderMiniCard(c, big)).join('')}</div>
      <div class="mini-tier"><span class="tier-tag">bot</span>${cards.slice(3, 7).map(c => renderMiniCard(c, big)).join('')}</div>
    </div>
  `;
}

function arrangementsIdentical(rows) {
  // Compare tier composition as sets, not raw card order.
  const key = (cards) => {
    const top = cards[0];
    const mid = [...cards.slice(1, 3)].sort().join(',');
    const bot = [...cards.slice(3, 7)].sort().join(',');
    return `${top}|${mid}|${bot}`;
  };
  const first = key(rows[0].best.cards);
  return rows.every(r => key(r.best.cards) === first);
}

function showCompareResult(r) {
  const tbody = document.querySelector('#compare-table tbody');
  tbody.innerHTML = '';
  for (const row of r.per_profile) {
    const tr = document.createElement('tr');
    if (row.is_match) tr.classList.add('match-row');
    const deltaCls = severityClassForDelta(row.delta);
    const fmtEv = (ev) => (ev >= 0 ? '+' : '') + ev.toFixed(3);
    tr.innerHTML = `
      <td>${row.profile.label}</td>
      <td class="num">${fmtEv(row.user.ev)}</td>
      <td class="num">${fmtEv(row.best.ev)}</td>
      <td class="num ${deltaCls}">${row.delta.toFixed(3)}</td>
      <td>${row.is_match ? '✓' : '—'}</td>
    `;
    tbody.appendChild(tr);
  }

  // Per-profile best arrangements panel.
  const arrEl = document.getElementById('compare-arrangements');
  const allAgree = arrangementsIdentical(r.per_profile);
  if (allAgree) {
    const cards = r.per_profile[0].best.cards;
    arrEl.innerHTML = `
      <h3>Per-profile optimal arrangement</h3>
      <div class="agreement-banner">All 4 profiles agree on the best arrangement for this hand — this is a robust (GTO-approximating) setting.</div>
      <div class="arrangement-card big">
        <div class="ac-label">Best arrangement (agreed by all profiles)</div>
        ${renderMiniArrangement(cards, true)}
      </div>
    `;
  } else {
    const parts = ['<h3>Per-profile optimal arrangements</h3>'];
    parts.push('<div class="disagreement-note">Profiles disagree — the best arrangement depends on which opponent type you\'re facing.</div>');
    for (const row of r.per_profile) {
      parts.push(`
        <div class="arrangement-card">
          <div class="ac-label">vs ${row.profile.label} — best EV ${row.best.ev >= 0 ? '+' : ''}${row.best.ev.toFixed(3)}</div>
          ${renderMiniArrangement(row.best.cards, false)}
        </div>
      `);
    }
    arrEl.innerHTML = parts.join('');
  }

  const rob = r.robustness;
  const robEl = document.getElementById('compare-robustness');
  let robustnessVerdict;
  if (rob.matches === r.per_profile.length) {
    robustnessVerdict = '<b>Your setting matches the best response against every profile</b> — this is as close to GTO as we can measure with this set of opponents. ';
  } else if (rob.worst_delta < 0.10) {
    robustnessVerdict = '<b>Robust choice.</b> Your setting is within 0.10 EV of the best-response for every profile — exploitable by no one meaningfully. ';
  } else if (rob.worst_delta < 0.50) {
    robustnessVerdict = '<b>Nearly robust.</b> Small miss against one or more profiles. ';
  } else {
    robustnessVerdict = `<b>Exploitable by "${rob.worst_label}"</b> — this profile can extract ${rob.worst_delta.toFixed(2)} more EV against your setting. `;
  }
  robEl.innerHTML =
    robustnessVerdict +
    `Worst-case delta: <b>${rob.worst_delta.toFixed(3)}</b>. ` +
    `Mean delta across profiles: <b>${rob.mean_delta.toFixed(3)}</b>. ` +
    `Exact matches: <b>${rob.matches} / ${r.per_profile.length}</b>.`;

  document.getElementById('result').hidden = true;  // hide single-profile result
  document.getElementById('compare-result').hidden = false;
}

// ---- Init ----

async function init() {
  wireDropTargets();
  document.getElementById('deal-btn').addEventListener('click', deal);
  document.getElementById('submit-btn').addEventListener('click', submit);
  document.getElementById('compare-btn').addEventListener('click', compareAllProfiles);
  document.getElementById('clear-all-btn').addEventListener('click', clearAllTiers);
  document.querySelectorAll('.clear-tier').forEach(btn => {
    btn.addEventListener('click', () => {
      clearTier(btn.dataset.tier);
      hideResult();
    });
  });
  await loadProfiles();
  await deal();
}

document.addEventListener('DOMContentLoaded', init);
