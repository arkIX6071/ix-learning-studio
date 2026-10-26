#!/usr/bin/env python3
"""QA for RS L04 lesson: independent numerics (numpy) vs JS model, plus UI behaviour.
Runs Chromium headless at desktop, iPad (820x1180 touch) and phone (390x844 touch)."""
import json, math, pathlib, sys
import numpy as np
from playwright.sync_api import sync_playwright

PAGE = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
CH = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
res = []
def check(name, ok, detail=''):
    res.append({'name': name, 'pass': bool(ok), 'detail': str(detail)})

# ---------- independent reference values (Python/numpy) ----------
ref_cal = 2 + 100 * (12 - 2) / 255
ref_mis = 2 + 180 * (12 - 2) / 255
PTS = {'P1': (15, 15, .6, -.4), 'P2': (85, 18, -.5, .7), 'P3': (52, 88, .3, .8), 'P4': (18, 72, -.8, -.2), 'P5': (82, 78, .7, .5), 'P6': (50, 48, -.3, -.9),
       'P7': (32, 40, .9, .1), 'P8': (68, 60, -.6, -.6), 'C1': (8, 10, .4, .9), 'C2': (22, 8, -.9, .3), 'C3': (12, 24, .2, -.7), 'C4': (26, 22, -.4, -.5)}
GOOD = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'C1', 'C2', 'C3', 'C4']
def fwd(X, Y, dx, dy, rot, s):
    t = math.radians(rot); c = 50
    return (c + s * ((X - c) * math.cos(t) - (Y - c) * math.sin(t)) + dx, c + s * ((X - c) * math.sin(t) + (Y - c) * math.cos(t)) + dy)
def ref_fit(n, dx=10, dy=-4, rot=0, s=1, sig=.5, order=GOOD):
    g, cp = order[:n], order[n:]
    obs = {k: np.array(fwd(PTS[k][0], PTS[k][1], dx, dy, rot, s)) + sig * np.array(PTS[k][2:]) for k in PTS}
    A = np.array([[1, PTS[k][0], PTS[k][1]] for k in g], float)
    ax, *_ = np.linalg.lstsq(A, np.array([obs[k][0] for k in g]), rcond=None)
    ay, *_ = np.linalg.lstsq(A, np.array([obs[k][1] for k in g]), rcond=None)
    def rm(ids):
        v = [(obs[k][0] - (ax[0] + ax[1] * PTS[k][0] + ax[2] * PTS[k][1]), obs[k][1] - (ay[0] + ay[1] * PTS[k][0] + ay[2] * PTS[k][1])) for k in ids]
        return math.sqrt(sum(a * a + b * b for a, b in v) / len(v)) if v else float('nan')
    return ax, ay, rm(g), rm(cp)
