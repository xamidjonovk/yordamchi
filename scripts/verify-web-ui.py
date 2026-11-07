"""Exercise dashboard against a fresh private instance, without cloud calls."""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'.impeccable/review';output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hpa-web-review-') as private:
        env=dict(os.environ,HPA_HOME=private,HERMES_HOME=private,HERMES_BIN=str(Path(private)/'missing-hermes'),PYTHONUTF8='1')
        with (Path(private)/'server.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([sys.executable,'-m','hermes_personal_agent.cli','web','--no-browser','--port','8799'],
                env=env,stdout=log,stderr=log,creationflags=0x08000000 if os.name=='nt' else 0)
            try:
                url=None
                for _ in range(100):
                    text=(Path(private)/'server.log').read_text(encoding='utf-8')
                    if 'http://127.0.0.1:8799/#token=' in text:
                        url='http://127.0.0.1:8799/#token='+text.split('#token=',1)[1].split()[0];break
                    if process.poll() is not None: raise RuntimeError('Web server did not start')
                    time.sleep(.1)
                if not url:raise RuntimeError('No local URL')
                with sync_playwright() as p:
                    browser=p.chromium.launch()
                    page=browser.new_page(viewport={'width':1440,'height':1080},reduced_motion='reduce')
                    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                    page.goto(url);page.wait_for_function("() => document.querySelector('#connection').textContent === 'Panel ulangan'")
                    page.screenshot(path=str(output/'desktop.png'),full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.get_by_role('button',name='Menga moslashtirish',exact=True).click()
                    page.locator('#owner-name').fill('Dars ishtirokchisi')
                    page.locator('#personal-context').fill('Men Python oâ€˜rganaman. Misol bilan tushuntir.')
                    page.get_by_role('button',name='Profilni saqlash',exact=True).click()
                    page.wait_for_function("() => document.querySelector('#notice').textContent.includes('Profil saqlandi')")
                    page.get_by_role('button',name='Bilimlarim',exact=True).click()
                    page.locator('#note-title').fill('Dars jadvali')
                    page.locator('#note-text').fill('Python darsi juma kuni soat 18 da boshlanadi.')
                    page.get_by_role('button',name='Xotiraga saqlash',exact=True).click()
                    page.locator('.source-row').wait_for()
                    page.locator('#query').fill('Python');page.get_by_role('button',name='Qidirish',exact=True).click()
                    page.locator('.result').first.wait_for();assert 'Python' in page.locator('#results').inner_text()
                    page.screenshot(path=str(output/'memory.png'),full_page=True)
                    page.get_by_role('button',name='Qidiruvdan chiqarish',exact=True).click()
                    page.get_by_role('button',name='Bekor qilish',exact=True).click()
                    assert page.locator('.source-row').count()==1
                    page.locator('#note-title').fill('Ikkinchi manba')
                    page.locator('#note-text').fill('Bu manba Escape bilan yopilganda saqlanishi kerak.')
                    page.get_by_role('button',name='Xotiraga saqlash',exact=True).click()
                    page.wait_for_function("() => document.querySelectorAll('.source-row').length === 2")
                    page.locator('.source-row button').last.click()
                    page.locator('#forget-dialog button[value=confirm]').click()
                    page.wait_for_function("() => document.querySelectorAll('.source-row').length === 1")
                    page.locator('.source-row button').first.click()
                    page.keyboard.press('Escape')
                    page.wait_for_function("() => !document.querySelector('#forget-dialog').open")
                    assert page.locator('.source-row h3').inner_text()=='Ikkinchi manba'
                    page.get_by_role('button',name='Yangilash',exact=True).click()
                    page.wait_for_timeout(200)
                    assert page.locator('.source-row').count()==1
                    page.get_by_role('button',name='Suhbat',exact=True).click()
                    page.locator('#message').fill('Test message')
                    page.get_by_role('button',name='Yuborish',exact=True).click()
                    page.wait_for_function("() => document.querySelector('#notice').textContent.includes('AI javob bermadi')")
                    page.get_by_role('button',name='Yangi suhbat',exact=True).click()
                    page.wait_for_function("() => document.querySelector('#notice').textContent.includes('Yangi suhbat')")
                    assert page.locator('#welcome').is_visible()
                    assert page.locator('#message').input_value()==''
                    page.locator('[data-prompt]').first.click()
                    assert page.locator('#message').input_value()
                    # A real reload, not fragment-only navigation, restores default UI.
                    page.reload()
                    page.goto(url);page.wait_for_function("() => document.querySelector('#connection').textContent === 'Panel ulangan'")
                    for width in (390,768):
                        page.set_viewport_size({'width':width,'height':844});page.screenshot(path=str(output/('mobile.png' if width==390 else 'tablet.png')),full_page=True)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),width
                        for tab in ('memory','profile','setup','chat'):
                            page.locator(f'[data-tab="{tab}"]').click()
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,tab)
                    assert not errors,errors
                    browser.close()
                    print(json.dumps({'ok':True,'viewports':[1440,390,768],'ui_errors':errors,'screenshots':str(output)}))
            finally:
                process.terminate();process.wait(timeout=15)

if __name__=='__main__':main()
