#!/usr/bin/env python3
"""Isolated 005C integration checks. No remote I/O, no writes into source tree.
Usage: python tests/test_cap005c.py --out /path/out
Browsers: Chromium via Playwright; network navigation is not exercised here.
"""
from pathlib import Path
import argparse, json, hashlib, math, re, sys
from playwright.sync_api import sync_playwright

p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args()
OUT=Path(args.out).resolve();OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[1]
lesson=ROOT/'lessons/rs-l04/index.html'
source=lesson.read_text(encoding='utf-8')
assets=ROOT/'assets/ix-components/v0.2.0'
q=[]
def ok(label,expr,detail=''):
    q.append(dict(name=label,passed=bool(expr),detail=str(detail)[:180]));
    if not expr: print('FAIL',label,repr(detail),flush=True)

# File-system and provenance checks
for name in ['jargon-lens.css','mechanism-viewer.css','jargon-lens.js','mechanism-viewer.js','mv-fallback.html']:
    ok('asset:'+name,(assets/name).is_file())
for n in range(1,7):ok('lesson:M'+str(n),f'id="m{n}"' in source)
ok('lesson:mechanism', 'id="mv"' in source)
ok('lesson:backlink','href="../../"' in source)
ok('lesson:corrected slide ref','p60' not in source)
ok('lesson:neutral status','ไฟล์เรียนส่วนตัว (LOCAL)' not in source)
ok('lesson:original two unchanged',hashlib.sha256((ROOT/'lessons/gnss-epoch/index.html').read_bytes()).hexdigest()=='9f92eb7831d039fe73ee8cc4244afe58920ea36b44a40bc9c8855b193b71b372' and hashlib.sha256((ROOT/'lessons/newtons-cooling/index.html').read_bytes()).hexdigest()=='fd9291a81e26be7237b366088443423b33f6b243dc3f488264dee95d8981b3e5')
ok('lesson:3 cards',source.count('<!--IX-CAP005:BEGIN')==5 and (ROOT/'index.html').read_text().count('class="lesson"')==3)
for f in ['jargon-lens.css','mechanism-viewer.css','jargon-lens.js','mechanism-viewer.js']:
    ok('lesson:correct asset ref '+f,('../../assets/ix-components/v0.2.0/'+f) in source)
gloss=json.loads((ROOT/'lessons/rs-l04/glossary.th.json').read_text(encoding='utf8'))
ok('glossary:9 terms',len(gloss['terms'])==9)
ok('glossary:version',gloss['version']=='0.2.0-publicsafe.1')
ok('glossary:pending owner',all(t['review']['owner']=='PENDING_PUBLIC_SAFE_EDITORIAL_CONFIRMATION' for t in gloss['terms']))
ok('glossary:page references',all(1<=int(x)<=59 for x in re.findall(r'\bp(\d+)\b',json.dumps(gloss,ensure_ascii=False))))

# Make an in-memory facsimile of modular page to test scripts when HTTP is blocked.
inline=source
for f in ['jargon-lens.css','mechanism-viewer.css']:
    inline=inline.replace('<link rel="stylesheet" href="../../assets/ix-components/v0.2.0/'+f+'">','<style>\n'+(assets/f).read_text()+'\n</style>')
for f in ['jargon-lens.js','mechanism-viewer.js']:
    inline=inline.replace('<script src="../../assets/ix-components/v0.2.0/'+f+'"></script>','<script>\n'+(assets/f).read_text()+'\n</script>')
