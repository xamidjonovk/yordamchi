"""Restricted JSON operator protocol, shared by the Windows panel and SSH host."""
import base64
import json
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path

from filelock import FileLock, Timeout

from .voice_common import APP_HOME, CONFIG, STATE, control

SETTING_KEYS = ('voice_provider', 'voice', 'openai_live_voice', 'hermes_model', 'max_call_minutes',
                'openai_live_max_minutes', 'semantic_enabled', 'learning_enabled', 'owner_style', 'language')


def controller(action='status', data=None, timeout=2):
    import urllib.request
    token = (STATE / 'control-token').read_text(encoding='utf-8').strip()
    request = urllib.request.Request(f"http://127.0.0.1:{CONFIG['control_port']}/{action}",
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'},
        data=json.dumps(data).encode() if data is not None else None,
        method='GET' if action == 'status' else 'POST')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def runtime():
    try:
        state = controller()
        state['running'] = True
        state['phase'] = 'running' if state.get('ready') else 'starting'
    except (OSError, ValueError):
        locked = False
        try:
            with FileLock(str(STATE / 'runtime.lock'), timeout=0):
                pass
        except Timeout:
            locked = True
        state = {'ready': False, 'running': locked, 'phase': 'starting' if locked else 'stopped', 'call': 'idle'}
    schedule = scheduler_snapshot()
    state['running_jobs'] = sum(job.get('status') == 'running' for job in schedule.get('jobs', []))
    state['owner_seen_id'] = schedule.get('owner_seen_id', 0)
    state['owner_id'] = CONFIG.get('owner_id')
    state['agent_id'] = CONFIG.get('agent_id')
    return state


def scheduler_snapshot():
    path = STATE / 'scheduler.sqlite3'
    if not path.exists():
        return {'jobs': [], 'missions': [], 'paused': False}
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=2) as db:
        row = db.execute('SELECT payload FROM runtime_state WHERE id=1').fetchone()
    return json.loads(row[0]) if row else {'jobs': [], 'missions': [], 'paused': False}


def validate_settings(data):
    if any(key not in SETTING_KEYS or key == 'voice_provider' for key in data):
        raise ValueError('Bu sozlamani o‘zgartirish mumkin emas')
    for key, value in data.items():
        if key in ('semantic_enabled', 'learning_enabled') and not isinstance(value, bool):
            raise ValueError('Noto‘g‘ri yoqish/o‘chirish qiymati')
        if key in ('max_call_minutes', 'openai_live_max_minutes') and (type(value) is not int or not 1 <= value <= 60):
            raise ValueError('Qo‘ng‘iroq muddati 1–60 daqiqa bo‘lsin')
        if key in ('voice', 'openai_live_voice', 'hermes_model', 'owner_style', 'language') and (
                not isinstance(value, str) or (key != 'owner_style' and not value.strip()) or len(value) > 2000):
            raise ValueError('Matn qiymatini tekshiring')
    return dict(data)


def update_settings(data):
    from .voice_common import save_config
    save_config(validate_settings(data))
    return {'ok': True}


