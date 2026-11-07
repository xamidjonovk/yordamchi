"""Authenticated, loopback-only browser dashboard; no Telegram login needed to open."""
import argparse
import asyncio
import contextlib
import hmac
import json
import secrets
import tempfile
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import unquote
from aiohttp import web
from .voice_common import CONFIG, HERMES, STATE
from .knowledge import Knowledge
from . import personalization

async def body(request):
    data = await request.json()
    if not isinstance(data, dict): raise ValueError('JSON object required')
    return data

ASSETS = Path(__file__).parent / 'web'
TOKEN_KEY = web.AppKey('token', str)
OPEN_TASK_KEY = web.AppKey('open_task', asyncio.Task)
MAX_UPLOAD = 10 * 1024 * 1024
UPLOAD_TYPES = {'.txt', '.md', '.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.tsv'}

def create_app(token=None, port=8787, task_runner=None, knowledge=None):
    from .setup_wizard import SetupWizard
    wizard=SetupWizard()
    token = token or secrets.token_urlsafe(32)
    kb = knowledge or Knowledge()
    origins = {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}
    hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
    busy = asyncio.Lock()
    session_key = 'web:' + uuid.uuid4().hex
    async def task(text):
        from .hermes_tasks import run_task
        return await run_task(text, session_key=session_key+':'+CONFIG.get('hermes_provider','openai-codex'))
    runner = task_runner or task

    @web.middleware
    async def guard(request, handler):
        # Host check also blocks DNS rebinding against localhost.
        if request.host not in hosts:
            raise web.HTTPForbidden(text='Host ruxsat etilmagan')
        origin = request.headers.get('Origin')
        if origin and origin not in origins:
            raise web.HTTPForbidden(text='Origin ruxsat etilmagan')
        if request.path.startswith('/api/'):
            supplied = request.headers.get('Authorization', '')
            if not hmac.compare_digest(supplied, 'Bearer ' + token):
                return web.json_response({'error':'Kirish havolasi kerak. hpa web buyrug‘ini qayta oching.'}, status=401)
        try:
            response = await handler(request)
        except (ValueError, KeyError, TypeError):
            response = web.json_response({'error':'Kiritilgan ma’lumot yoki fayl formati noto‘g‘ri.'}, status=400)
        except web.HTTPException:
            raise
        except Exception:
            # Provider exceptions can contain keys, paths or request bodies.
            response = web.json_response({'error':'Amal bajarilmadi. Sozlamalarni tekshiring; yuborilgan vazifani tekshirmasdan takrorlamang.'}, status=500)
        response.headers.update({'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff',
            'Referrer-Policy':'no-referrer', 'X-Frame-Options':'DENY',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"})
        return response

    app = web.Application(middlewares=[guard], client_max_size=MAX_UPLOAD+65536)
    app[TOKEN_KEY] = token

    async def index(request): return web.FileResponse(ASSETS/'index.html')
    async def asset(request):
        if request.match_info['name'] not in {'app.css','app.js','dashboard.js','wizard.js','display.ttf'}: raise web.HTTPNotFound()
        return web.FileResponse(ASSETS/request.match_info['name'])
    async def status(request):
        from .desktop_rpc import runtime
        state = await asyncio.to_thread(runtime)
        if wizard.client:state={**state,'running':False,'ready':False,'phase':'setup'}
        return web.json_response({'profile':personalization.profile(), 'memory':await asyncio.to_thread(kb.stats),
            'hermes_installed':HERMES.is_file(), 'telegram_configured':(STATE/'telegram.json').exists(),
            'service':{key:state.get(key) for key in ('ready','running','phase','call')},
            'busy':busy.locked(), 'learning_enabled':CONFIG.get('learning_enabled', True),'setup':wizard.status()})
    async def profile(request):
        if busy.locked(): return web.json_response({'error':'Avval joriy vazifa tugashini kuting.'},status=409)
        result = await asyncio.to_thread(personalization.update, await body(request))
        return web.json_response({'profile':result,'restart_telegram':True})
    async def sources(request): return web.json_response({'sources':await asyncio.to_thread(kb.sources, 100)})
    async def search(request):
        query=request.query.get('q','').strip()
        if not 1 <= len(query) <= 1000: raise ValueError()
        return web.json_response(await asyncio.to_thread(kb.search, query, 12, False))
    async def note(request):
        data=await body(request); title=data.get('title',''); text=data.get('text','')
        if not isinstance(title,str) or not isinstance(text,str) or not 1 <= len(title.strip()) <= 160 or not 1 <= len(text.strip()) <= 50000: raise ValueError()
        return web.json_response(await asyncio.to_thread(kb.add_text,title.strip(),text.strip(),
            kind='note',trust='owner',uri='web:note:'+uuid.uuid4().hex))
    async def upload(request):
        reader=await request.multipart(); field=await reader.next()
        if field is None or field.name!='file': raise ValueError()
        name=Path(unquote(field.filename or '').replace('\\','/')).name[:160]
        suffix=Path(name).suffix.lower()
        if suffix not in UPLOAD_TYPES: raise ValueError()
        # Random directory and fixed basename prevent traversal and symlink overwrite.
        with tempfile.TemporaryDirectory(prefix='hpa-upload-') as folder:
            target=Path(folder)/('document'+suffix); size=0
            with target.open('wb') as stream:
                while chunk:=await field.read_chunk():
                    size+=len(chunk)
                    if size>MAX_UPLOAD: raise web.HTTPRequestEntityTooLarge(max_size=MAX_UPLOAD,actual_size=size)
                    stream.write(chunk)
            from .documents import extract
            parts=await asyncio.to_thread(extract,target)
            text='\n\n'.join(value for _,value in parts)
            if not text.strip() or len(text)>CONFIG['max_document_chars']: raise ValueError()
            result=await asyncio.to_thread(kb.add_text,name,text,kind='file',trust='document',
                uri='web:upload:'+uuid.uuid4().hex,parts=parts)
        return web.json_response(result)
    async def forget(request):
        data=await body(request)
        if data.get('confirm') is not True: raise ValueError()
        return web.json_response(await asyncio.to_thread(kb.forget,str(data['id'])))
    async def chat(request):
        if wizard.auth.get('phase')=='waiting':return web.json_response({'error':'Avval AI loginini tugating.'},status=409)
        data=await body(request); text=data.get('text','')
        if not isinstance(text,str) or not 1 <= len(text.strip()) <= 20000: raise ValueError()
        if busy.locked(): return web.json_response({'error':'Bitta vazifa bajarilmoqda. Natijani kuting.'},status=409)
        async with busy:
            result=await runner(text.strip())
        if not result.get('ok'):
            return web.json_response({'error':'AI javob bermadi. Hermes loginini va tanlangan modelni tekshiring. Vazifa holatini tekshirmasdan takrorlamang.'},status=503)
        return web.json_response({'text':str(result.get('text',''))[:30000]})
    async def reset(request):
        nonlocal session_key
        if busy.locked(): return web.json_response({'error':'Vazifa tugashini kuting.'},status=409)
        session_key='web:'+uuid.uuid4().hex
        return web.json_response({'ok':True})
    async def learn(request):
        data=await body(request)
        if type(data.get('enabled')) is not bool: raise ValueError()
        from .voice_common import save_config
        await asyncio.to_thread(save_config,{'learning_enabled':data['enabled']})
        return web.json_response({'ok':True,'restart_telegram':True})
    async def lifecycle(request):
        if wizard.client or wizard.auth.get('phase')=='waiting':return web.json_response({'error':'Avval hisob sozlashini tugating yoki bekor qiling.'},status=409)
        op=request.match_info['action']
        from . import services
        if op not in {'start','stop'}: raise ValueError()
        if not (STATE/'telegram.json').exists():
            return web.json_response({'error':'Telegram hali ulanmagan. Sozlash ustasini ochib Telegram qadamini tugating.'},status=409)
        # Service lifecycle uses the existing instance locks, not the desktop's mandatory VPS switch.
        if op=='stop':
            from .desktop_rpc import runtime
            r=await asyncio.to_thread(runtime)
            if busy.locked() or r.get('call')!='idle' or r.get('owner_task_active') or r.get('running_jobs') or r.get('owner_queue'):
                return web.json_response({'error':'Faol ish bor. Tugashini kuting.'},status=409)
        result=await asyncio.to_thread(getattr(services,op))
        return web.json_response(result)

    async def setup_action(request):
        data=await body(request);action=request.match_info['action']
        if busy.locked():return web.json_response({'error':'Joriy AI vazifasi tugashini kuting.'},status=409)
        try:
            if action=='auth':result=await wizard.start_auth(data.get('provider'),data.get('model'),data.get('consent',False))
            elif action=='auth-input':result=await wizard.auth_input(data.get('code'))
            elif action=='model':result=await wizard.change_model(data.get('model'))
            elif action=='auth-cancel':result=await wizard.cancel_auth()
            elif action=='telegram-code':result=await wizard.telegram_code(data)
            elif action=='telegram-verify':result=await wizard.telegram_verify(data)
            elif action=='telegram-owner':result=await wizard.telegram_owner(data.get('username'))
            elif action=='telegram-cancel':await wizard.disconnect_telegram();result={'ok':True}
            elif action=='voice':result=await wizard.voice(data.get('mode'),data.get('key',''))
            elif action=='finish':result=await wizard.finish(data.get('start_service') is True)
            elif action=='test-ai':
                from .hermes_tasks import run_task
                if not CONFIG.get('ai_connected'):raise ValueError('Avval AI hisobiga kiring')
                async with busy:
                    result=await run_task('Respond with one short Uzbek greeting. Do not use any tools.',learn=False)
                if not result.get('ok'):raise ValueError('Model javobi olinmadi. Hisob va model nomini tekshiring')
                from .voice_common import save_config
                save_config({'ai_verified':True})
                result={'ok':True,'text':result.get('text','')[:500]}
            elif action=='preferences':
                keywords=data.get('keywords','')
                if not isinstance(keywords,str) or len(keywords)>500 or type(data.get('enabled')) is not bool:raise ValueError('Kalit so‘zlarni tekshiring')
                await wizard.ensure_stopped()
                from .voice_common import save_config
                save_config({'inbox_enabled':data['enabled'],'important_keywords':keywords})
                result={'ok':True}
            else:raise ValueError('Noma’lum sozlash qadami')
            return web.json_response(result)
        except ValueError as exc:return web.json_response({'error':str(exc)},status=400)

    async def dashboard(request):
        from .dashboard import snapshot
        data=await asyncio.to_thread(snapshot)
        if wizard.client:data['runtime'].update(running=False,ready=False,phase='setup')
        return web.json_response(data)

    async def jobs(request):
        if wizard.client:return web.json_response({'error':'Reja kiritishdan oldin Telegram loginini tugating yoki bekor qiling.'},status=409)
        from .dashboard import change_job
        try:return web.json_response(await asyncio.to_thread(change_job,await body(request)))
        except ValueError as exc:return web.json_response({'error':str(exc)},status=400)

    async def inbox(request):
        data=await body(request)
        from .dashboard import MessageInbox
        if data.get('op')=='seen':
            await asyncio.to_thread(MessageInbox().seen,str(data.get('id','')))
            return web.json_response({'ok':True})
        if data.get('op')=='sync':
            if not CONFIG.get('inbox_enabled'):raise ValueError('Xabarlar yig‘ilishini sozlash ustasida yoqing')
            from .desktop_rpc import controller
            try:return web.json_response(await asyncio.to_thread(controller,'agent',{'op':'dashboard-inbox'},20))
            except OSError:return web.json_response({'error':'Telegram xizmati ishlamayapti. Sozlashni tugatib ishga tushiring.'},status=409)
        raise ValueError('Noma’lum xabar amali')

    async def wizard_lifetime(application):
        import time
        async def expire():
            while True:
                await asyncio.sleep(30)
                async with wizard.lock:
                    if wizard.client and time.monotonic()>wizard.expires:await wizard.disconnect_telegram()
        task=asyncio.create_task(expire())
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):await task
        await wizard.close()
    app.cleanup_ctx.append(wizard_lifetime)

    app.add_routes([web.get('/',index),web.get('/assets/{name}',asset),web.get('/api/status',status),
        web.post('/api/profile',profile),web.get('/api/sources',sources),web.get('/api/search',search),
        web.post('/api/note',note),web.post('/api/upload',upload),web.post('/api/forget',forget),
        web.post('/api/chat',chat),web.post('/api/reset',reset),web.post('/api/learning',learn),
        web.post('/api/service/{action}',lifecycle),web.post('/api/setup/{action}',setup_action),
        web.get('/api/dashboard',dashboard),web.post('/api/jobs',jobs),web.post('/api/inbox',inbox)])
    return app

def main(argv=None):
    parser=argparse.ArgumentParser(description='Shaxsiy assistent — brauzer paneli')
    parser.add_argument('--port',type=int,default=8787); parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--setup',action='store_true',help='O‘zbekcha sozlash ustasini ochish')
    args=parser.parse_args(argv)
    if not 1024<=args.port<=65535: parser.error('Port 1024–65535 oralig‘ida bo‘lsin')
    app=create_app(port=args.port)
    async def started(application):
        query='?setup=1' if args.setup else ''
        url=f'http://127.0.0.1:{args.port}/{query}#token={application[TOKEN_KEY]}'
        print('Shaxsiy kirish havolasi (ulashmang): '+url,flush=True)
        if not args.no_browser: await asyncio.to_thread(webbrowser.open,url)
    # on_startup runs before listening; schedule browser opening after site startup.
    async def schedule(application):
        async def open_later():
            await asyncio.sleep(.5); await started(application)
        application[OPEN_TASK_KEY]=asyncio.create_task(open_later())
    async def cleanup(application):
        application[OPEN_TASK_KEY].cancel()
        with contextlib.suppress(asyncio.CancelledError): await application[OPEN_TASK_KEY]
    app.on_startup.append(schedule); app.on_cleanup.append(cleanup)
    web.run_app(app,host='127.0.0.1',port=args.port,access_log=None,print=None)
