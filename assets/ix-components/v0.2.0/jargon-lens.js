/*! IX Jargon Lens v0.2.0 — curated, source-anchored glossary popovers for IX Learning Studio.
 *  Original code written for IX Learning Studio (no third-party code). Runs fully client-side:
 *  no network requests, no storage, no text leaves the page.
 *  Matching rules (deliberate, documented):
 *   - English terms: case-insensitive, must not be glued to another Latin letter/digit
 *     (manual boundary check; no regex lookbehind so older iPad Safari still parses the file).
 *   - Thai terms: exact listed phrases only. Thai has no spaces, so no word segmentation is
 *     attempted; only multi-syllable phrases are listed to avoid matching inside other words.
 *   - The original text is never replaced: the matched characters are wrapped, byte-for-byte.
 *   - First occurrence per section only, to limit visual noise.
 *   - Assessment zones are excluded by the host page (exclude option) so the lens never
 *     reveals answers.
 */
(function () {
  'use strict';
  var VERSION = '0.2.0';
  var BASE_EXCLUDE = 'script,style,svg,textarea,input,select,option,button,label,summary,a,h1,nav,output,code,pre,.eq,.metric,.note,.fb,.hint,[aria-live],[data-ix-no-jargon],.ix-jl-ui';
  var LATIN = /[A-Za-z0-9]/;
  function provLine(t) {
    var pv = t.provenance || {}, rv = t.review || {};
    var a = (pv.added || []).length, b = (pv.from_slides || []).length;
    var approval = document.querySelector('meta[name="ix-glossary-owner-approved-sha256"]');
    var signed = approval && approval.content === '01a1e3052a8f03f31cf5796264bf548b7aec7d88d207ec506d2b63c3befde0da';
    return (b || a ? ('จากสไลด์ ' + b + ' ข้อ · ส่วนเสริมนอกสไลด์ ' + a + ' ข้อ · ') : '') + 'สถานะตรวจ: ' + ((rv.owner === 'APPROVED' || signed) ? 'เจ้าของรับรองแล้ว' : 'ยังรอเจ้าของตรวจ');
  }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  function init(opts) {
    if (!opts || !opts.glossary || !opts.glossary.terms) throw new Error('IXJargonLens: glossary missing');
    var root = opts.root || document.querySelector('main') || document.body;
    var exclude = opts.exclude ? BASE_EXCLUDE + ',' + opts.exclude : BASE_EXCLUDE;
    var scopeSel = opts.scopeSelector || 'section';
    var terms = opts.glossary.terms, byId = {};
    terms.forEach(function (t) { byId[t.id] = t; });
    var level = 'beginner', lastTrigger = null;

    /* ---------- 1. find and wrap first occurrence per section ---------- */
    var pats = [];
    terms.forEach(function (t) {
      (t.match_en || []).forEach(function (s) { pats.push({ t: t, s: s.toLowerCase(), latin: true }); });
      (t.match_th || []).forEach(function (s) { if (s) pats.push({ t: t, s: s, latin: false }); });
    });
    pats.sort(function (a, b) { return b.s.length - a.s.length; });
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var p = n.parentElement;
        return (!p || p.closest(exclude)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    var shown = [], folded = [];   /* visible text first, so the highlighted first occurrence is one the learner can see */
    while (walker.nextNode()) { var nd = walker.currentNode, dt = nd.parentElement.closest('details'); (dt && !dt.open ? folded : shown).push(nd); }
    var nodes = shown.concat(folded);
    var usedByScope = (typeof WeakMap !== 'undefined') ? new WeakMap() : null, fallbackUsed = {};
    var counts = {}, wrapped = 0;
    nodes.forEach(function (node) {
      var scope = node.parentElement.closest(scopeSel) || root;
      var used = usedByScope ? (usedByScope.get(scope) || {}) : fallbackUsed;
      if (usedByScope && !usedByScope.has(scope)) usedByScope.set(scope, used);
      var text = node.nodeValue, low = text.toLowerCase(), hits = [];
      pats.forEach(function (p) {
        if (used[p.t.id]) return;
        var hay = p.latin ? low : text, from = 0, i;
        while ((i = hay.indexOf(p.s, from)) !== -1) {
          var end = i + p.s.length;
          var okBoundary = !p.latin || (!LATIN.test(text.charAt(i - 1)) && !LATIN.test(text.charAt(end)));
          var overlaps = hits.some(function (h) { return i < h.end && end > h.start; });
          if (okBoundary && !overlaps) { hits.push({ start: i, end: end, t: p.t }); used[p.t.id] = true; break; }
          from = i + 1;
        }
      });
      if (!hits.length) return;
      hits.sort(function (a, b) { return a.start - b.start; });
      var frag = document.createDocumentFragment(), pos = 0;
      hits.forEach(function (h) {
        if (h.start > pos) frag.appendChild(document.createTextNode(text.slice(pos, h.start)));
        var b = el('button', 'ix-term', text.slice(h.start, h.end));
        b.type = 'button'; b.setAttribute('data-ix-term', h.t.id);
        b.setAttribute('aria-haspopup', 'dialog'); b.setAttribute('aria-expanded', 'false');
        frag.appendChild(b); pos = h.end; wrapped++; counts[h.t.id] = (counts[h.t.id] || 0) + 1;
      });
      if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
      node.parentNode.replaceChild(frag, node);
    });

    /* ---------- 2. shared popover ---------- */
    var pop = el('div', 'ix-jl-ui ix-jl-pop');
    pop.id = 'ix-jl-pop'; pop.hidden = true; pop.tabIndex = -1;
    pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-modal', 'false'); pop.setAttribute('aria-labelledby', 'ix-jl-title');
    pop.innerHTML =
      '<div class="ix-jl-head"><div><div class="ix-jl-kicker">คำศัพท์เทคนิค</div><strong id="ix-jl-title"></strong><div class="ix-jl-th"></div></div>' +
      '<button type="button" class="ix-jl-x" aria-label="ปิดคำอธิบาย">×</button></div>' +
      '<div class="ix-jl-lvl" role="radiogroup" aria-label="ระดับคำอธิบาย">' +
      '<label><input type="radio" name="ix-jl-lvl" value="beginner" checked> เริ่มต้น</label>' +
      '<label><input type="radio" name="ix-jl-lvl" value="advanced"> ขั้นสูง</label></div>' +
      '<p class="ix-jl-body"></p><div class="ix-jl-eq"></div><div class="ix-jl-links"></div><div class="ix-jl-src"></div><div class="ix-jl-prov"></div>';
    document.body.appendChild(pop);
    function q(sel) { return pop.querySelector(sel); }
    function fill(t) {
      q('#ix-jl-title').textContent = t.en; q('.ix-jl-th').textContent = t.th;
      q('.ix-jl-body').textContent = t[level];
      q('.ix-jl-eq').textContent = t.equation || ''; q('.ix-jl-eq').hidden = !t.equation;
      var links = q('.ix-jl-links'); links.textContent = '';
      (t.links || []).forEach(function (l) { var a = el('a', 'ix-jl-link', l.label + ' →'); a.href = l.href; a.addEventListener('click', close); links.appendChild(a); });
      q('.ix-jl-src').textContent = 'แหล่ง: ' + (t.sources || []).join(' · ');
      q('.ix-jl-prov').textContent = provLine(t);
      pop.setAttribute('data-term', t.id);
    }
    function place(trigger) {
      var vw = document.documentElement.clientWidth;
      if (vw < 720) { pop.classList.add('ix-jl-sheet'); pop.style.left = ''; pop.style.top = ''; return; }
      pop.classList.remove('ix-jl-sheet');
      var r = trigger.getBoundingClientRect(), w = Math.min(380, vw - 24);
      pop.style.width = w + 'px';
      var left = Math.max(12, Math.min(r.left + window.pageXOffset, window.pageXOffset + vw - w - 12));
      pop.style.left = left + 'px'; pop.style.top = (r.bottom + window.pageYOffset + 8) + 'px';
    }
    function open(trigger) {
      var t = byId[trigger.getAttribute('data-ix-term')]; if (!t) return;
      if (lastTrigger && lastTrigger !== trigger) lastTrigger.setAttribute('aria-expanded', 'false');
      lastTrigger = trigger; fill(t); pop.hidden = false; place(trigger);
      trigger.setAttribute('aria-expanded', 'true'); pop.focus({ preventScroll: true });
    }
    function close() {
      if (pop.hidden) return; pop.hidden = true;
      if (lastTrigger) { lastTrigger.setAttribute('aria-expanded', 'false'); if (document.body.contains(lastTrigger)) lastTrigger.focus({ preventScroll: true }); }
    }
    q('.ix-jl-x').addEventListener('click', close);
    pop.addEventListener('change', function (e) {
      if (e.target.name === 'ix-jl-lvl') { level = e.target.value; var t = byId[pop.getAttribute('data-term')]; if (t) q('.ix-jl-body').textContent = t[level]; syncDrawerLevel(); }
    });
    document.addEventListener('click', function (e) {
      var trig = e.target.closest && e.target.closest('.ix-term');
      if (trig && !document.documentElement.classList.contains('ix-jl-off')) { e.preventDefault(); if (!pop.hidden && lastTrigger === trig) close(); else open(trig); return; }
      if (!pop.hidden && !pop.contains(e.target)) close();
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { if (!pop.hidden) close(); else if (!drawer.hidden) toggleDrawer(false); } });
    window.addEventListener('resize', function () { if (!pop.hidden && lastTrigger) place(lastTrigger); });

    /* ---------- 3. glossary drawer with search ---------- */
    var fab = document.querySelector('[data-ix-glossary-open]'), floating = !fab;
    if (floating) { fab = el('button', 'ix-jl-ui ix-jl-fab', 'คำศัพท์ (' + terms.length + ')'); fab.type = 'button'; }
    else { fab.textContent = 'คำศัพท์ (' + terms.length + ')'; fab.classList.add('ix-jl-ui'); } fab.setAttribute('aria-expanded', 'false'); fab.setAttribute('aria-controls', 'ix-jl-drawer');
    var drawer = el('aside', 'ix-jl-ui ix-jl-drawer'); drawer.id = 'ix-jl-drawer'; drawer.hidden = true;
    drawer.setAttribute('role', 'dialog'); drawer.setAttribute('aria-label', 'อภิธานศัพท์ของบทเรียน');
    drawer.innerHTML =
      '<div class="ix-jl-head"><strong>อภิธานศัพท์ · Jargon Lens</strong><button type="button" class="ix-jl-x" aria-label="ปิดอภิธานศัพท์">×</button></div>' +
      '<label class="ix-jl-search-l" for="ix-jl-search">ค้นหา (ไทยหรืออังกฤษ)</label>' +
      '<input id="ix-jl-search" type="search" autocomplete="off" placeholder="เช่น GCP, path, กำลังสอง">' +
      '<label class="ix-jl-toggle"><input type="checkbox" id="ix-jl-hl" checked> ไฮไลต์คำศัพท์ในบทเรียน</label>' +
      '<div class="ix-jl-lvl" role="radiogroup" aria-label="ระดับคำอธิบายในอภิธานศัพท์">' +
      '<label><input type="radio" name="ix-jl-dlvl" value="beginner" checked> เริ่มต้น</label>' +
      '<label><input type="radio" name="ix-jl-dlvl" value="advanced"> ขั้นสูง</label></div>' +
      '<p class="ix-jl-count" role="status" aria-live="polite"></p><ul class="ix-jl-list"></ul>' +
      '<p class="ix-jl-note">คำอธิบายเรียบเรียงสำหรับการเรียนรู้โดยอ้างอิงแหล่งข้อมูลสาธารณะ ไม่ได้ให้คะแนนความยากของคำจากความถี่ และไม่ได้ส่งข้อความใดออกนอกหน้า</p>';
    if (floating) document.body.appendChild(fab); document.body.appendChild(drawer);
    var list = drawer.querySelector('.ix-jl-list'), search = drawer.querySelector('#ix-jl-search');
    terms.forEach(function (t) {
      var li = el('li', 'ix-jl-item'); li.setAttribute('data-id', t.id);
      li.setAttribute('data-hay', [t.en, t.th].concat(t.match_en || [], t.match_th || []).join(' ').toLowerCase());
      var d = el('details'), s = el('summary');
      s.appendChild(el('strong', null, t.en)); s.appendChild(el('span', 'ix-jl-th', ' · ' + t.th));
      d.appendChild(s);
      var body = el('p', 'ix-jl-body'); body.setAttribute('data-id', t.id); d.appendChild(body);
      if (t.equation) d.appendChild(el('div', 'ix-jl-eq', t.equation));
      var links = el('div', 'ix-jl-links');
      (t.links || []).forEach(function (l) { var a = el('a', 'ix-jl-link', l.label + ' →'); a.href = l.href; a.addEventListener('click', function () { toggleDrawer(false); }); links.appendChild(a); });
      d.appendChild(links); d.appendChild(el('div', 'ix-jl-src', 'แหล่ง: ' + (t.sources || []).join(' · ')));
      var pv = t.provenance || {};
      [['from_slides', 'จากสไลด์'], ['added', 'ส่วนเสริม / คำอธิบายนอกสไลด์']].forEach(function (kv) { var arr = pv[kv[0]] || []; if (!arr.length) return; var box = el('div', 'ix-jl-pv ix-jl-pv-' + kv[0]); box.appendChild(el('div', 'ix-jl-pv-h', kv[1])); var ul = el('ul'); arr.forEach(function (x) { ul.appendChild(el('li', null, x)); }); box.appendChild(ul); d.appendChild(box); });
      d.appendChild(el('div', 'ix-jl-src', provLine(t).replace(/^.*· (สถานะตรวจ)/, '$1')));
      var n = counts[t.id] || 0; d.appendChild(el('div', 'ix-jl-src', n ? ('ไฮไลต์ในบทเรียน ' + n + ' ตำแหน่ง') : 'ไม่ได้ไฮไลต์ในบทเรียน (อาจอยู่เฉพาะในส่วนที่ยกเว้น)'));
      li.appendChild(d); list.appendChild(li);
    });
    var dlevel = 'beginner';
    function renderDrawerText() { list.querySelectorAll('.ix-jl-body').forEach(function (p) { p.textContent = byId[p.getAttribute('data-id')][dlevel]; }); }
    function syncDrawerLevel() { /* popover and drawer keep independent levels by design */ }
    drawer.addEventListener('change', function (e) {
      if (e.target.name === 'ix-jl-dlvl') { dlevel = e.target.value; renderDrawerText(); }
      if (e.target.id === 'ix-jl-hl') {
        var off = !e.target.checked; document.documentElement.classList.toggle('ix-jl-off', off);
        document.querySelectorAll('.ix-term').forEach(function (b) { if (off) { b.setAttribute('tabindex', '-1'); b.removeAttribute('aria-haspopup'); } else { b.removeAttribute('tabindex'); b.setAttribute('aria-haspopup', 'dialog'); } });
        close();
      }
    });
    function filter() {
      var v = search.value.trim().toLowerCase(), n = 0;
      list.querySelectorAll('.ix-jl-item').forEach(function (li) { var on = !v || li.getAttribute('data-hay').indexOf(v) !== -1; li.hidden = !on; if (on) n++; });
      drawer.querySelector('.ix-jl-count').textContent = v ? ('พบ ' + n + ' คำ') : ('ทั้งหมด ' + terms.length + ' คำ');
    }
    search.addEventListener('input', filter);
    function toggleDrawer(show) {
      drawer.hidden = !show; fab.setAttribute('aria-expanded', String(show));
      if (show) { close(); search.focus({ preventScroll: true }); } else fab.focus({ preventScroll: true });
    }
    fab.addEventListener('click', function (e) { e.stopPropagation(); toggleDrawer(drawer.hidden); });
    drawer.querySelector('.ix-jl-x').addEventListener('click', function () { toggleDrawer(false); });
    renderDrawerText(); filter();

    var api = { version: VERSION, wrapped: wrapped, counts: counts, entry: floating ? 'floating' : 'inline', open: function (id) { var b = document.querySelector('.ix-term[data-ix-term="' + id + '"]'); if (b) open(b); }, close: close, toggleDrawer: toggleDrawer };
    window.IXJargonLens.instance = api;
    return api;
  }

  function featureOn(name) {
    var m = document.querySelector('meta[name="ix-features"]');
    return !!(m && (' ' + m.getAttribute('content').replace(/,/g, ' ') + ' ').indexOf(' ' + name + ' ') !== -1);
  }
  window.IXJargonLens = { version: VERSION, init: init, featureOn: featureOn };
  function auto() {
    if (!featureOn('jargon-lens')) return;
    var data = document.getElementById('ix-glossary'); if (!data) return;
    var cfg = document.querySelector('meta[name="ix-jargon-exclude"]');
    try { init({ glossary: JSON.parse(data.textContent), exclude: cfg ? cfg.getAttribute('content') : '' }); }
    catch (e) { if (window.console) console.warn('IX Jargon Lens disabled:', e.message); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();
})();
