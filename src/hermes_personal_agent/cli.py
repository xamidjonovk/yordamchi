"""Small cross-platform operator CLI. No user data or credentials are bundled."""
import argparse
import asyncio
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

from .voice_common import APP_HOME, STATE, CONFIG, HERMES, HERMES_HOME, control


def memory(argv):
    from .knowledge import Knowledge
    k=Knowledge();p=argparse.ArgumentParser(prog='hpa memory');s=p.add_subparsers(dest='op',required=True)
    s.add_parser('stats');s.add_parser('warmup');s.add_parser('attention');s.add_parser('retry-learning')
    for name in ['search','context']:
        a=s.add_parser(name);a.add_argument('query');a.add_argument('--limit',type=int,default=8)
    a=s.add_parser('ingest');a.add_argument('path')
    a=s.add_parser('ingest-text');a.add_argument('--title',required=True);a.add_argument('--file',required=True);a.add_argument('--uri',required=True)
    a=s.add_parser('source');a.add_argument('id');a.add_argument('--offset',type=int,default=0);a.add_argument('--limit',type=int,default=6000)
    a=s.add_parser('facts');a.add_argument('--query',default='')
    a=s.add_parser('add-fact')
    for field in ['entity','attribute','value','source','evidence']:a.add_argument('--'+field,required=True)
    a=s.add_parser('related');a.add_argument('entity');a.add_argument('--depth',type=int,default=2)
    a=s.add_parser('resolve');a.add_argument('id')
    a=s.add_parser('forget');a.add_argument('id')
    s.add_parser('wiki-pages')
    a=s.add_parser('wiki-page');a.add_argument('name')
    a=p.parse_args(argv)
    if a.op=='stats':return k.stats()
    if a.op=='wiki-pages':return {'pages':k.wiki_pages()}
    if a.op=='wiki-page':return k.wiki_page(a.name)
    if a.op in {'attention','retry-learning'}:
        if a.op=='retry-learning':return {'ok':True,'jobs_reset':k.retry_learning()}
        return k.attention()
    if a.op=='search':return k.search(a.query,a.limit)
    if a.op=='context':return {'context':k.context(a.query)}
    if a.op=='facts':return {'facts':k.facts(a.query)}
    if a.op=='source':
        row=k.source(a.id);text=row.pop('content');row.update(content=text[a.offset:a.offset+min(a.limit,20000)],total_chars=len(text),next_offset=a.offset+min(a.limit,20000))
        return row
    if a.op=='ingest':
        path=Path(a.path)
        if path.is_file():return k.ingest(path)
        results=[]
        for file in path.rglob('*'):
            if not file.is_file() or any(part.startswith('.') for part in file.relative_to(path).parts):continue
            try:results.append({'file':str(file),**k.ingest(file)})
            except (ValueError,OSError) as error:results.append({'file':str(file),'error':str(error)})
        return {'files':results}
    if a.op=='ingest-text':return k.add_text(a.title,Path(a.file).read_text(encoding='utf-8'),uri=a.uri,kind='file')
    if a.op=='add-fact':return k.add_fact(a.entity,a.attribute,a.value,a.source,a.evidence)
    if a.op=='related':return {'relations':k.related(a.entity,a.depth)}
    if a.op=='resolve':return k.resolve(a.id)
    if a.op=='forget':return k.forget(a.id)
    if a.op=='warmup':
        total=0
        while count:=k.embed_pending(32):total+=count
        return {'embedded':total,**k.stats()}


