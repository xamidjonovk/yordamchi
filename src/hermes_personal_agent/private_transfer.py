"""Explicit human-operated private migration. Credentials never enter Git or stdout."""
import json
import os
import sqlite3
import stat
import tempfile
import zipfile
from contextlib import closing
from functools import wraps
from pathlib import Path
from filelock import FileLock, Timeout

from dotenv import dotenv_values
from .voice_common import APP_HOME, STATE, HERMES_HOME, control


def require_stopped():
    try:
        if control().get('ready'):raise ValueError('Stop this instance before a private transfer')
    except OSError:pass


def exclusive_stopped(function):
    """Prevent a supervisor or service from starting during private transfer."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        STATE.mkdir(parents=True, exist_ok=True)
        try:
            with FileLock(str(STATE/'supervisor.lock'), timeout=0), FileLock(str(STATE/'runtime.lock'), timeout=0):
                require_stopped()
                return function(*args, **kwargs)
        except Timeout:
            raise ValueError('Stop the service and supervisor before private transfer') from None
    return wrapped


@exclusive_stopped
def export_private(path,confirm=False):
    if not confirm:raise ValueError('Private transfer includes login credentials; explicit confirmation is required')
    require_stopped()
    output=Path(path).expanduser().resolve()
    if output.exists():raise ValueError('Private archive already exists; choose a new path')
    if STATE in output.parents:raise ValueError('Keep the private archive outside indexed data folders')
    key=dotenv_values(APP_HOME/'.env').get('GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not key:raise ValueError('Gemini key is missing')
    raw=json.loads((HERMES_HOME/'auth.json').read_text(encoding='utf-8-sig'))
    provider=(raw.get('providers') or {}).get('openai-codex')
    pool=(raw.get('credential_pool') or {}).get('openai-codex')
    if not provider and not pool:raise ValueError('Hermes has no OpenAI Codex OAuth login to migrate')
    auth={'version':raw.get('version',1),'active_provider':'openai-codex','providers':{},'credential_pool':{}}
    if provider:auth['providers']['openai-codex']=provider
    if pool:auth['credential_pool']['openai-codex']=pool
    for name in ['telegram.json','telegram.session']:
        if not (STATE/name).is_file():raise ValueError('Telegram login is missing')
    output.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    try:
        # Create with private mode before any credentials are written.
        fd=os.open(output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'wb') as stream,tempfile.TemporaryDirectory() as temporary:
            from .cli import backup
            knowledge=Path(temporary)/'knowledge.zip';backup(knowledge)
            with closing(sqlite3.connect((STATE/'telegram.session').as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(Path(temporary)/'telegram.session')) as dest:
                src.backup(dest)
            with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json',json.dumps({'type':'hermes-private-transfer','version':1,'includes_credentials':True}))
                with zipfile.ZipFile(knowledge) as original:
                    for name in original.namelist():
                        if name=='manifest.json':continue
                        archive.writestr('agent/'+name,original.read(name))
                archive.writestr('agent/.env','GEMINI_API_KEY='+json.dumps(key)+'\n')
                archive.write(STATE/'telegram.json','agent/data/telegram.json')
                archive.write(Path(temporary)/'telegram.session','agent/data/telegram.session')
                archive.writestr('hermes/auth.json',json.dumps(auth))
                for name in ['MEMORY.md','USER.md']:
                    source=HERMES_HOME/'memories'/name
                    if source.is_file():archive.write(source,'hermes/memories/'+name)
    except BaseException:
        if output.exists():output.unlink()
        raise
    return {'ok':True,'archive':str(output),'includes_credentials':True,'providers':['openai-codex']}


@exclusive_stopped
def import_private(path,confirm=False,delete_source=False):
    if not confirm:raise ValueError('Explicit confirmation is required to import private login material')
    require_stopped()
    if (APP_HOME/'config.json').exists() or (STATE/'telegram.session').exists():
        raise ValueError('Destination is already configured; private import requires a fresh instance')
    source=Path(path).expanduser().resolve(strict=True)
    with zipfile.ZipFile(source) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        if manifest.get('type')!='hermes-private-transfer' or manifest.get('version')!=1:
            raise ValueError('Unsupported private transfer archive')
        if sum(i.file_size for i in archive.infolist())>5_000_000_000:raise ValueError('Archive exceeds 5 GB')
        names=archive.namelist()
        if len(set(names))!=len(names):raise ValueError('Duplicate archive entry')
        targets=[]
        required={'agent/config.json','agent/.env','agent/data/telegram.json','agent/data/telegram.session','hermes/auth.json'}
        if not required.issubset(names):raise ValueError('Private archive is incomplete')
        for item in archive.infolist():
            name=item.filename
            if name=='manifest.json':continue
            if '\\' in name or '..' in name.split('/') or name.startswith('/'):
                raise ValueError('Invalid private archive path')
            if stat.S_ISLNK(item.external_attr>>16):raise ValueError('Links are not allowed in a private archive')
            if name.startswith('agent/'):
                relative=name[6:];base=APP_HOME
                allowed=relative in {'config.json','.env','data/telegram.json','data/telegram.session','data/knowledge.sqlite3','data/scheduler.sqlite3','data/sessions.sqlite3'} or relative.startswith('inbox/') or any(relative.startswith('data/'+folder+'/') for folder in ['sources','wiki','downloads','vault'])
            elif name.startswith('hermes/'):
                relative=name[7:];base=HERMES_HOME
                allowed=relative in {'auth.json','memories/MEMORY.md','memories/USER.md'}
            else:raise ValueError('Unexpected private archive entry')
            target=(base/relative).resolve()
            if not allowed or base not in target.parents:raise ValueError('Invalid private archive path')
            targets.append((name,target))
        auth=json.loads(archive.read('hermes/auth.json'))
        if set(auth.get('providers',{}))-{'openai-codex'} or set(auth.get('credential_pool',{}))-{'openai-codex'}:
            raise ValueError('Only OpenAI Codex credentials may be imported')
        existing=HERMES_HOME/'auth.json'
        if existing.exists():
            previous=json.loads(existing.read_text(encoding='utf-8-sig'))
            if any(previous.get(k) for k in ['providers','credential_pool']):raise ValueError('Destination Hermes already has login credentials')
        # All names and credential scope are validated before the first write.
        for name,target in targets:
            if name.endswith('/'):continue
            data=archive.read(name)
            if name=='agent/config.json':
                config=json.loads(data);config.update(hermes_bin='',hermes_home='')
                data=json.dumps(config,ensure_ascii=False,indent=2).encode()
            target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            fd=os.open(target,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as stream:stream.write(data)
            if os.name!='nt':target.chmod(0o600)
    database=STATE/'knowledge.sqlite3'
    if database.exists():
        with closing(sqlite3.connect(database)) as db:
            if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Imported database integrity check failed')
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='agent_sessions'").fetchone():db.execute('DELETE FROM agent_sessions');db.commit()
    sessions=STATE/'sessions.sqlite3'
    if sessions.exists():
        with closing(sqlite3.connect(sessions)) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='agent_sessions'").fetchone():db.execute('DELETE FROM agent_sessions');db.commit()
    if delete_source:source.unlink()
    return {'ok':True,'home':str(APP_HOME),'credentials_imported':['Telegram','Gemini','OpenAI Codex OAuth'],
            'started':False,'next':'Regenerate install-skill, verify subscription, then start only this instance.'}
