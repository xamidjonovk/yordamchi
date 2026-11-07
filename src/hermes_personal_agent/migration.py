"""Import the previous local project without modifying or deleting its files."""
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from contextlib import closing

from .knowledge import Knowledge
from .voice_common import APP_HOME,CONFIG_PATH,STATE,HERMES_HOME,save_config


def migrate_legacy(root,with_credentials=False):
    root=Path(root).expanduser().resolve(strict=True)
    if root==APP_HOME:raise ValueError('Source and destination must be different')
    if CONFIG_PATH.exists():raise ValueError('Destination is already configured; choose a new HPA_HOME')
    config=json.loads((root/'voice_config.json').read_text(encoding='utf-8'))
    save_config(config)
    previous=root/'.state'
    if (previous/'agent-state.json').exists():shutil.copy2(previous/'agent-state.json',STATE/'agent-state.json')
    if (previous/'downloads').exists():shutil.copytree(previous/'downloads',STATE/'downloads',dirs_exist_ok=True)
    if with_credentials:
        if (root/'.env').exists():shutil.copy2(root/'.env',APP_HOME/'.env')
        for filename in ['telegram.json','control-token']:
            if (previous/filename).exists():shutil.copy2(previous/filename,STATE/filename)
        if (previous/'telegram.session').exists():
            with closing(sqlite3.connect((previous/'telegram.session').as_uri()+'?mode=ro',uri=True)) as origin,closing(sqlite3.connect(STATE/'telegram.session')) as target:
                origin.backup(target)
    kb=Knowledge();count=0
    mappings=previous/'hermes-sessions.json'
    if mappings.exists() and (HERMES_HOME/'state.db').exists():
        with closing(sqlite3.connect((HERMES_HOME/'state.db').as_uri()+'?mode=ro',uri=True)) as db:
            db.row_factory=sqlite3.Row
            columns=[r[1] for r in db.execute('PRAGMA table_info(messages)')]
            for name,sid in json.loads(mappings.read_text()).items():
                if name.startswith('integration'):continue
                for row in db.execute('SELECT * FROM messages WHERE session_id=? AND role IN (\'user\',\'assistant\') ORDER BY id',(sid,)):
                    content=row['content'] or ''
                    if not isinstance(content,str):continue
                    if row['role']=='user' and content.startswith('Bu ') and 'Telegram shaxsiy AI agentidan topshiriq.' in content[:200] and '\n\n' in content:
                        content=content.split('\n\n',1)[1]
                    if not content.strip():continue
                    date=None
                    for column in ['timestamp','created_at']:
                        if column in columns and row[column]:
                            try:date=datetime.fromtimestamp(float(row[column]),timezone.utc).isoformat()
                            except (ValueError,TypeError):date=str(row[column])
                            break
                    kb.add_text('Imported '+row['role']+' conversation',content,kind='conversation',
                        uri=f"hermes:{sid}:{row['id']}",trust='owner' if row['role']=='user' and name.startswith('owner') else 'assistant',created_at=date)
                    count+=1
    for name in ['MEMORY.md','USER.md']:
        source=HERMES_HOME/'memories'/name
        if source.exists():kb.ingest(source)
    return {'ok':True,'destination':str(APP_HOME),'imported_messages':count,'credentials_copied':with_credentials,
            'note':'Stop the old instance before starting this one. Old Hermes sessions are archived for retrieval; new contexts start compact.'}
