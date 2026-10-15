// Front end: get data and render cards / profile.
// Running under Flask, data comes from the JSON API. On the live demo (GitHub Pages),
// static-api.js provides the same two calls by running the SQL in the browser.
const api = window.staticApi ?? {
  cards: async (q, side = '') => (await fetch(`/api/characters?q=${encodeURIComponent(q)}&side=${side}`)).json(),
  sides: async () => (await fetch('/api/sides')).json(),
  character: async (id) => (await fetch(`/api/characters/${id}`)).json(),
};
const SECTIONS = [['hero', 'Heroes'], ['villain', 'Villains'], ['antihero', 'Antiheroes']];
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const monogram = (name) => name.split(/[\s-]+/).map((w) => w[0]).join('').slice(0, 2).toUpperCase();

const card = (c, tag = 'button') => `
  <${tag} class="card" data-id="${c.id}" style="--accent:${c.color}" aria-label="${esc(c.hero_name)}">
    <span class="monogram">${monogram(c.hero_name)}</span>
    <span class="badge">${c.alignment}</span>
    <span class="name">${esc(c.hero_name)}</span>
    <span class="real">${esc(c.real_name)} · ${c.first_year}</span>
  </${tag}>`;

let all = [];
let side = '';                     // '' = everyone, or 'hero' / 'villain' / 'antihero'

async function loadCards(q = '') {
  let list;
  try {
    list = await api.cards(q, side);
  } catch (err) {
    $('grid').innerHTML = '<p class="meta">Could not load the database. Please refresh the page.</p>';
    throw err;
  }
  if (!q && !side) {
    all = list;
    $('names').innerHTML = all.map((c) => `<option value="${esc(c.hero_name)}">`).join('');
  }
  const grid = (cards) => `<div class="card-grid">${cards.map((c) => card(c)).join('')}</div>`;
  if (!list.length) {
    $('grid').innerHTML = '<p class="meta">No characters match.</p>';
  } else if (side) {
    $('grid').innerHTML = grid(list);
  } else {
    // Everyone: one section per side, each with its own heading
    $('grid').innerHTML = SECTIONS.map(([key, title]) => {
      const cards = list.filter((c) => c.alignment === key);
      return cards.length ? `<section class="side side-${key}" aria-label="${title}"><h2>${title} <span class="count">${cards.length}</span></h2>${grid(cards)}</section>` : '';
    }).join('');
  }
}

async function showTabs() {
  const counts = await api.sides();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  $('tabs').innerHTML = [['', 'All', total], ...SECTIONS.map(([key, title]) => [key, title, counts[key] ?? 0])]
    .map(([key, title, n]) => `<button class="tab tab-${key || 'all'}" data-side="${key}" aria-pressed="${key === side}">${title} <span class="count">${n}</span></button>`).join('');
}

$('tabs').addEventListener('click', (e) => {
  const b = e.target.closest('[data-side]');
  if (!b) return;
  side = b.dataset.side;
  $('tabs').querySelectorAll('[data-side]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  showGrid();
  loadCards($('search').value);
});

async function showCharacter(id) {
  const c = await api.character(id);
  if (!c) return showGrid();
  $('grid').hidden = true;
  $('detail').hidden = false;
  document.documentElement.style.setProperty('--accent', c.color);
  $('featured').innerHTML = `<button class="back" id="back">← All characters</button>` + card(c, 'div');
  $('info').innerHTML = `
    <h2>${esc(c.hero_name)}</h2>
    <p class="meta">${esc(c.real_name)} · First appeared in ${esc(c.first_appearance)} (${c.first_year}) · Created by ${esc(c.creators)}</p>

    <h3>Origin</h3>
    <p>${esc(c.origin)}</p>

    <h3>Powers & abilities</h3>
    <div class="chips">${c.powers.map((p) => `<span class="chip">${esc(p)}</span>`).join('')}</div>

    ${c.teams.length ? `<h3>Teams</h3><div class="chips">${c.teams.map((t) => `<span class="chip">${esc(t)}</span>`).join('')}</div>` : ''}

    <h3>Relationships</h3>
    <div class="rel">${c.relationships.map((r) => `
      <div><span class="kind">${r.kind}</span>${r.id ? `<a href="#${r.id}" data-id="${r.id}">${esc(r.name)}</a>` : esc(r.name)}</div>`).join('')}
    </div>

    <h3>Pop culture highlights</h3>
    <ul class="timeline">${c.appearances.map((a) => `
      <li><strong>${a.year}</strong> · ${esc(a.title)} <span class="meta">(${a.medium})</span>${a.note ? `<br><span class="meta">${esc(a.note)}</span>` : ''}</li>`).join('')}
    </ul>`;
  // restart animations when switching between characters
  ['featured', 'info'].forEach((el) => { $(el).style.animation = 'none'; void $(el).offsetWidth; $(el).style.animation = ''; });
  history.replaceState(null, '', `#${id}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showGrid() {
  $('detail').hidden = true;
  $('grid').hidden = false;
  history.replaceState(null, '', location.pathname);
}

document.addEventListener('click', (e) => {
  if (e.target.closest('#back')) return showGrid();
  const el = e.target.closest('[data-id]');
  if (el && !el.closest('#featured')) { e.preventDefault(); showCharacter(el.dataset.id); }
});

let timer;
$('search').addEventListener('input', (e) => {
  clearTimeout(timer);
  const q = e.target.value;
  const exact = all.find((c) => c.hero_name.toLowerCase() === q.trim().toLowerCase());
  if (exact) return showCharacter(exact.id);           // picked from the suggestions
  timer = setTimeout(() => { showGrid(); loadCards(q); }, 200);
});

showTabs();
loadCards().then(() => { const id = location.hash.slice(1); if (id) showCharacter(id); });
