/*! IX Mechanism Viewer v0.2.0 — "whiskbroom-scan" model.
 *  Original code written for IX Learning Studio (no third-party code). Pure SVG, no WebGL,
 *  no network. Every drawn position and every number comes from IXScanModel below.
 *
 *  Explicit model (lecture slides p8, p11–15):
 *    scan angle      θ_j = θmax·(2j/(M−1) − 1),  j = 0..M−1    (equal angle increments, p14)
 *    ground offset   x = H·tan θ − v_e·t                      (flat Earth, Earth rotates east, p8/p11)
 *    along-track     y = v_g·t
 *    Earth surface   v_e = ω_e·R_e·cos λ ,  ω_e = 72.72 µrad/s, R_e = 6378.1 km   (p11)
 *    scene time      t_s = L / v_g  (L = swath = 2H·tan θmax; p11 uses t_s = L/(ω₀·r_e))
 *    pixel growth    cross-track ∝ sec²θ, along-track ∝ sec θ  (p13–14)
 *  Simplifications: flat Earth (no curvature, p16), constant attitude/altitude/velocity (no p17
 *  effects), one detector line per sweep, one-direction sweep, orbit treated as north–south
 *  (slide p12 applies cos 13° for inclination; ignored here), Earth motion within one sweep ignored.
 */