def dispatch(action, args=None):
    args = args or {}
    if action == 'runtime':
        return runtime()
    if action == 'prepare-activation':
        from .agent_store import Store
        marker = args.get('owner_seen_id', 0)
        if type(marker) is not int or marker < 0:
            raise ValueError('Noto‘g‘ri suhbat belgisi')
        if args.get('owner_id') != CONFIG.get('owner_id') or args.get('agent_id') != CONFIG.get('agent_id'):
            raise ValueError('Muhitlar turli Telegram akkauntlariga bog‘langan')
        with FileLock(str(STATE / 'runtime.lock'), timeout=0):
            store = Store(STATE / 'scheduler.sqlite3')
            store.data['owner_seen_id'] = max(marker, store.data.get('owner_seen_id', 0))
            store.save()
        return {'ok': True}
    if action == 'snapshot':
        from .knowledge import Knowledge, scrub
        kb = Knowledge()
        schedule = scheduler_snapshot()
        sources = kb.sources()
        log = STATE / 'service.log'
        lines = []
        if log.exists():
            # Dashboard polling must not reread an unbounded service log during a call.
            with log.open('rb') as stream:
                stream.seek(0, 2)
                start = max(0, stream.tell() - 128 * 1024)
                stream.seek(start)
                tail = stream.read().decode('utf-8', errors='replace').splitlines()
                lines = (tail[1:] if start else tail)[-80:]
        return {'runtime': runtime(), 'jobs': schedule['jobs'], 'missions': schedule['missions'],
                'paused': schedule.get('paused', False), 'memory': kb.stats(), 'sources': sources,
                'settings': {key: CONFIG.get(key) for key in SETTING_KEYS},
                'owner': CONFIG['owner_username'], 'agent': CONFIG['agent_username'],
                'timezone': CONFIG['timezone'], 'logs': [scrub(line) for line in lines],
                'updated_at': datetime.now().astimezone().isoformat()}
    if action == 'settings-save':
        settings = dict(args)
        provider = settings.pop('voice_provider', None)
        if provider is not None and provider not in ('gemini', 'openai'):
            raise ValueError('Noma’lum ovoz provayderi')
        validate_settings(settings)
        if provider == 'openai':
            from .live_sessions import openai_key
            openai_key(CONFIG)
        if runtime().get('running'):
            return controller('agent', {'op': 'settings-update', 'settings': args}, timeout=10)
        else:
            if provider is not None:
                settings['voice_provider'] = provider
            from .voice_common import save_config
            save_config(settings)
        return {'ok': True}
    if action == 'memory-search':
        from .knowledge import Knowledge
        return Knowledge().search(str(args.get('query', '')), 30, use_semantic=False)
    if action == 'memory-source':
        from .knowledge import Knowledge
        row = Knowledge().source(str(args['id']))
        offset = max(0, int(args.get('offset', 0)))
        text = row['content']
        row.update(content=text[offset:offset + 20000], total_chars=len(text), next_offset=offset + 20000 if offset + 20000 < len(text) else None)
        return row
    if action == 'memory-facts':
        from .knowledge import Knowledge
        return {'facts': Knowledge().facts(str(args.get('query', '')), 100)}
    if action == 'memory-wiki-pages':
        from .knowledge import Knowledge
        return {'pages': Knowledge().wiki_pages()}
    if action == 'memory-wiki-page':
        from .knowledge import Knowledge
        return Knowledge().wiki_page(str(args.get('name', '')))
    if action == 'memory-text':
        from .knowledge import Knowledge
        title, text = str(args.get('title', '')).strip(), str(args.get('text', '')).strip()
        if not title or not text:
            raise ValueError('Sarlavha va ma’lumotni kiriting')
        return {'ok': True, **Knowledge().add_text(title, text, kind='note', trust='owner',
                                                uri='desktop:' + uuid.uuid4().hex)}
    if action == 'memory-upload':
        from .knowledge import Knowledge
        suffix = Path(str(args.get('name', 'document.txt'))).suffix.lower()
        original = Path(str(args.get('name', '')).replace('\\', '/')).name
        if suffix in ('.session', '.key', '.pem') or original.startswith('.env') or original in ('auth.json', 'telegram.json', 'control-token'):
            raise ValueError('Maxfiy faylni xotiraga qo‘shib bo‘lmaydi')
        content = base64.b64decode(args['data'], validate=True)
        if len(content) > CONFIG['max_document_mb'] * 1024 * 1024:
            raise ValueError('Fayl hajmi limitdan oshdi')
        if not original or original in ('.', '..'):
            raise ValueError('Noto‘g‘ri fayl nomi')
        directory = STATE / 'desktop-imports' / uuid.uuid4().hex
        directory.mkdir(parents=True)
        path = directory / original
        path.write_bytes(content)
        try:
            return {'ok': True, **Knowledge().ingest(path)}
        finally:
            path.unlink(missing_ok=True)
            directory.rmdir()
    if action == 'memory-forget':
        from .knowledge import Knowledge
        return Knowledge().forget(str(args['id']))
    if action == 'memory-resolve':
        from .knowledge import Knowledge
        return Knowledge().resolve(str(args['id']))
    if action == 'agent':
        allowed = {'schedule', 'cancel', 'unwatch', 'watch', 'pause', 'resume', 'voice-provider', 'settings-update'}
        if args.get('op') not in allowed:
            raise ValueError('Noma’lum boshqaruv amali')
        return controller('agent', args, timeout=15)
    if action in ('call', 'hangup'):
        if action == 'call' and args.get('chat'):
            return controller('agent', {'op': 'call', 'chat': args['chat'], 'purpose': args.get('purpose', '')}, timeout=15)
        return controller(action, timeout=15)
    raise ValueError('Noma’lum boshqaruv amali')


def main():
    import sys
    try:
        data = json.loads(sys.stdin.read())
        result = dispatch(data['action'], data.get('args'))
    except Exception as exc:
        from .knowledge import scrub
        result = {'ok': False, 'error': scrub(str(exc))[:400], 'error_type': type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False))
