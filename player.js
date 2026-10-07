// Player ID + save data, stored in this browser.
// Any game page can include <script src="player.js"></script> and use:
//   Player.id                 -> "CC-7F3K-92QD"
//   Player.name / setName(n)
//   Player.save(game, data)   -> stores an object for that game
//   Player.load(game)         -> returns that object (or {})
//   Player.submitScore(game, score) -> returns true if it's a new best
//   Player.exportCode() / importCode(code) -> move saves between devices
(function () {
  const KEY = "cc-player";
  const CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";

  function randomId() {
    const bytes = new Uint8Array(8);
    crypto.getRandomValues(bytes);
    const s = Array.from(bytes, b => CHARS[b % CHARS.length]).join("");
    return `CC-${s.slice(0, 4)}-${s.slice(4)}`;
  }

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch { return null; }
  }
  function write(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch { /* storage blocked */ }
  }

  let state = read();
  if (!state || !state.id) {
    state = { id: randomId(), name: "", created: Date.now(), games: {} };
    write(state);
  }

  window.Player = {
    get id() { return state.id; },
    get name() { return state.name || "Player"; },
    setName(name) { state.name = String(name).slice(0, 20); write(state); },
    load(game) { return { ...(state.games[game] || {}) }; },
    save(game, data) { state.games[game] = { ...(state.games[game] || {}), ...data }; write(state); },
    submitScore(game, score) {
      const g = this.load(game);
      const isBest = score > (g.best || 0);
      this.save(game, { best: Math.max(score, g.best || 0), plays: (g.plays || 0) + 1, last: score });
      return isBest;
    },
    allGames() { return { ...state.games }; },
    exportCode() { return btoa(unescape(encodeURIComponent(JSON.stringify(state)))); },
    importCode(code) {
      const next = JSON.parse(decodeURIComponent(escape(atob(code.trim()))));
      if (!next || typeof next.id !== "string" || typeof next.games !== "object") throw new Error("Invalid save code");
      state = next; write(state);
    },
    reset() { state = { id: randomId(), name: "", created: Date.now(), games: {} }; write(state); },
  };
})();