def doctor():
    from .voice_notes import ffmpeg_path
    from .knowledge import Knowledge
    report={'python':sys.version.split()[0],'platform':platform.platform(),'home':str(APP_HOME),
        'hermes_found':HERMES.is_file(),'telegram_configured':(STATE/'telegram.json').exists(),
        'gemini_key_present':bool(os.environ.get('GEMINI_API_KEY')),'owner_configured':bool(CONFIG.get('owner_id'))}
    try:report['ffmpeg']=ffmpeg_path()
    except RuntimeError:report['ffmpeg']=None
    if report['hermes_found']:
        provider=CONFIG.get('hermes_provider','openai-codex')
        r=subprocess.run([str(HERMES),'auth','status',provider],capture_output=True,text=True,timeout=20)
        report['ai_provider']=provider
        report['ai_login_connected']='logged in' in r.stdout.lower()
        if provider=='openai-codex':report['openai_subscription_connected']=report['ai_login_connected']
    report['memory']=Knowledge().stats()
    report['memory_backend']='llm-wiki'
    try:report['service']=control()
    except OSError:report['service']={'ready':False}
    return report


def backup(path):
    """Consistent SQLite snapshots plus knowledge files, excluding login/session material."""
    target=Path(path).expanduser().resolve()
    if any(STATE/name in target.parents for name in ('sources','downloads','vault')):
        raise ValueError('Place the backup outside indexed source/download folders')
    from filelock import FileLock
    with FileLock(str(STATE/'vault.lock'), timeout=30), tempfile.TemporaryDirectory() as temporary:
        root=Path(temporary)
        for source in STATE.glob('*.sqlite3'):
            with closing(sqlite3.connect(source)) as origin,closing(sqlite3.connect(root/source.name)) as dest:origin.backup(dest)
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json',json.dumps({'version':1,'includes_credentials':False}))
            if (APP_HOME/'config.json').exists():archive.write(APP_HOME/'config.json','config.json')
            for source in root.iterdir():archive.write(source,'data/'+source.name)
            for name in ['sources','wiki','downloads','vault']:
                directory=STATE/name
                if directory.exists():
                    for file in directory.rglob('*'):
                        if file.is_file() and not file.is_symlink() and not file.name.startswith('.tmp-'):
                            archive.write(file,'data/'+str(file.relative_to(STATE)).replace('\\','/'))
            inbox=APP_HOME/'inbox'
            if inbox.exists():
                for file in inbox.rglob('*'):
                    if file.is_file() and not file.is_symlink() and not any(part.startswith('.') for part in file.relative_to(inbox).parts) and file.suffix.lower() not in {'.session','.pem','.key'} and file.name not in {'auth.json','telegram.json','control-token'}:
                        archive.write(file,'inbox/'+str(file.relative_to(inbox)).replace('\\','/'))
    return {'ok':True,'backup':str(target),'includes_credentials':False}


