import json
import os
import sqlite3
import zipfile
from contextlib import closing

import pytest

from hermes_personal_agent import cli,private_transfer as transfer


def test_private_transfer_scopes_credentials_and_resets_host_paths(tmp_path,monkeypatch):
    home=tmp_path/'source';state=home/'data';state.mkdir(parents=True)
    hermes=tmp_path/'hermes';hermes.mkdir()
    (home/'config.json').write_text(json.dumps({'owner_id':123,'agent_id':456,'hermes_bin':'C:/old/hermes.exe','hermes_home':'C:/old/home'}))
    (home/'.env').write_text('GEMINI_API_KEY=fake-gemini-test-only\nUNRELATED_SECRET=must-stay-behind\n')
    (state/'telegram.json').write_text(json.dumps({'api_id':123,'api_hash':'fake-hash-test-only'}))
    with closing(sqlite3.connect(state/'telegram.session')) as db:
        db.execute('CREATE TABLE proof(value TEXT)');db.execute("INSERT INTO proof VALUES('session-preserved')");db.commit()
    with closing(sqlite3.connect(state/'knowledge.sqlite3')) as db:
        db.execute('CREATE TABLE agent_sessions(key TEXT,session_id TEXT)');db.execute("INSERT INTO agent_sessions VALUES('owner','old-host-session')");db.commit()
    (hermes/'auth.json').write_text(json.dumps({'version':1,'providers':{'openai-codex':{'tokens':{'access_token':'test-token'}},'unrelated':{'token':'must-stay-behind'}},'credential_pool':{'unrelated':[{'key':'must-stay-behind'}]}}))
    monkeypatch.setattr(transfer,'APP_HOME',home);monkeypatch.setattr(transfer,'STATE',state);monkeypatch.setattr(transfer,'HERMES_HOME',hermes)
    monkeypatch.setattr(cli,'APP_HOME',home);monkeypatch.setattr(cli,'STATE',state)
    monkeypatch.setattr(transfer,'control',lambda:(_ for _ in ()).throw(OSError()))
    archive=tmp_path/'private.zip'
    with pytest.raises(ValueError):transfer.export_private(archive)
    assert not archive.exists()
    transfer.export_private(archive,confirm=True)
    with zipfile.ZipFile(archive) as package:
        assert b'must-stay-behind' not in b''.join(package.read(n) for n in package.namelist())
        assert json.loads(package.read('hermes/auth.json'))['active_provider']=='openai-codex'
    dest=tmp_path/'destination';dest.mkdir();new_hermes=tmp_path/'new-hermes';new_hermes.mkdir()
    monkeypatch.setattr(transfer,'APP_HOME',dest);monkeypatch.setattr(transfer,'STATE',dest/'data');monkeypatch.setattr(transfer,'HERMES_HOME',new_hermes)
    result=transfer.import_private(archive,confirm=True,delete_source=True)
    assert not result['started'] and not archive.exists()
    config=json.loads((dest/'config.json').read_text())
    assert config['owner_id']==123 and config['hermes_bin']==config['hermes_home']==''
    with closing(sqlite3.connect(dest/'data/telegram.session')) as db:assert db.execute('SELECT value FROM proof').fetchone()[0]=='session-preserved'
    with closing(sqlite3.connect(dest/'data/knowledge.sqlite3')) as db:assert db.execute('SELECT count(*) FROM agent_sessions').fetchone()[0]==0
    if os.name!='nt':assert (new_hermes/'auth.json').stat().st_mode&0o777==0o600


def test_private_import_rejects_archive_paths_before_any_write(tmp_path,monkeypatch):
    home=tmp_path/'home';home.mkdir();hermes=tmp_path/'hermes';hermes.mkdir()
    monkeypatch.setattr(transfer,'APP_HOME',home);monkeypatch.setattr(transfer,'STATE',home/'data');monkeypatch.setattr(transfer,'HERMES_HOME',hermes)
    monkeypatch.setattr(transfer,'control',lambda:(_ for _ in ()).throw(OSError()))
    archive=tmp_path/'malicious.zip'
    with zipfile.ZipFile(archive,'w') as package:
        package.writestr('manifest.json',json.dumps({'type':'hermes-private-transfer','version':1}))
        for name in ['agent/config.json','agent/.env','agent/data/telegram.json','agent/data/telegram.session','hermes/auth.json']:
            package.writestr(name,'{}')
        package.writestr('agent/data/sources/../../../../escape.txt','bad')
    with pytest.raises(ValueError):transfer.import_private(archive,confirm=True)
    assert {p.name for p in (home/'data').iterdir()} <= {'runtime.lock','supervisor.lock'}
    assert not list(hermes.iterdir())


def test_private_export_refuses_running_instance(tmp_path,monkeypatch):
    monkeypatch.setattr(transfer,'control',lambda:{'ready':True})
    with pytest.raises(ValueError,match='Stop this instance'):transfer.export_private(tmp_path/'private.zip',confirm=True)
