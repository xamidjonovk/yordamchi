"""Private Uzbek browser onboarding. No passwords or provider output are logged."""
import asyncio
import contextlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from filelock import FileLock, Timeout
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from .voice_common import APP_HOME, STATE, CONFIG, HERMES_HOME, find_hermes, save_config

PROVIDERS = {'openai-codex', 'anthropic'}
AUTH_HOSTS = {'auth.openai.com', 'claude.ai', 'console.anthropic.com', 'platform.claude.com'}

def private_json(path, value):
    from .wiki_store import atomic
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2))
    if os.name != 'nt': path.chmod(0o600)

def save_secret(name, value):
    from dotenv import set_key
    if not isinstance(value, str) or not 10 <= len(value.strip()) <= 500 or any(c in value for c in '\r\n\x00'):
        raise ValueError('Kalit qiymatini tekshiring')
    path = APP_HOME / '.env'
    with FileLock(str(path)+'.lock', timeout=10):
        set_key(str(path), name, value.strip())
        if os.name != 'nt': path.chmod(0o600)
    os.environ[name] = value.strip()

async def stop_process(process):
    if process.returncode is None:
        import psutil
        with contextlib.suppress(psutil.NoSuchProcess):
            for child in psutil.Process(process.pid).children(recursive=True):
                with contextlib.suppress(psutil.NoSuchProcess,psutil.AccessDenied):child.kill()
        with contextlib.suppress(ProcessLookupError):process.kill()
        await process.wait()

