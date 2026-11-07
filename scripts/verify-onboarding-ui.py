"""Real local API + simulated external account responses; never uses real logins."""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

class ReviewDirectory(tempfile.TemporaryDirectory):
    def cleanup(self):
        # Windows can retain a just-closed SQLite/WAL handle briefly after exit.
        for attempt in range(10):
            try:
                super().cleanup(); return
            except PermissionError:
                if attempt==9: raise
                time.sleep(.2)

def main():
    root=Path(__file__).resolve().parents[1];output=root/'.impeccable/review';output.mkdir(parents=True,exist_ok=True)
    with ReviewDirectory(prefix='hpa-onboarding-') as home:
        env=dict(os.environ,HPA_HOME=home,HERMES_HOME=home,HERMES_BIN=str(Path(home)/'missing'),PYTHONUTF8='1')
        with (Path(home)/'server.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([sys.executable,'-m','hermes_personal_agent.cli','web','--no-browser','--port','8799'],
                env=env,stdout=log,stderr=log,creationflags=0x08000000 if os.name=='nt' else 0)
            try:
                url=None
                for _ in range(100):
                    text=(Path(home)/'server.log').read_text(encoding='utf-8')
                    if '#token=' in text:url='http://127.0.0.1:8799/#token='+text.split('#token=',1)[1].split()[0];break
                    if process.poll() is not None:raise RuntimeError('Server failed')
                    time.sleep(.1)
                if not url:raise RuntimeError('No server URL')
                with sync_playwright() as p:
                    browser=p.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1080},reduced_motion='reduce')
                    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    external={'connected':False,'telegram':False,'verified':False,'auth':{'phase':'idle','urls':[],'code':'','provider':''}}
                    def status(route):
                        response=route.fetch();data=response.json();data['setup'].update(ai_connected=external['connected'],ai_verified=external['verified'],telegram_connected=external['telegram'],auth=external['auth']);route.fulfill(response=response,json=data)
                    def account(route):
                        action=route.request.url.rsplit('/',1)[1]
                        if action=='auth':external.update(connected=True,auth={'phase':'connected','urls':[],'code':'','provider':'openai-codex'});data={'ok':True}
                        elif action=='telegram-code':data={'phase':'code'}
                        elif action=='telegram-verify':data={'phase':'password' if route.request.post_data_json.get('code') else 'owner'}
                        elif action=='telegram-owner':external['telegram']=True;data={'phase':'connected'}
                        elif action=='test-ai':external['verified']=True;data={'ok':True,'text':'Salom! Sinov javobi.'}
                        elif action=='finish':data={'ok':True}
                        else:route.continue_();return
                        route.fulfill(json=data)
                    page.route('**/api/status',status);page.route('**/api/setup/*',account)
                    page.goto(url.replace('/#','/?setup=1#'));page.wait_for_function("() => document.querySelector('#connection').textContent==='Panel ulangan'")
                    page.locator('#view-setup').wait_for(state='visible');assert '?setup=1' in page.url and '#token=' not in page.url;page.locator('#w-name').fill('Dars ishtirokchisi');page.locator('#w-zone').fill('Asia/Tashkent')
                    page.screenshot(path=str(output/'wizard-profile.png'),full_page=True)
                    page.locator('#w-profile button[type=submit]').click();assert page.locator('#ai-next').is_disabled()
                    page.locator('#auth-start').click();page.locator('#ai-next').wait_for(state='visible');page.wait_for_function("() => !document.querySelector('#ai-next').disabled")
                    page.screenshot(path=str(output/'wizard-ai.png'),full_page=True);page.locator('#w-provider').select_option('anthropic');page.wait_for_function("() => document.querySelector('#ai-next').disabled");page.locator('#w-provider').select_option('openai-codex');page.wait_for_function("() => !document.querySelector('#ai-next').disabled");page.locator('#ai-next').click()
                    page.screenshot(path=str(output/'wizard-telegram.png'),full_page=True)
                    page.locator('#tg-api-id').fill('12345');page.locator('#tg-api-hash').fill('a'*32);page.locator('#tg-phone').fill('+15550001111');page.locator('#tg-connect button[type=submit]').click()
                    page.locator('#tg-verify').wait_for(state='visible');assert page.locator('#tg-api-hash').input_value()==''
                    page.locator('#tg-code').fill('12345');page.locator('#tg-verify button').click();page.locator('#tg-password-wrap').wait_for(state='visible');assert page.locator('#tg-code').input_value()==''
                    page.locator('#tg-password').fill('test-password');page.locator('#tg-verify button').click();page.locator('#tg-owner').wait_for(state='visible');assert page.locator('#tg-password').input_value()==''
                    page.locator('#tg-username').fill('@owner_example');page.locator('#tg-owner button').click();page.wait_for_function("() => !document.querySelector('#tg-next').disabled");page.locator('#tg-next').click()
                    page.locator('#w-voice button[type=submit]').click();page.locator('#setup-summary').wait_for(state='visible');assert page.locator('#finish-setup').is_disabled()
                    page.locator('#test-ai').click();page.wait_for_function("() => !document.querySelector('#finish-setup').disabled")
                    page.screenshot(path=str(output/'wizard-finish.png'),full_page=True)
                    page.locator('#finish-setup').click();page.locator('#view-dashboard').wait_for(state='visible')
                    page.locator('[data-tab=calendar]').click();page.locator('#calendar-grid button').first.wait_for()
                    page.locator('#job-at').fill('2030-12-20T15:30');page.locator('#job-text').fill('Python darsiga tayyorlanish');page.locator('#job-form button[type=submit]').click()
                    page.wait_for_function("() => document.querySelector('#all-jobs').textContent.includes('Python darsiga tayyorlanish')")
                    page.screenshot(path=str(output/'calendar.png'),full_page=True)
                    page.locator('[data-tab=dashboard]').click();page.wait_for_function("() => document.querySelector('#upcoming-jobs').textContent.includes('Python darsiga tayyorlanish')")
                    # The inbox data below is a synthetic local fixture, not a Telegram account.
                    import sqlite3
                    from contextlib import closing
                    with closing(sqlite3.connect(Path(home)/'data/message-inbox.sqlite3')) as db:
                        db.execute('INSERT OR IGNORE INTO inbox(id,chat_id,message_id,sender,text,at,reason) VALUES(?,?,?,?,?,?,?)',('sample:1',1,1,'Dars xabari (sinov)','Muhim: ertangi dars 18:00 da boshlanadi.','2026-11-07T09:00:00+05:00','Kalit so‘z: muhim'))
                        db.commit()
                    page.locator('[data-tab=dashboard]').click()
                    page.wait_for_function("() => document.querySelector('#important-messages').textContent.includes('ertangi dars')")
                    page.screenshot(path=str(output/'dashboard.png'),full_page=True)
                    for width in (390,768):
                        page.set_viewport_size({'width':width,'height':844})
                        for name in ('dashboard','calendar','setup'):
                            page.locator(f'[data-tab={name}]').click()
                            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,name)
                            page.screenshot(path=str(output/f'{name}-{width}.png'),full_page=True)
                    page.set_viewport_size({'width':390,'height':844})
                    for previous in (3,2,1,0):
                        page.locator(f'[data-prev="{previous}"]:visible').click()
                        if previous==1:page.locator('#w-provider').select_option('anthropic')
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),('wizard-step',previous)
                        page.screenshot(path=str(output/f'wizard-step-{previous}-390.png'),full_page=True)
                        if previous==1:page.locator('#w-provider').select_option('openai-codex')
                    assert not errors,errors
                    page.unroute_all(behavior='wait')
                    browser.close();print(json.dumps({'ok':True,'external_logins':'simulated','local_profile_voice_jobs':'real API','widths':[1440,390,768],'js_errors':errors}))
            finally:process.terminate();process.wait(timeout=15)

if __name__=='__main__':main()