CONT = np.array([[20, 22, 25, 30, 34, 36], [21, 60, 62, 31, 35, 38], [23, 61, 200, 64, 36, 40], [26, 58, 63, 60, 39, 42], [30, 33, 36, 40, 44, 46], [33, 35, 39, 43, 47, 50]], float)
def ref_bl(u, v):
    fx, fy = u - .5, v - .5; j0, i0 = int(math.floor(fx)), int(math.floor(fy)); a, b = fx - j0, fy - i0
    return (1 - a) * (1 - b) * CONT[i0, j0] + a * (1 - b) * CONT[i0, j0 + 1] + (1 - a) * b * CONT[i0 + 1, j0] + a * b * CONT[i0 + 1, j0 + 1]

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CH, args=['--no-sandbox'])
    for label, vp, touch in [('desktop', {'width': 1280, 'height': 900}, False), ('ipad', {'width': 820, 'height': 1180}, True), ('phone', {'width': 390, 'height': 844}, True)]:
        ctx = br.new_context(viewport=vp, has_touch=touch, is_mobile=touch, device_scale_factor=2 if touch else 1)
        p = ctx.new_page(); errs = []
        p.on('pageerror', lambda e: errs.append(str(e)))
        p.on('console', lambda m: errs.append('console:' + m.text) if m.type == 'error' else None)
        p.goto(PAGE.as_uri()); p.wait_for_load_state('load')
        t = f'{label}:'
        check(t + ' JS ready', 'JavaScript ทำงาน' in p.inner_text('#js-status'))
        if label == 'desktop':
            # ---- numeric anchors through exported pure functions ----
            v = p.evaluate('RS.calib(100,2,12,255)'); check('anchor DN_TO_RADIANCE', abs(v - 5.921568627) < 1e-6 and abs(v - ref_cal) < 1e-12, v)
            v = p.evaluate('RS.calib(180,2,12,255)'); check('anchor CALIBRATION_MISUSE', abs(v - 9.058823529) < 1e-6 and abs(v - ref_mis) < 1e-12, v)
            v = p.evaluate('RS.sensorDN(5,2,10,255)'); check('anchor SENSOR_RESPONSE', v['dn'] == 20 and v['state'] == 'ok', v)
            v = p.evaluate('RS.forward(20,30,{dx:10,dy:-4,rot:0,s:1})'); check('anchor TRANSLATION', abs(v[0] - 30) < 1e-12 and abs(v[1] - 26) < 1e-12, v)
            v = p.evaluate('RS.stretch(100,40,125,255)'); check('stretch 100 -> 180', v == 180, v)
            v = p.evaluate('(()=>{const g=RS.gainOffset(2,12,255);return [g.G,g.B,RS.invDN(100,g.G,g.B)]})()')
            check('inverse response consistent', abs(v[0] - 25.5) < 1e-12 and abs(v[1] + 51) < 1e-12 and abs(v[2] - ref_cal) < 1e-12, v)
            v = p.evaluate('RS.sensorDN(200,2,10,255)'); check('saturation high', v['dn'] == 255 and v['state'] == 'high', v)
            v = p.evaluate('RS.sensorDN(0,2,-20,255)'); check('clip low', v['dn'] == 0 and v['state'] == 'low', v)
            for bad in ['RS.calib(10,5,5,255)', 'RS.stretch(10,50,40,255)', 'RS.fitAffine([[0,0],[1,1],[2,2]],[[0,0],[1,1],[2,2]])', 'RS.sensorDN(NaN,1,0,255)']:
                ok = p.evaluate(f'(()=>{{try{{{bad};return false}}catch(e){{return e instanceof RangeError}}}})()'); check('rejects invalid: ' + bad, ok)
            # LS fit vs numpy for several n
            for n in (3, 4, 6, 8):
                ax, ay, rf, rc = ref_fit(n, rot=7, s=1.03)
                js = p.evaluate(f'''(()=>{{const P={json.dumps({k: list(v) for k, v in PTS.items()})},O={json.dumps(GOOD)};const par={{dx:10,dy:-4,rot:7,s:1.03}},sig=.5;
                  const obs=k=>{{const [x,y]=RS.forward(P[k][0],P[k][1],par);return [x+sig*P[k][2],y+sig*P[k][3]]}};
                  const g=O.slice(0,{n}),c=O.slice({n});const f=RS.fitAffine(g.map(k=>[P[k][0],P[k][1]]),g.map(obs));
                  const res=ids=>ids.map(k=>{{const q=RS.applyAffine(f,P[k][0],P[k][1]),o=obs(k);return [o[0]-q[0],o[1]-q[1]]}});
                  return [f.a,f.b,RS.rmse(res(g)),RS.rmse(res(c))]}})()''')
                d = max(np.max(np.abs(np.array(js[0]) - ax)), np.max(np.abs(np.array(js[1]) - ay)), abs(js[2] - rf), abs(js[3] - rc))
                check(f'LS affine n={n} matches numpy', d < 1e-9, f'maxdiff={d:.2e} rmse_fit={js[2]:.4f} rmse_cp={js[3]:.4f}')
                if n == 3: check('n=3 exact fit RMSE=0', js[2] < 1e-9 and js[3] > 0.1, js[2])
            v = p.evaluate('(()=>{const f={a:[3,1.1,0.2],b:[-2,-0.1,0.95]};const q=RS.applyAffine(f,40,60);return RS.invertAffine(f,q[0],q[1])})()')
            check('affine inverse round-trip', abs(v[0] - 40) < 1e-9 and abs(v[1] - 60) < 1e-9, v)
            for (u, vv) in [(2.8, 2.9), (1.25, 3.7), (4.4, 1.6)]:
                js = p.evaluate(f'RS.sampleBL({json.dumps(CONT.tolist())},{u},{vv}).value'); check(f'bilinear ({u},{vv}) matches numpy', abs(js - ref_bl(u, vv)) < 1e-9, f'{js:.4f}')
            check('bilinear at pixel centre = value', abs(p.evaluate(f'RS.sampleBL({json.dumps(CONT.tolist())},2.5,2.5).value') - 200) < 1e-12)
            check('NN picks containing pixel', p.evaluate(f'RS.sampleNN({json.dumps(CONT.tolist())},2.99,2.01)') == 200)
            check('NN outside -> null', p.evaluate(f'RS.sampleNN({json.dumps(CONT.tolist())},-0.1,2)') is None)
            E = 1550 * math.cos(math.radians(90 - 55)); Lt = .4 * E * .85 / math.pi + 12
            v = p.evaluate('(()=>{const E=RS.irradiance(1550,55,1);return [E,RS.totalRadiance(.4,E,.85,12)]})()'); check('haze model vs python', abs(v[0] - E) < 1e-9 and abs(v[1] - Lt) < 1e-9, v)
            v = p.evaluate('RS.irradiance(1000,90,0.983)'); check('earth-sun distance 1/d^2', abs(v - 1000 / .983 ** 2) < 1e-9, v)
        # ---- UI: module 1 ----
        p.click('#m1-svg rect[aria-label^="แถว 0 คอลัมน์ 1"]'); check(t + ' M1 tap pixel', p.inner_text('#m1-ij') == '(0, 1)' and p.inner_text('#m1-dn') == '14', p.inner_text('#m1-dn'))
        p.check('#m1-stretch'); check(t + ' M1 stretch keeps DN', p.inner_text('#m1-dn') == '14' and 'ยืดแล้ว' in p.inner_text('#m1-disp'))
        # ---- module 2 ----
        check(t + ' M2 translation readout', p.inner_text('#g-tout') == '(30.000, 26.000)', p.inner_text('#g-tout'))
        check(t + ' M2 default r=0 warning', p.inner_text('#g-r') == '0' and 'r = 0' in p.inner_text('#g-msg'))
        fit0 = p.inner_text('#g-rmse-fit'); check(t + ' M2 RMSE fit 0 at n=3', fit0.startswith('0.000'), fit0)
        p.fill('#g-n-num', '6'); p.dispatch_event('#g-n-num', 'change')
        _, _, rf6, rc6 = ref_fit(6)
        check(t + ' M2 numeric input n=6 updates RMSE', p.inner_text('#g-r') == '6' and abs(float(p.inner_text('#g-rmse-fit').split()[0]) - rf6) < 6e-4 and abs(float(p.inner_text('#g-rmse-cp').split()[0]) - rc6) < 6e-4, (p.inner_text('#g-rmse-fit'), rf6, rc6))
        p.eval_on_selector('#g-rot', "e=>{e.value='8';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        check(t + ' M2 rotation slider moves test point', p.inner_text('#g-tout') != '(30.000, 26.000)', p.inner_text('#g-tout'))
        p.check('input[name="g-view"][value="cor"]'); check(t + ' M2 corrected view draws residual vectors', p.locator('#g-svg line[stroke="#b3261e"]').count() == 12)
        p.check('input[name="g-dist"][value="cluster"]'); rc_cl = float(p.inner_text('#g-rmse-cp').split()[0])
        check(t + ' M2 clustered GCP raises CP RMSE', rc_cl > rc6, f'{rc_cl} vs {rc6:.3f}')
        p.click('button[aria-label="เพิ่ม หมุน (θ)"]'); check(t + ' M2 plus button', p.input_value('#g-rot') == '8.5', p.input_value('#g-rot'))
        p.click('#g-reset'); check(t + ' M2 reset', p.inner_text('#g-tout') == '(30.000, 26.000)' and p.input_value('#g-n') == '3' and p.is_checked('input[name="g-view"][value="raw"]'))
        p.fill('#g-n-num', '99'); p.dispatch_event('#g-n-num', 'change'); check(t + ' M2 invalid input clamped + flagged', p.input_value('#g-n') == '8' and p.get_attribute('#g-n-num', 'aria-invalid') == 'true')
        p.click('#g-reset')
        # ---- module 3 ----
        check(t + ' M3 default L', p.inner_text('#r-L') == '5.9216' and p.inner_text('#r-dn2') == '180' and p.inner_text('#r-Lbad') == '9.0588', (p.inner_text('#r-L'), p.inner_text('#r-Lbad')))
        p.eval_on_selector('#r-dn', "e=>{e.value='255';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        check(t + ' M3 saturation message', 'อิ่มตัว' in p.inner_text('#r-msg') and p.inner_text('#r-L') == '12.0000')
        p.fill('#r-lmax-num', '3'); p.dispatch_event('#r-lmax-num', 'change'); p.fill('#r-lmin-num', '5'); p.dispatch_event('#r-lmin-num', 'change')
        check(t + ' M3 Lmax<=Lmin rejected', 'ต้องมากกว่า' in p.inner_text('#r-msg') and p.inner_text('#r-L') == '—')
        p.click('#r-reset'); check(t + ' M3 reset', p.inner_text('#r-L') == '5.9216')
        p.check('input[name="r-bits"][value="4095"]'); check(t + ' M3 12-bit rescale', p.get_attribute('#r-dn', 'max') == '4095' and abs(float(p.inner_text('#r-L')) - ref_cal) < 0.002, p.inner_text('#r-L'))
        p.click('#r-reset')
        check(t + ' M3 sensor calc anchor', p.inner_text('#s-dn') == '20', p.inner_text('#s-dn'))
        v0 = p.inner_text('#h-rho-dos'); p.eval_on_selector('#h-elev', "e=>{e.value='25';e.dispatchEvent(new Event('input',{bubbles:true}))}")
        check(t + ' M3 DOS rho invariant to sun elevation', p.inner_text('#h-rho-dos') == v0 == '0.4000' and float(p.inner_text('#h-rho-raw')) > 0.4, (v0, p.inner_text('#h-rho-raw')))
        p.click('#r-reset')
        # ---- module 4 ----
        p.check('input[name="rs-m"][value="bl"]')
        _, ox, oy = 0, None, None
        th = math.radians(10); ox_, oy_ = 2.5 - 3, 2.5 - 3   # default cell (2,2), sx=.3, sy=.4, rot=10
        u = 3 + ox_ * math.cos(th) - oy_ * math.sin(th) + .3; vv = 3 + ox_ * math.sin(th) + oy_ * math.cos(th) + .4
        uv = p.inner_text('#rs-uv').strip('()').split(',')
        check(t + ' M4 (u,v) mapping matches python', abs(float(uv[0]) - u) < 6e-4 and abs(float(uv[1]) - vv) < 6e-4, (uv, u, vv))
        check(t + ' M4 bilinear readout matches numpy', abs(float(p.inner_text('#rs-bl')) - ref_bl(u, vv)) < 6e-4, (p.inner_text('#rs-bl'), ref_bl(u, vv)))
        maxout = float(p.locator('#rs-stats tr').nth(1).locator('td').nth(2).inner_text())
        check(t + ' M4 bilinear loses extreme 200', maxout < 200, maxout)
        p.check('input[name="rs-d"][value="cat"]'); check(t + ' M4 categorical bilinear flags invalid classes', 'ไม่มีอยู่จริง' in p.inner_text('#rs-msg'))
        p.check('input[name="rs-m"][value="nn"]'); check(t + ' M4 categorical NN valid', 'ไม่มีอยู่จริง' not in p.inner_text('#rs-msg'))
        p.click('#rs-svg rect[aria-label="output แถว 0 คอลัมน์ 0"]'); check(t + ' M4 tap output cell', p.inner_text('#rs-cell') == 'แถว 0, คอลัมน์ 0')
        p.click('#rs-reset'); check(t + ' M4 reset', p.inner_text('#rs-cell') == 'แถว 2, คอลัมน์ 2' and p.is_checked('input[name="rs-m"][value="nn"]'))
        # ---- module 5 ----
        p.select_option('#dl3-t', 'qc'); p.select_option('#dl3-a', 'c'); p.fill('#dl3-p', 'RMSE CP จะไม่เป็นศูนย์'); p.click('#dl3 button.primary')
        check(t + ' M5 scenario PASS', 'PASS' in p.inner_text('#dl3-fb') and p.inner_text('#dl-score') == '1 / 4')
        p.select_option('#dl0-t', 'enh'); p.select_option('#dl0-a', 'b'); p.fill('#dl0-p', 'ถนนจะชัดขึ้น'); p.click('#dl0 button.primary')
        check(t + ' M5 scenario RETRY', 'RETRY' in p.inner_text('#dl0-fb'))
        # ---- module 6 ----
        p.check('input[name="mq0"][value="a"]'); p.click('#mq0 button[data-act="check"]'); check(t + ' M6 reasoning required', 'เหตุผล' in p.inner_text('#mq0-fb'))
        p.fill('#mq0-r', 'ตำแหน่งกับค่าเป็นข้อมูลคนละชนิดของ pixel'); p.click('#mq0 button[data-act="check"]'); check(t + ' M6 Q1 PASS', 'PASS' in p.inner_text('#mq0-fb'))
        p.fill('#mq1-n', '7.0'); p.fill('#mq1-r', 'ใช้สูตร Lmin + DN*(range)/255'); p.click('#mq1 button[data-act="check"]'); check(t + ' M6 Q2 wrong -> RETRY', 'RETRY' in p.inner_text('#mq1-fb'))
        p.fill('#mq1-n', '7.38'); p.click('#mq1 button[data-act="check"]'); check(t + ' M6 Q2 7.38 -> PASS', 'PASS' in p.inner_text('#mq1-fb'))
        p.check('input[name="mq3"][value="a"]'); p.fill('#mq3-r', 'offset ไม่เปลี่ยนจึงเท่าเดิม'); p.click('#mq3 button[data-act="check"]')
        check(t + ' M6 level-2 hint appears after wrong', 'Hint' in p.inner_text('#mq3-fb'))
        check(t + ' M6 level-3 has no hint button', p.locator('#mq7 button[data-act="hint"]').count() == 0)
        check(t + ' M6 counters', p.inner_text('#mg-done') == '2 / 8' and p.inner_text('#mg-first') == '1 / 8', (p.inner_text('#mg-done'), p.inner_text('#mg-first')))
        p.click('#mg-export'); out = p.input_value('#mg-out'); check(t + ' M6 export summary', 'Q2' in out and '7.38' in out and 'S4' in out)
        # ---- layout ----
        sw = p.evaluate('[document.documentElement.scrollWidth, innerWidth]'); check(t + ' no horizontal overflow', sw[0] <= sw[1] + 1, sw)
        small = p.evaluate("[...document.querySelectorAll('.tools button,.btn')].filter(b=>b.offsetParent).map(b=>{const r=b.getBoundingClientRect();return Math.min(r.width,r.height)}).reduce((a,b)=>Math.min(a,b),999)")
        check(t + ' touch targets >= 44px', small >= 44, small)
        check(t + ' no JS/console errors', not errs, errs)
        if label != 'desktop':
            p.evaluate('scrollTo(0,0)'); p.click('#g-reset'); p.click('#r-reset'); p.click('#rs-reset')
        for sec in ['m2', 'm3', 'm4']:
            p.locator('#' + sec).screenshot(path=str(OUT / f'{label}_{sec}.png'))
        p.screenshot(path=str(OUT / f'{label}_top.png'))
        ctx.close()
    br.close()
fails = [r for r in res if not r['pass']]
(OUT / 'results.json').write_text(json.dumps({'passed': len(res) - len(fails), 'total': len(res), 'results': res}, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({'passed': len(res) - len(fails), 'total': len(res), 'failures': fails}, ensure_ascii=False, indent=1))