class SetupWizard:
    def __init__(self, client_factory=TelegramClient):
        self.client_factory = client_factory
        self.client = None
        self.telegram_lock = None
        self.phone = self.phone_hash = None
        self.pending_credentials=None
        self.telegram_phase='idle'
        self.expires = 0
        self.auth_process = self.auth_task = None
        self.auth = {'phase':'idle', 'urls':[], 'code':'', 'provider':''}
        self.lock = asyncio.Lock()

    def status(self):
        return {'hermes_installed':find_hermes().is_file(), 'auth':dict(self.auth),
                'telegram_phase': self.telegram_phase,
                'telegram_connected':bool(not self.client and CONFIG.get('owner_id') and CONFIG.get('agent_id') and (STATE/'telegram.json').exists()),
                'voice_mode':CONFIG.get('setup_voice_mode', 'browser'),
                'gemini_key_present':bool(os.environ.get('GEMINI_API_KEY')),
                'completed':bool(CONFIG.get('setup_completed')), 'provider':CONFIG.get('hermes_provider','openai-codex'),
                'ai_connected':bool(CONFIG.get('ai_connected')),'ai_verified':bool(CONFIG.get('ai_verified'))}

    async def ensure_stopped(self):
        from .desktop_rpc import runtime
        if (await asyncio.to_thread(runtime)).get('running'):
            raise ValueError('Sozlashdan oldin ishlayotgan Telegram xizmatini to‘xtating')

    async def configure(self, key, value):
        env=dict(os.environ,HERMES_HOME=str(HERMES_HOME),PYTHONUTF8='1')
        proc=await asyncio.create_subprocess_exec(str(find_hermes()),'config','set',key,value,
            stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL,env=env,
            creationflags=0x08000000 if os.name=='nt' else 0)
        try:
            await asyncio.wait_for(proc.wait(),30)
            if proc.returncode:raise ValueError('Hermes sozlamasi yozilmadi. Installerni qayta ochib tiklang')
        finally:
            await stop_process(proc)

    async def start_auth(self, provider, model, consent=False):
        async with self.lock:
            await self.ensure_stopped()
            if provider not in PROVIDERS or not isinstance(model,str) or not re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,120}', model):
                raise ValueError('Provayder yoki model noto‘g‘ri')
            if provider == 'anthropic' and consent is not True:
                raise ValueError('Claude Max va qo‘shimcha kreditlar shartini tasdiqlang')
            if self.auth_task and not self.auth_task.done(): raise ValueError('Avval joriy loginni tugating yoki bekor qiling')
            hermes=find_hermes()
            if not hermes.is_file(): raise ValueError('Hermes topilmadi. install.cmd orqali o‘rnatishni tugating')
            self.auth={'phase':'waiting','urls':[],'code':'','provider':provider}
            env=dict(os.environ,HERMES_HOME=str(HERMES_HOME),PYTHONUNBUFFERED='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
            # Do not borrow or refresh a login used by another application.
            for key,value in [('auth.adopt_external_logins','false')]:
                try:await self.configure(key,value)
                except Exception:
                    self.auth['phase']='error'
                    raise ValueError('Hermes tayyor emas. Installerni qayta ochib tiklang') from None
            args=[str(hermes),'auth','add',provider,'--type','oauth','--no-browser']
            self.auth_process=await asyncio.create_subprocess_exec(*args,stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT,env=env,
                creationflags=0x08000000 if os.name=='nt' else 0)
            self.auth_task=asyncio.create_task(self._read_auth(provider,model))
            return self.status()

    def parse_auth_output(self, text):
        text=re.sub(r'\x1b\[[0-9;]*m','',text)
        urls=[]
        for url in re.findall(r'https://[^\s<>"\x1b]+',text):
            url=url.rstrip(').,')
            if urlparse(url).hostname in AUTH_HOSTS and len(url)<4000 and url not in urls: urls.append(url)
        self.auth['urls']=urls[-3:]
        codes=re.findall(r'\b[A-Z0-9]{4}-[A-Z0-9]{4,5}\b',text)
        if codes:self.auth['code']=codes[-1]

    async def _read_auth(self, provider, model):
        process=self.auth_process
        async def consume():
            output=''
            while chunk:=await process.stdout.read(1024):
                output=(output+chunk.decode('utf-8',errors='replace'))[-16000:]
                self.parse_auth_output(output)
            await process.wait()
        try:
            await asyncio.wait_for(consume(),15*60)
            if process.returncode: self.auth['phase']='error';return
            # A successful CLI OAuth flow stored its own credential. Verify routing config too.
            for key,value in [('model.provider',provider),('model.default',model),('fallback_providers','[]')]:
                await self.configure(key,value)
            save_config({'hermes_provider':provider,'hermes_model':model,'ai_connected':True,'ai_verified':False})
            from .hermes_tasks import reset_session
            await asyncio.to_thread(reset_session)
            self.auth['phase']='connected'
        except asyncio.CancelledError: raise
        except Exception: self.auth['phase']='error'
        finally:
            await stop_process(process)
            self.auth['code']=''
            self.auth['urls']=[] if self.auth['phase']!='waiting' else self.auth['urls']

    async def auth_input(self, value):
        if self.auth.get('provider')!='anthropic' or not self.auth_process or self.auth_process.returncode is not None:
            raise ValueError('Faol Claude login so‘rovi yo‘q')
        if not isinstance(value,str) or not 1<=len(value)<=4000 or any(c in value for c in '\r\n\x00'): raise ValueError('Tasdiqlash kodini tekshiring')
        self.auth_process.stdin.write((value.strip()+'\n').encode());await self.auth_process.stdin.drain()
        return {'ok':True}

    async def cancel_auth(self):
        if self.auth_task and not self.auth_task.done():
            self.auth_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):await self.auth_task
        self.auth={'phase':'idle','urls':[],'code':'','provider':''}
        return {'ok':True}

    async def change_model(self, model):
        async with self.lock:
            await self.ensure_stopped()
            if not CONFIG.get('ai_connected') or self.auth.get('phase')=='waiting':raise ValueError('Avval hisobga kirishni tugating')
            if not isinstance(model,str) or not re.fullmatch(r'[a-zA-Z0-9_.:/-]{1,120}',model):raise ValueError('Model nomini tekshiring')
            await self.configure('model.default',model)
            save_config({'hermes_model':model,'ai_verified':False})
            return {'ok':True}

    async def disconnect_telegram(self):
        if self.client:
            with contextlib.suppress(Exception):await self.client.disconnect()
        self.client=None;self.phone=self.phone_hash=None
        self.pending_credentials=None;self.telegram_phase='idle'
        if self.telegram_lock:self.telegram_lock.release();self.telegram_lock=None

    async def telegram_code(self, data):
        async with self.lock:
            await self.disconnect_telegram();await self.ensure_stopped()
            api_id=str(data.get('api_id',''));api_hash=data.get('api_hash','');phone=data.get('phone','')
            if not api_id.isdigit() or not 1<=int(api_id)<2**31 or not re.fullmatch(r'[a-fA-F0-9]{32}',api_hash) or not re.fullmatch(r'\+[0-9]{7,15}',phone):
                raise ValueError('API ID, API Hash yoki xalqaro telefon raqamini tekshiring')
            self.telegram_lock=FileLock(str(STATE/'runtime.lock'),timeout=0)
            try:
                self.telegram_lock.acquire()
                self.client=self.client_factory(str(STATE/'telegram'),int(api_id),api_hash,
                    device_model='Yordamchi Setup',flood_sleep_threshold=0)
                await asyncio.wait_for(self.client.connect(),30)
                self.phone=phone;self.expires=time.monotonic()+600
                # Keep existing working credentials until login and owner validation both succeed.
                self.pending_credentials={'api_id':int(api_id),'api_hash':api_hash,'phone':phone}
                if await self.client.is_user_authorized():
                    me=await self.client.get_me()
                    if getattr(me,'phone',None) and str(me.phone).lstrip('+')!=phone.lstrip('+'):
                        raise ValueError('Bu nusxa boshqa yordamchi akkauntga ulangan. Uning telefonidan foydalaning yoki yangi alohida nusxa yarating')
                    self.telegram_phase='owner'
                    return {'phase':'owner'}
                sent=await self.client.send_code_request(phone)
                self.phone_hash=sent.phone_code_hash
                self.telegram_phase='code'
                return {'phase':'code'}
            except FloodWaitError as exc:
                await self.disconnect_telegram();raise ValueError(f'Telegram kutishni so‘radi: {exc.seconds} soniya') from None
            except ValueError:
                await self.disconnect_telegram();raise
            except Exception:
                await self.disconnect_telegram();raise ValueError('Telegramga ulanib bo‘lmadi. API va telefonni tekshiring; boshqa nusxani to‘xtating') from None

    async def telegram_verify(self, data):
        async with self.lock:
            if not self.client or time.monotonic()>self.expires:
                await self.disconnect_telegram();raise ValueError('Login vaqti tugadi. Kodni qayta so‘rang')
            code=data.get('code','');password=data.get('password','')
            if not isinstance(code,str) or not isinstance(password,str) or len(code)>12 or len(password)>300:raise ValueError('Kod yoki parol noto‘g‘ri')
            try:
                if not await self.client.is_user_authorized():
                    if password:await self.client.sign_in(password=password)
                    else:await self.client.sign_in(self.phone,code=code.replace(' ',''),phone_code_hash=self.phone_hash)
                self.telegram_phase='owner'
                return {'phase':'owner'}
            except SessionPasswordNeededError:
                self.telegram_phase='password';return {'phase':'password'}
            except FloodWaitError as exc:raise ValueError(f'Telegram: {exc.seconds} soniya kuting') from None
            except Exception:raise ValueError('Kod yoki ikki bosqichli parol noto‘g‘ri. Qayta tekshiring') from None

    async def telegram_owner(self, username):
        async with self.lock:
            if not isinstance(username,str) or not re.fullmatch(r'@?[A-Za-z][A-Za-z0-9_]{3,31}',username):raise ValueError('Asosiy Telegram username’ini kiriting')
            if not self.client or time.monotonic()>self.expires:
                await self.disconnect_telegram();raise ValueError('Avval Telegram loginini bajaring')
            try:
                me=await self.client.get_me();owner=await self.client.get_entity(username.lstrip('@'))
                if me.bot or getattr(owner,'bot',False) or not getattr(owner,'first_name',None) or me.id==owner.id:
                    raise ValueError('Asosiy va yordamchi akkauntlar ikki alohida inson akkaunti bo‘lsin')
                private_json(STATE/'telegram.json',self.pending_credentials)
                save_config({'agent_id':me.id,'agent_username':me.username or '',
                             'owner_id':owner.id,'owner_username':owner.username or username.lstrip('@')})
            except ValueError:raise
            except Exception:raise ValueError('Asosiy akkaunt topilmadi. Username va kontaktni tekshiring') from None
            await self.disconnect_telegram()
            return {'phase':'connected'}

    async def voice(self, mode, key=''):
        if mode not in {'browser','gemini'}:raise ValueError('Ovoz rejimini tanlang')
        await self.ensure_stopped()
        if mode=='gemini':
            if not isinstance(key,str) or len(key)>500 or any(c in key for c in '\r\n\x00'):raise ValueError('Gemini kalitini tekshiring')
            candidate=key.strip() or os.environ.get('GEMINI_API_KEY')
            if not candidate:raise ValueError('Gemini API kalitini kiriting')
            def verify():
                from google import genai
                with genai.Client(api_key=candidate) as client:
                    client.models.get(model=CONFIG['transcription_model'])
            try:await asyncio.wait_for(asyncio.to_thread(verify),30)
            except Exception:raise ValueError('Gemini kaliti yoki modelga kirish tekshirilmadi. Kalit va loyihani tekshiring') from None
            if key:save_secret('GEMINI_API_KEY',key)
        save_config({'setup_voice_mode':mode,'live_voice_enabled':mode=='gemini','voice_note_replies':mode=='gemini'})
        return {'ok':True,'mode':mode}

    async def finish(self, start_service=False):
        if self.client:raise ValueError('Telegram loginini tugating yoki bekor qiling')
        if self.auth_task and not self.auth_task.done():raise ValueError('AI loginini tugating yoki bekor qiling')
        if not CONFIG.get('ai_connected'):raise ValueError('Avval AI hisobini ulang va tasdiqlang')
        if not CONFIG.get('ai_verified'):raise ValueError('Yakunlashdan oldin AI javobini sinash tugmasini bosing')
        from .onboarding import install_skill
        await asyncio.to_thread(install_skill)
        save_config({'setup_completed':True})
        if start_service:
            if not CONFIG.get('owner_id'):raise ValueError('Avval Telegramni ulang')
            from .services import start
            return await asyncio.to_thread(start)
        return {'ok':True}

    async def close(self):
        await self.cancel_auth();await self.disconnect_telegram()
