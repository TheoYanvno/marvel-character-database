// Data layer for the live demo on GitHub Pages, which can't run the Flask server.
// It downloads the SQLite database built by build_site.py and runs the SAME named
// queries from sql/app_queries.sql in the browser, using SQLite compiled to
// WebAssembly (sql.js). It provides the same two calls as the Flask JSON API.
const SQLJS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/';

// Same format the Python side reads: a "-- name: x" line starts each query.
function loadQueries(text) {
  const queries = {};
  let name = null;
  for (const line of text.split('\n')) {
    const match = line.match(/^--\s*name:\s*(\w+)/);
    if (match) { name = match[1]; queries[name] = ''; }
    else if (name && !line.trimStart().startsWith('--')) queries[name] += line + '\n';
  }
  for (const k in queries) queries[k] = queries[k].trim();
  return queries;
}

const ready = (async () => {
  const [SQL, file, sql] = await Promise.all([
    initSqlJs({ locateFile: (f) => SQLJS_CDN + f }),
    fetch('marvel.db').then((r) => r.arrayBuffer()),
    fetch('app_queries.sql').then((r) => r.text()),
  ]);
  return { db: new SQL.Database(new Uint8Array(file)), Q: loadQueries(sql) };
})();

// Run a parameterized query and return the rows as plain objects.
function rows(db, sql, params = []) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  const out = [];
  while (stmt.step()) out.push(stmt.getAsObject());
  stmt.free();
  return out;
}

window.staticApi = {
  async cards(q = '', side = '') {
    const { db, Q } = await ready;
    const like = `%${q.trim()}%`;
    side = ['hero', 'villain', 'antihero'].includes(side) ? side : '';
    const prefix = `${q.trim()}%`;
    return rows(db, Q.search, [like, like, like, side, side, prefix, like, like]);
  },
  async sides() {
    const { db, Q } = await ready;
    return Object.fromEntries(rows(db, Q.side_counts).map((r) => [r.alignment, r.total]));
  },
  async character(id) {
    const { db, Q } = await ready;
    id = Number(id);
    const [c] = rows(db, Q.character, [id]);
    if (!c) return null;
    return {
      ...c,
      powers: rows(db, Q.character_powers, [id]).map((r) => r.name),
      teams: rows(db, Q.character_teams, [id]).map((r) => r.name),
      relationships: rows(db, Q.character_relationships, [id]),
      appearances: rows(db, Q.character_appearances, [id]),
    };
  },
};
