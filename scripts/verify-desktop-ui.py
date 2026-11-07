"""Headless Edge checks with a real Python bridge and an isolated knowledge store."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from playwright.async_api import async_playwright

from hermes_personal_agent.desktop_app import DesktopApi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.state/desktop-check'
OUT.mkdir(parents=True, exist_ok=True)
UI = (ROOT / 'src/hermes_personal_agent/desktop/index.html').as_uri()


async def attach(browser, api, size):
    page = await browser.new_page(viewport=size, device_scale_factor=1)
    async def invoke(action, args):
        return await asyncio.to_thread(api.invoke, action, args)
    await page.expose_function('desktopBridge', invoke)
    await page.add_init_script('window.pywebview={api:{invoke:(a,b)=>window.desktopBridge(a,b)}}')
    await page.goto(UI)
    await page.wait_for_function('state.environments.local?.data != null', timeout=40000)
    return page


async def main():
    errors = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(channel='msedge', headless=True)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / 'config.json').write_text(json.dumps({'owner_username':'example_owner',
                'agent_username':'example_assistant','semantic_enabled':False,'learning_enabled':False,
                'control_port':18991,'owner_style':'Hurmat bilan murojaat qil.'}))
            api = DesktopApi(home)
            original = api._rpc
            def sandbox_rpc(env, action, args=None, **kwargs):
                if env == 'server':
                    raise RuntimeError('Test server is intentionally offline')
                return original(env, action, args, **kwargs)
            api._rpc = sandbox_rpc
            page = await attach(browser, api, {'width':1440,'height':940})
            page.on('pageerror', lambda error: errors.append(str(error)))
            await page.get_by_role('link', name='Xotira', exact=True).click()
            await page.locator('#memory-title').fill('UI tekshiruvi')
            await page.locator('#memory-text').fill('Uchrashuvlar seshanba kuni bo‘ladi.')
            await page.wait_for_timeout(2500)
            assert await page.locator('#memory-title').input_value() == 'UI tekshiruvi'
            await page.get_by_role('button', name='Xotiraga saqlash', exact=True).click()
            await page.get_by_role('row').filter(has_text='UI tekshiruvi').wait_for(timeout=20000)
            await page.get_by_role('row').filter(has_text='UI tekshiruvi').click()
            await page.get_by_text('Uchrashuvlar seshanba kuni bo‘ladi.', exact=True).wait_for()
            await page.get_by_role('button', name='Qidiruvdan chiqarish').click()
            await page.get_by_role('button', name='Tasdiqlash', exact=True).click()
            await page.wait_for_function('!state.environments.local.data.sources.length', timeout=20000)
            malicious = '<img src=x onerror="window.__xss=1">'
            await asyncio.to_thread(api.invoke, 'memory-text', {'environment':'local','title':malicious,'text':'Oddiy matn'})
            await page.wait_for_function('state.environments.local.data.sources.length===1', timeout=20000)
            assert await page.locator('#page img').count() == 0
            assert await page.evaluate('window.__xss') is None
            input_file = home / 'input-notes.txt'
            input_file.write_text('Hujjat orqali qo‘shilgan test ma’lumoti.', encoding='utf-8')
            api._window = SimpleNamespace(create_file_dialog=lambda *a, **k: (str(input_file),))
            await page.get_by_role('button', name='Fayl tanlash', exact=True).click()
            await page.get_by_role('button', name='Qo‘shish', exact=True).click()
            await page.get_by_role('row').filter(has_text='input-notes.txt').wait_for(timeout=20000)
            await page.get_by_role('link', name='Sozlamalar', exact=True).click()
            await page.locator('#settings-max').fill('25')
            await page.get_by_role('button', name='O‘zgarishlarni saqlash', exact=True).click()
            await page.wait_for_function('state.environments.local.data.settings.max_call_minutes===25', timeout=20000)
            assert json.loads((home / 'config.json').read_text())['max_call_minutes'] == 25
            for route in ('tasks','calendar','memory','calls','settings','logs'):
                await page.goto(UI+'#'+route)
                await page.wait_for_function(f'state.page==="{route}"')
                await page.wait_for_timeout(200)
                assert await page.locator('h1').count() == 1
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            await page.close()
        actual = DesktopApi()
        page = await attach(browser, actual, {'width':1440,'height':940})
        page.on('pageerror', lambda error: errors.append(str(error)))
        await page.wait_for_function('state.environments.server != null', timeout=45000)
        local_control=page.locator('.runtime').first.locator('.runtime-controls button')
        await local_control.focus()
        await page.wait_for_timeout(6500)
        assert await local_control.evaluate('(button)=>button===document.activeElement'), 'Polling lost keyboard focus'
        await page.screenshot(path=str(OUT / 'overview-1440.png'))
        for route in ('tasks','calendar','memory','calls','settings','logs'):
            await page.get_by_role('link', name=({'tasks':'Vazifalar','calendar':'Kalendar','memory':'Xotira','calls':'Qo‘ng‘iroqlar','settings':'Sozlamalar','logs':'Faoliyat jurnali'})[route], exact=True).click()
            await page.wait_for_timeout(250)
            await page.screenshot(path=str(OUT / (route+'-1440.png')))
        await page.get_by_role('link', name='Boshqaruv stoli', exact=True).click()
        await page.set_viewport_size({'width':960,'height':750})
        await page.screenshot(path=str(OUT / 'overview-960.png'))
        assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        await browser.close()
    if errors:
        raise AssertionError(errors)
    print(json.dumps({'ui_checks':'passed','screenshots':str(OUT)}))


asyncio.run(main())
