"""Private local message inbox and safe access to the existing durable scheduler."""
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from filelock import FileLock
from .database import connect
from .voice_common import CONFIG, STATE

class MessageInbox:
    def __init__(self, path=None):
        self.path=path or STATE/'message-inbox.sqlite3'
        with connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY,chat_id INTEGER,message_id INTEGER,sender TEXT,text TEXT,at TEXT,reason TEXT,seen INTEGER DEFAULT 0)')

    def add(self, chat_id, message_id, sender, text, at, reason):
        from .wiki_store import scrub
        with connect(self.path) as db:
            db.execute('INSERT OR IGNORE INTO inbox(id,chat_id,message_id,sender,text,at,reason) VALUES(?,?,?,?,?,?,?)',
                (f'{chat_id}:{message_id}',chat_id,message_id,str(sender)[:120],scrub(str(text))[:4000],at,str(reason)[:120]))
            db.execute('DELETE FROM inbox WHERE id NOT IN (SELECT id FROM inbox ORDER BY at DESC LIMIT 500)')

    def rows(self):
        with connect(self.path) as db:
            return [dict(row) for row in db.execute('SELECT * FROM inbox ORDER BY at DESC LIMIT 100')]

    def seen(self, identity):
        with connect(self.path) as db:db.execute('UPDATE inbox SET seen=1 WHERE id=?',(identity,))

    def capture(self, event):
        if not CONFIG.get('inbox_enabled') or getattr(event.message,'out',False):return
        text=(getattr(event,'raw_text','') or '').strip()
        if not text:return
        terms=[t.strip().casefold() for t in CONFIG.get('important_keywords','muhim,shoshilinch,urgent,tezkor').split(',') if t.strip()]
        hit=next((t for t in terms if t in text.casefold()),None)
        if hit or getattr(event,'mentioned',False):
            self.add(event.chat_id,event.id,str(event.sender_id),text,event.message.date.isoformat(),
                'Siz tilga olingansiz' if getattr(event,'mentioned',False) else 'Kalit so‘z: '+hit)

def snapshot():
    from .desktop_rpc import scheduler_snapshot, runtime
    schedule=scheduler_snapshot()
    return {'jobs':schedule['jobs'],'missions':schedule['missions'],'paused':schedule.get('paused',False),
        'messages':MessageInbox().rows(),'runtime':runtime(),'timezone':CONFIG['timezone'],
        'inbox_enabled':CONFIG.get('inbox_enabled',False),'important_keywords':CONFIG.get('important_keywords','muhim,shoshilinch,urgent,tezkor'),
        'now':datetime.now(ZoneInfo(CONFIG['timezone'])).isoformat()}

def change_job(data):
    from .desktop_rpc import runtime,controller
    op=data.get('op')
    if op not in {'schedule','cancel'}:raise ValueError('Noma’lum reja amali')
    if op=='schedule':
        if data.get('kind')=='call' and not CONFIG.get('live_voice_enabled',True):raise ValueError('Qo‘ng‘iroq uchun sozlash ustasida Gemini ovozini ulang')
        if data.get('local_at'):
            local=datetime.fromisoformat(data['local_at'])
            if local.tzinfo is not None:raise ValueError('Mahalliy sana va vaqtni tanlang')
            zone=ZoneInfo(CONFIG['timezone']);aware=local.replace(tzinfo=zone)
            if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)!=local or aware.utcoffset()!=local.replace(tzinfo=zone,fold=1).utcoffset():
                raise ValueError('Bu vaqt yozgi/qishki vaqt almashishiga to‘g‘ri keladi. Boshqa vaqt tanlang')
            data={**data,'at':aware.isoformat()}
        if data.get('kind') not in {'message','task','call'} or data.get('repeat','once') not in {'once','daily','weekly'}:raise ValueError('Reja turini tanlang')
        if not isinstance(data.get('text',''),str) or len(data.get('text',''))>4000:raise ValueError('Matn 4000 belgidan oshmasin')
        from .agent_store import parse_at,now
        if not isinstance(data.get('at'),str) or parse_at(data['at'])<=now():raise ValueError('Kelajakdagi sana va vaqtni tanlang')
    if runtime().get('running'):return controller('agent',data,timeout=10)
    # Never create a second Store writer while a supervisor starts the service.
    with FileLock(str(STATE/'supervisor.lock'),timeout=0),FileLock(str(STATE/'runtime.lock'),timeout=0):
        from .agent_store import Store
        store=Store()
        if op=='schedule':return {'ok':True,'job':store.schedule(data['kind'],data['at'],data.get('text',''),data.get('repeat','once'))}
        return {'ok':True,'job':store.cancel(str(data.get('id','')))}