(function () {
  'use strict';
  var VERSION = '0.2.0', OMEGA_E = 72.72e-6, R_E_KM = 6378.1, D2R = Math.PI / 180;

  var IXScanModel = {
    summary: function (p) {
      var th = p.thetaMaxDeg * D2R;
      var swath = 2 * p.H * Math.tan(th);
      var ts = swath / p.vg;
      var ve = p.earthRot ? OMEGA_E * R_E_KM * 1000 * Math.cos(p.latDeg * D2R) : 0;
      var skew = ve * ts / 1000;
      return { swath: swath, ts: ts, ve: ve, skew: skew, skewPct: 100 * skew / swath, edgeCross: 1 / Math.pow(Math.cos(th), 2), edgeAlong: 1 / Math.cos(th) };
    },
    ground: function (p, s, j) {          /* s: line time fraction 0..1, j: sample 0..M-1 */
      var S = IXScanModel.summary(p), th = p.thetaMaxDeg * D2R * (2 * j / (p.M - 1) - 1), t = s * S.ts;
      return { x: p.H * Math.tan(th) - S.ve * t / 1000, y: p.vg * t, theta: th };
    },
    rawImage: function (p, s, j, fixSkew, fixPan) {   /* where a naive raw image puts the sample */
      var S = IXScanModel.summary(p), t = s * S.ts, th = p.thetaMaxDeg * D2R * (2 * j / (p.M - 1) - 1);
      var x = fixPan ? p.H * Math.tan(th) : (2 * j / (p.M - 1) - 1) * S.swath / 2;  /* uniform columns */
      if (fixSkew) x -= S.ve * t / 1000;                                        /* deskew: shift west */
      return { x: x, y: p.vg * t };
    }
  };

  function mount(host, opts) {
    opts = opts || {};
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var D = { H: 705, thetaMaxDeg: 7.5, latDeg: 40, vg: 6.754, earthRot: true, M: 25, N: 12, s: 0.55, fixSkew: false, fixPan: false };
    var p = {}; for (var k in D) p[k] = D[k];
    var uid = 'mv' + Math.random().toString(36).slice(2, 7);
    host.classList.add('ix-mv'); host.innerHTML =
      '<div class="ix-mv-grid">' +
      '<div class="ix-mv-ctrls" role="group" aria-label="ตัวแปรของแบบจำลอง scanner">' +
      ctrlHtml('theta', 'ครึ่งมุมกวาด θmax', 2, 40, 0.5, D.thetaMaxDeg, '°', 'Landsat TM ≈ 7.5° · airborne scanner ได้ถึง ~40°') +
      ctrlHtml('H', 'ความสูง H', 300, 1000, 5, D.H, 'km', '') +
      ctrlHtml('lat', 'ละติจูด λ', 0, 80, 1, D.latDeg, '°', 'v_e = ω_e·R_e·cos λ') +
      ctrlHtml('s', 'เวลาในการถ่ายภาพ (สัดส่วนของ scene)', 0, 1, 0.005, D.s, '', '') +
      '<div class="ix-mv-row"><label><input type="checkbox" data-k="earthRot" checked> คิดการหมุนของโลก</label></div>' +
      '<div class="ix-mv-row"><label><input type="checkbox" data-k="fixSkew"> แก้ skew (deskew)</label><label><input type="checkbox" data-k="fixPan"> แก้ panoramic (tan θ)</label></div>' +
      '<div class="ix-mv-row"><button type="button" class="ix-mv-btn" data-act="play">' + (reduce ? 'ถัดไป 1 scan line ▶' : '▶ เล่น') + '</button><button type="button" class="ix-mv-btn" data-act="reset">↶ Reset</button></div>' +
      '</div>' +
      '<div class="ix-mv-views">' +
      '<figure><p class="ix-mv-read" data-r="iso" aria-live="polite"></p><svg class="ix-mv-iso" viewBox="0 0 560 360" role="img" aria-labelledby="' + uid + '-t1"><title id="' + uid + '-t1">ภาพมุมเฉียงของ scanner กวาดเป็นแนวตั้งฉากกับทิศการบิน</title></svg>' +
      '<figcaption>มุมเฉียง (isometric): ดาวเทียม เส้นสายตา และ scan line บนพื้น · <b>แกนตั้งย่อส่วน</b> และ footprint ขยายให้มองเห็น (อัตราส่วน sec²θ : sec θ ถูกต้อง)</figcaption></figure>' +
      '<figure><p class="ix-mv-read" data-r="top"></p><svg class="ix-mv-top" viewBox="0 0 560 300" role="img" aria-labelledby="' + uid + '-t2"><title id="' + uid + '-t2">มุมมองจากด้านบน: ตำแหน่งจริงของ sample บนพื้นเทียบกับตำแหน่งในภาพดิบ</title></svg>' +
      '<figcaption>มุมบน: ● และกรอบเขียวอมฟ้า = ตำแหน่งจริงบนพื้น · ▪ และกรอบส้ม = ตำแหน่งที่ภาพดิบสมมติ (กริดสม่ำเสมอ) · ถ้ากรอบสองสีไม่ทับกัน แปลว่ายังมีความคลาดเคลื่อน</figcaption></figure>' +
      '</div></div>' +
      '<div class="ix-mv-metrics" aria-live="polite"></div>';
    var $ = function (sel) { return host.querySelector(sel); };
    var iso = $('.ix-mv-iso'), top = $('.ix-mv-top'), out = $('.ix-mv-metrics');
    var keyOf = { theta: 'thetaMaxDeg', H: 'H', lat: 'latDeg', s: 's' };

    function ctrlHtml(k, label, mn, mx, st, v, unit, help) {
      var id = uid + '-' + k;
      return '<div class="control ix-mv-c"><label for="' + id + '">' + label + ' <output data-o="' + k + '"></output></label>' +
        '<input id="' + id + '" data-c="' + k + '" type="range" min="' + mn + '" max="' + mx + '" step="' + st + '" value="' + v + '">' +
        '<div class="tools"><button type="button" data-d="-1" data-c="' + k + '" aria-label="ลด ' + label + '">−</button>' +
        '<input type="number" inputmode="decimal" data-n="' + k + '" min="' + mn + '" max="' + mx + '" step="' + st + '" value="' + v + '" aria-label="กรอก ' + label + '">' +
        '<button type="button" data-d="1" data-c="' + k + '" aria-label="เพิ่ม ' + label + '">+</button></div>' +
        (help ? '<p class="help">' + help + '</p>' : '') + '</div>';
    }
    function setVal(k, v) {
      var r = host.querySelector('input[type=range][data-c="' + k + '"]'), mn = +r.min, mx = +r.max, st = +r.step;
      if (!isFinite(v)) return;
      var qv = Math.min(mx, Math.max(mn, mn + Math.round((v - mn) / st) * st));
      r.value = String(+qv.toFixed(6)); p[keyOf[k]] = +r.value; render();
    }
    host.addEventListener('input', function (e) { var k = e.target.getAttribute('data-c'); if (k && e.target.type === 'range') { p[keyOf[k]] = +e.target.value; render(); } });
    host.addEventListener('change', function (e) {
      var n = e.target.getAttribute('data-n'); if (n) setVal(n, parseFloat(e.target.value));
      var b = e.target.getAttribute('data-k'); if (b) { p[b] = e.target.checked; render(); }
    });
    host.addEventListener('click', function (e) {
      var b = e.target.closest('button'); if (!b || !host.contains(b)) return;
      var k = b.getAttribute('data-c'), d = b.getAttribute('data-d');
      if (k && d) { var r = host.querySelector('input[type=range][data-c="' + k + '"]'); setVal(k, +r.value + (+d) * (+r.step)); return; }
      var act = b.getAttribute('data-act');
      if (act === 'reset') { stop(); for (var q in D) p[q] = D[q]; host.querySelectorAll('input[type=range]').forEach(function (r) { var kk = r.getAttribute('data-c'); r.value = D[keyOf[kk]]; }); host.querySelectorAll('input[data-k]').forEach(function (c) { c.checked = D[c.getAttribute('data-k')]; }); render(); }
      if (act === 'play') { if (reduce) { setVal('s', Math.min(1, (Math.floor(p.s * p.N + 1e-9) + 1) / p.N)); } else if (raf) stop(); else start(); }
    });

    /* ---------- animation: only on request, only while visible ---------- */
    var raf = 0, last = 0, visible = true;
    function start() { var b = host.querySelector('[data-act=play]'); b.textContent = '❚❚ หยุด'; b.setAttribute('aria-pressed', 'true'); if (p.s >= 1) p.s = 0; last = 0; raf = requestAnimationFrame(tick); }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; var b = host.querySelector('[data-act=play]'); if (b) { b.textContent = reduce ? 'ถัดไป 1 scan line ▶' : '▶ เล่น'; b.setAttribute('aria-pressed', 'false'); } }
    function tick(ts) {
      if (!visible || document.hidden) { raf = requestAnimationFrame(tick); last = ts; return; }
      var dt = last ? Math.min(0.1, (ts - last) / 1000) : 0; last = ts;
      p.s = Math.min(1, p.s + dt / 12);              /* 12 s per scene on screen */
      host.querySelector('input[data-c="s"]').value = p.s; render();
      if (p.s >= 1) { stop(); return; } raf = requestAnimationFrame(tick);
    }
    var lastW = 0; if ('ResizeObserver' in window) new ResizeObserver(function () { var w = Math.round(iso.getBoundingClientRect().width); if (w && w !== lastW) { lastW = w; render(); } }).observe(iso); else window.addEventListener('resize', function () { render(); });
    if ('IntersectionObserver' in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }).observe(host);

    /* ---------- drawing ---------- */
    function labelPx(svg, vbW, minPx) { var w = svg.getBoundingClientRect().width || vbW; return Math.min(30, Math.max(minPx, minPx * vbW / w)).toFixed(1); }
    function f(n, d) { return Number(n).toFixed(d == null ? 1 : d); }
    function render() {
      var t0 = (window.performance && performance.now()) || 0;
      var S = IXScanModel.summary(p), half = S.swath / 2, N = p.N, M = p.M;
      var cur = Math.min(N - 1, Math.floor(p.s * N + 1e-9)), frac = p.s >= 1 ? 1 : p.s * N - cur;
      ['theta', 'H', 'lat', 's'].forEach(function (k) {
        var v = p[keyOf[k]]; host.querySelector('output[data-o="' + k + '"]').textContent = k === 's' ? f(v * S.ts, 1) + ' s / ' + f(S.ts, 1) + ' s' : f(v, k === 'theta' ? 1 : 0) + (k === 'H' ? ' km' : '°');
        host.querySelector('input[data-n="' + k + '"]').value = k === 's' ? f(v, 3) : v;
      });
      /* --- iso view: world units = km / half-swath; vertical display height fixed (not to scale) --- */
      var Zd = 1.35, Sc = 105, ox = 300, oy = 170;
      var LF = labelPx(iso, 560, 13);   /* label font in user units so that rendered size >= 13 px */
      var P = function (u, w, z) { return [ox + (u - w) * 0.866 * Sc, oy + (u + w) * 0.5 * Sc - z * Sc]; };
      var g = '', pts = function (arr) { return arr.map(function (a) { return f(a[0], 1) + ',' + f(a[1], 1); }).join(' '); };
      var Wlen = 2; /* along-track display length (scene is square: L = swath) */
      for (var gx = -1; gx <= 1.0001; gx += 0.5) g += '<polyline class="mv-grid" points="' + pts([P(gx, 0, 0), P(gx, Wlen, 0)]) + '"/>';
      for (var gw = 0; gw <= 2.0001; gw += 0.5) g += '<polyline class="mv-grid" points="' + pts([P(-1, gw, 0), P(1, gw, 0)]) + '"/>';
      g += '<polygon class="mv-ground" points="' + pts([P(-1, 0, 0), P(1, 0, 0), P(1, Wlen, 0), P(-1, Wlen, 0)]) + '"/>';
      var tsNow = p.s * S.ts, nadirX = -S.ve * tsNow / 1000;
      g += '<polyline class="mv-track" points="' + pts([P(0, 0, 0), P(nadirX / half, p.vg * tsNow / half, 0)]) + '"/>';
      for (var i = 0; i <= cur; i++) {
        var line = [], jmax = i < cur ? M - 1 : Math.round(frac * (M - 1));
        for (var j = 0; j <= jmax; j++) { var q = IXScanModel.ground(p, i / N, j); line.push(P(q.x / half, q.y / half, 0)); }
        if (line.length > 1) g += '<polyline class="mv-scan' + (i === cur ? ' cur' : '') + '" points="' + pts(line) + '"/>';
      }
      var jc = Math.round(frac * (M - 1)), qc = IXScanModel.ground(p, cur / N, jc), sat = P(nadirX / half, p.vg * tsNow / half, Zd), fp = [qc.x / half, qc.y / half];
      var sec = 1 / Math.cos(qc.theta), a = 0.05 * sec * sec, b = 0.05 * sec;
      g += '<polygon class="mv-fp" points="' + pts([P(fp[0] - a, fp[1] - b, 0), P(fp[0] + a, fp[1] - b, 0), P(fp[0] + a, fp[1] + b, 0), P(fp[0] - a, fp[1] + b, 0)]) + '"/>';
      g += '<polyline class="mv-los" points="' + pts([sat, P(fp[0], fp[1], 0)]) + '"/>';
      g += '<polyline class="mv-drop" points="' + pts([sat, P(nadirX / half, p.vg * tsNow / half, 0)]) + '"/>';
      var sx = sat[0], sy = sat[1];
      g += '<g class="mv-sat"><rect x="' + f(sx - 9) + '" y="' + f(sy - 7) + '" width="18" height="14" rx="2"/><rect class="pan" x="' + f(sx - 40) + '" y="' + f(sy - 4) + '" width="26" height="8"/><rect class="pan" x="' + f(sx + 14) + '" y="' + f(sy - 4) + '" width="26" height="8"/></g>';
      var ah = '<defs><marker id="' + uid + '-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#1e3340"/></marker></defs>';
      var arr0 = P(1.25, 0.2, 0), arr1 = P(1.25, 0.9, 0);
      g += '<polyline class="mv-arrow" marker-end="url(#' + uid + '-ah)" points="' + pts([arr0, arr1]) + '"/><text style="font-size:' + LF + 'px" x="' + f(arr1[0] + 6) + '" y="' + f(arr1[1] + 4) + '">ทิศการบิน</text>';
      var e0 = P(-1, 2.2, 0), e1 = P(-0.4, 2.2, 0);
      g += '<polyline class="mv-arrow" marker-end="url(#' + uid + '-ah)" points="' + pts([e0, e1]) + '"/><text style="font-size:' + LF + 'px" x="' + f(e1[0] - 12) + '" y="' + f(e1[1] + 18) + '">ตะวันออก (โลกหมุน)</text>';
      g = ah + g;
      host.querySelector('[data-r=iso]').innerHTML = '<b>θ = ' + f(qc.theta / D2R, 2) + '° · x = H·tan θ = ' + f(p.H * Math.tan(qc.theta), 1) + ' km</b> · scan line ' + (cur + 1) + '/' + N;
      host.querySelector('[data-r=iso]').innerHTML += '<br><span>แกนตั้งย่อส่วน: H จริง ' + f(p.H, 0) + ' km ≈ ' + f(p.H / half, 1) + ' เท่าของครึ่ง swath</span>';
      iso.innerHTML = iso.querySelector('title').outerHTML + g;

      /* --- top view: ground truth vs naive raw image placement --- */
      var Sm = Math.max(1.08, 1 + S.skewPct / 100 * 2 + 0.08), W2 = 560, H2 = 300, m = 22;
      var sxs = (W2 - 2 * m) / (2 * Sm * half), sys = (H2 - 2 * m) / (S.swath * 1.04), sc2 = Math.min(sxs, sys);
      var cx = W2 / 2, X = function (x) { return cx + x * sc2; }, Y = function (y) { return H2 - m - y * sc2; };
      var h = '<rect class="mv-frame" x="' + f(X(-half)) + '" y="' + f(Y(S.swath)) + '" width="' + f(S.swath * sc2) + '" height="' + f(S.swath * sc2) + '"/>';
      var maxErr = 0, rows = [0, 3, 6, 9, 11];
      var outline = function (fn) { var a = fn(0, 0), b = fn(0, M - 1), c = fn(N - 1, M - 1), d = fn(N - 1, 0); return pts([[X(a.x), Y(a.y)], [X(b.x), Y(b.y)], [X(c.x), Y(c.y)], [X(d.x), Y(d.y)]]); };
      h += '<polygon class="mv-out-raw" points="' + outline(function (i, j) { return IXScanModel.rawImage(p, i / N, j, p.fixSkew, p.fixPan); }) + '"/>';
      h += '<polygon class="mv-out-gnd" points="' + outline(function (i, j) { return IXScanModel.ground(p, i / N, j); }) + '"/>';
      rows.forEach(function (i) {
        var gline = [], rline = [];
        for (var j = 0; j < M; j += 2) {
          var gq = IXScanModel.ground(p, i / N, j), rq = IXScanModel.rawImage(p, i / N, j, p.fixSkew, p.fixPan);
          var err = Math.hypot(gq.x - rq.x, gq.y - rq.y); maxErr = Math.max(maxErr, err);
          if (err * sc2 > 0.8) h += '<line class="mv-err" x1="' + f(X(rq.x)) + '" y1="' + f(Y(rq.y)) + '" x2="' + f(X(gq.x)) + '" y2="' + f(Y(gq.y)) + '"/>';
          h += '<rect class="mv-raw" x="' + f(X(rq.x) - 3) + '" y="' + f(Y(rq.y) - 3) + '" width="6" height="6"/><circle class="mv-gnd" cx="' + f(X(gq.x)) + '" cy="' + f(Y(gq.y)) + '" r="3"/>';
          gline.push([X(gq.x), Y(gq.y)]); rline.push([X(rq.x), Y(rq.y)]);
        }
        h += '<polyline class="mv-gline" points="' + pts(gline) + '"/>';
      });
      host.querySelector('[data-r=top]').textContent = 'กรอบเส้นประ = พื้นที่ ' + f(S.swath, 1) + ' × ' + f(S.swath, 1) + ' km · ทิศการบินชี้ขึ้นด้านบน';
      top.innerHTML = top.querySelector('title').outerHTML + h;

      var ms = ((window.performance && performance.now()) || 0) - t0;
      host.setAttribute('data-render-ms', ms.toFixed(2));
      out.innerHTML = metric('Swath L = 2H·tan θmax', f(S.swath, 2) + ' km') + metric('เวลาถ่ายทั้ง scene t_s = L/v_g', f(S.ts, 2) + ' s') +
        metric('ความเร็วผิวโลก v_e', f(S.ve, 1) + ' m/s') + metric('Skew ท้าย scene = v_e·t_s', f(S.skew, 2) + ' km (' + f(S.skewPct, 2) + '% ของ swath)') +
        metric('ขนาด pixel ที่ขอบ (cross-track) sec²θmax', '×' + f(S.edgeCross, 4)) + metric('ขนาด pixel ที่ขอบ (along-track) sec θmax', '×' + f(S.edgeAlong, 4)) +
        metric('ความคลาดเคลื่อนสูงสุด ภาพดิบ − พื้นจริง', f(maxErr, 3) + ' km', maxErr > 0.05);
      host.setAttribute('data-max-err-km', maxErr.toFixed(6));
    }
    function metric(k, v, bad) { return '<div class="metric' + (bad ? ' bad' : '') + '"><span>' + k + '</span><strong>' + v + '</strong></div>'; }
    render();
    return { render: render, params: p, model: IXScanModel };
  }

  window.IXMechanismViewer = { version: VERSION, mount: mount, model: IXScanModel };
  function auto() {
    var m = document.querySelector('meta[name="ix-features"]');
    if (!m || (' ' + m.getAttribute('content').replace(/,/g, ' ') + ' ').indexOf(' mechanism-viewer ') === -1) return;
    document.querySelectorAll('[data-ix-mechanism="whiskbroom-scan"]').forEach(function (el) { try { mount(el); } catch (e) { if (window.console) console.warn('IX Mechanism Viewer disabled:', e.message); } });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();
})();