def restore(path):
    try:
        if control().get('ready'):raise ValueError('Stop this instance before restoring')
    except OSError:pass
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate backup entry')
        if not json.loads(archive.read('manifest.json')).get('version')==1:raise ValueError('Unsupported backup format')
        if sum(item.file_size for item in archive.infolist())>5_000_000_000:raise ValueError('Backup exceeds 5 GB')
        for name in names:
            if '\\' in name or '..' in name.split('/') or name.startswith('/'):
                raise ValueError('Invalid backup path')
            target=(APP_HOME/name).resolve()
            if APP_HOME not in target.parents:raise ValueError('Invalid backup path')
            allowed=(name in {'manifest.json','config.json','data/knowledge.sqlite3','data/scheduler.sqlite3','data/sessions.sqlite3','data/message-inbox.sqlite3'} or
                     name.startswith('inbox/') or any(name.startswith('data/'+folder+'/') for folder in ['sources','wiki','downloads','vault']))
            if not allowed:raise ValueError('Unexpected file in knowledge backup')
        for name in names:
            if name=='manifest.json' or name.endswith('/'):continue
            target=APP_HOME/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
    # Hermes session IDs belong to the original gateway. Keep their source archive, start fresh on this host.
    from .database import connect
    with connect() as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='agent_sessions'").fetchone():db.execute('DELETE FROM agent_sessions')
    if (STATE/'sessions.sqlite3').exists():
        with connect(STATE/'sessions.sqlite3') as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='agent_sessions'").fetchone(): db.execute('DELETE FROM agent_sessions')
    return {'ok':True,'message':'Knowledge restored. Run setup for this host and install-skill to regenerate paths.'}


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    try:
        if argv and argv[0]=='setup' and '--terminal' not in argv:
            from .web_app import main as web_app
            web_app(['--setup',*argv[1:]]);return
        if argv==['setup','--terminal']:
            from .onboarding import setup
            setup();return
        if argv and argv[0]=='web':
            from .web_app import main as web_app
            web_app(argv[1:]);return
        elif argv and argv[0]=='desktop-rpc':
            from .desktop_rpc import main as desktop_rpc
            desktop_rpc();return
        elif argv and argv[0]=='desktop':
            from .desktop_app import main as desktop_app
            desktop_app();return
        elif argv and argv[0]=='telegram':
            from .voice_control import main as telegram
            result=telegram(argv[1:])
        elif argv and argv[0]=='memory':result=memory(argv[1:])
        else:
            p=argparse.ArgumentParser(prog='hpa',description='Your portable personal Telegram agent')
            s=p.add_subparsers(dest='op',required=True)
            s.add_parser('web',help='Open the private browser dashboard (hpa web --help)')
            for op in ['setup','serve','supervisor','start','stop','status','doctor','install-skill']:s.add_parser(op)
            a=s.add_parser('install-service');a.add_argument('--enable',action='store_true')
            a=s.add_parser('research');a.add_argument('url')
            a=s.add_parser('migrate-legacy');a.add_argument('path');a.add_argument('--with-credentials',action='store_true')
            a=s.add_parser('export-wiki');a.add_argument('destination');a.add_argument('--database',default=str(STATE/'knowledge.sqlite3'))
            a=s.add_parser('desktop-config');a.add_argument('--ssh-alias',required=True);a.add_argument('--remote-wrapper',default='~/hermes-personal/hpa')
            for op in ['export-private','import-private']:
                a=s.add_parser(op);a.add_argument('path');a.add_argument('--confirm-credentials',action='store_true')
                if op=='import-private':a.add_argument('--delete-source',action='store_true')
            for op in ['backup','restore']:s.add_parser(op).add_argument('path')
            a=p.parse_args(argv)
            if a.op=='setup':
                from .onboarding import setup
                setup();return
            if a.op=='serve':
                from .voice_service import serve
                serve();return
            if a.op=='supervisor':
                from .services import supervise
                supervise();return
            if a.op in {'start','stop','install-service'}:
                from . import services
                result=services.install_service(a.enable) if a.op=='install-service' else getattr(services,a.op)()
            elif a.op=='status':result=control();result['ok']=bool(result.get('ready'))
            elif a.op=='doctor':result=doctor()
            elif a.op=='install-skill':
                from .onboarding import install_skill
                result={'ok':True,'skill':install_skill()}
            elif a.op=='research':
                from .research import fetch
                from .knowledge import Knowledge
                result=fetch(a.url,Knowledge())
            elif a.op=='migrate-legacy':
                from .migration import migrate_legacy
                result=migrate_legacy(a.path,a.with_credentials)
            elif a.op=='export-wiki':
                from .wiki_migration import export_wiki
                result=export_wiki(a.database,a.destination)
            elif a.op=='desktop-config':
                from .desktop_config import save
                result={'ok':True,**save(a.ssh_alias,a.remote_wrapper)}
            elif a.op in {'export-private','import-private'}:
                from .private_transfer import export_private,import_private
                result=export_private(a.path,a.confirm_credentials) if a.op=='export-private' else import_private(a.path,a.confirm_credentials,a.delete_source)
            elif a.op=='backup':result=backup(a.path)
            elif a.op=='restore':result=restore(a.path)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if isinstance(result,dict) and result.get('ok') is False:raise SystemExit(1)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(json.dumps({'ok':False,'error':type(error).__name__,'detail':str(error)[:500]},ensure_ascii=False))
        raise SystemExit(1)


if __name__=='__main__':main()