ok('inline:all external module refs replaced','<script src="../../assets/' not in inline and '<link rel="stylesheet" href="../../assets/' not in inline)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for label,viewport,touch in [('desktop',(1280,900),False),('ipad_emulation',(820,1180),True),('phone_emulation',(390,844),True)]:
        ctx=browser.new_context(viewport={'width':viewport[0],'height':viewport[1]},has_touch=touch,is_mobile=touch)
        page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(inline,wait_until='domcontentloaded',timeout=20000)
        def c(name,expr,detail=''):ok(label+':'+name,expr,detail)
        c('JS ready','JavaScript ทำงาน' in page.locator('#js-status').inner_text())
        c('jargon initialized',page.evaluate('IXJargonLens.instance.version')=='0.2.0')
        c('viewer initialized',page.evaluate('IXMechanismViewer.version')=='0.2.0')
        c('nine glossary terms highlighted',len(set(page.locator('.ix-term').evaluate_all('(ee)=>ee.map(e=>e.dataset.ixTerm)')))==9)
        c('mechanism graphics',page.locator('[data-ix-mechanism] svg').count()>=2)
        c('mechanism equations', '185.63' in page.locator('#mv').inner_text() and '9.77' in page.locator('#mv').inner_text())
        c('M1 pixel output',page.locator('#m1-ij').inner_text()=='(3, 4)')
        c('DN radiance anchor',abs(page.evaluate('RS.calib(100,2,12,255)')-5.92156862745098)<1e-10)
        c('numerical sensor response',page.evaluate('RS.sensorDN(5,2,10,255).dn')==20)
        c('geometry anchor',page.evaluate('RS.forward(20,30,{dx:10,dy:-4,rot:0,s:1})')==[30,26])
        c('library back href',page.locator('a[href="../../"]').count()>=1)
        c('no viewport overflow',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'))
        # Exercise simple user events without potentially waiting for sticky navigation animations.
        page.evaluate("document.querySelector('[data-ix-glossary-open]').click()")
        c('glossary drawer opens',page.locator('#ix-jl-drawer').is_visible())
        c('all 9 glossary entries',page.locator('.ix-jl-item').count()==9)
        page.keyboard.press('Escape')
        c('glossary closes',not page.locator('#ix-jl-drawer').is_visible())
        page.evaluate("document.querySelector('#mv input[type=range]').value='10'; document.querySelector('#mv input[type=range]').dispatchEvent(new Event('input',{bubbles:true}))")
        c('scanner slider changes swath', '248.' in page.locator('#mv').inner_text()) # 2*705*tan10°=248.64
        page.evaluate("document.querySelector('#mv button[data-act=reset]').click()")
        c('scanner reset', '185.63 km' in page.locator('#mv').inner_text())
        page.evaluate("document.querySelector('#m1-stretch').click()")
        c('M1 contrast toggled',page.locator('#m1-stretch').is_checked())
        c('no page errors',not errors,errors)
        if label in ('ipad_emulation','phone_emulation'):
            page.locator('#mv').scroll_into_view_if_needed(timeout=10000)
            page.screenshot(path=str(OUT/(label+'_mechanism.png')))
        ctx.close()
    # Optional-capabilities disabled: base lesson remains functional.
    no_features=inline.replace('name="ix-features" content="jargon-lens mechanism-viewer"', 'name="ix-features" content=""')
    ctx=browser.new_context(viewport={'width':820,'height':1180})
    page=ctx.new_page();page.set_content(no_features,wait_until='domcontentloaded')
    ok('feature-off: no jargon buttons',page.locator('.ix-term').count()==0)
    ok('feature-off: base L04 works','JavaScript ทำงาน' in page.locator('#js-status').inner_text())
    ok('feature-off: numeric anchor',abs(page.evaluate('RS.calib(100,2,12,255)')-5.92156862745098)<1e-10)
    ctx.close()
    browser.close()
report={'suite':'IXLS-CAPABILITIES-005C independent isolated integration smoke','browser':'Chromium /usr/bin/chromium','navigation':'in-memory; actual HTTP and file:// blocked','total':len(q),'passed':sum(x['passed'] for x in q),'failed':[x for x in q if not x['passed']],'checks':q}
(OUT/'results_005c.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'total':report['total'],'failed':report['failed']},ensure_ascii=False),flush=True)
sys.exit(bool(report['failed']))
