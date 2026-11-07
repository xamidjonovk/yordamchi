import json
import os
import time
import zipfile
from datetime import timedelta
from pathlib import Path

import pytest

from hermes_personal_agent.knowledge import Knowledge
from hermes_personal_agent.agent_store import Store, now
from hermes_personal_agent import inbox
from hermes_personal_agent.services import service_definition


@pytest.fixture
def kb(tmp_path):
    return Knowledge(tmp_path/'knowledge.sqlite3',tmp_path)


def test_fact_conflict_requires_explicit_resolution(kb):
    first=kb.add_text('First','My employer is Alpha.',trust='owner')
    old=kb.add_fact('Owner','Employer','Alpha',first['source_id'],'My employer is Alpha.')
    second=kb.add_text('Correction','My employer is now Beta.',trust='owner')
    new=kb.add_fact('Owner','Employer','Beta',second['source_id'],'My employer is now Beta.')
    assert new['status']=='conflict'
    assert {f['value']:f['status'] for f in kb.facts()}=={'Alpha':'active','Beta':'conflict'}
    kb.resolve(new['id'])
    assert [f['value'] for f in kb.facts()]==['Beta']
    manifest=json.loads((kb.path/'manifest.json').read_text(encoding='utf-8'))
    assert next(f for f in manifest['facts'] if f['id']==old['id'])['status']=='superseded'


def test_fake_evidence_is_rejected(kb):
    source=kb.add_text('Actual','The meeting is on Friday.')
    with pytest.raises(ValueError):kb.add_fact('meeting','day','Sunday',source['source_id'],'The meeting is on Sunday.')
    with pytest.raises(ValueError):kb.relate('meeting','on','Sunday',source['source_id'],'Invented quote')


def test_unicode_search_and_context_budget(kb):
    kb.add_text('Uzbek',"O‘zbekiston bo‘yicha to‘lovlar jadvali.\n"*100)
    assert kb.search("O'zbekiston",use_semantic=False)['results']
    assert len(kb.context('jadval',budget=650))<=650
    assert '[source ' in kb.context('jadval',budget=650)
    assert kb.search('" OR * --',use_semantic=False)['results']==[]


def test_document_revisions_remain_auditable(kb,tmp_path):
    source=tmp_path/'report.txt';source.write_text('Alpha contract is active.')
    first=kb.ingest(source)
    assert kb.ingest(source)['duplicate']
    source.write_text('Beta contract is active.')
    second=kb.ingest(source)
    assert first['source_id']!=second['source_id']
    assert not kb.search('Alpha',use_semantic=False)['results']
    assert kb.source(first['source_id'])['content']=='Alpha contract is active.'
    restored=Knowledge(kb.path,tmp_path)
    assert restored.search('Beta',use_semantic=False)['results'][0]['source_id']==second['source_id']
    source.write_text('Alpha contract is active.')
    assert kb.ingest(source)['duplicate']
    assert kb.search('Alpha',use_semantic=False)['results']
    assert not kb.search('Beta',use_semantic=False)['results']


def test_relationships_find_two_hops(kb):
    source=kb.add_text('Links','Alice works at Alpha. Alpha owns Project Z.')
    kb.relate('Alice','works at','Alpha',source['source_id'],'Alice works at Alpha.')
    kb.relate('Alpha','owns','Project Z',source['source_id'],'Alpha owns Project Z.')
    links=kb.related('ALICE',2)
    assert len(links)==2
    assert any(r['object']=='project z' for r in links)
    kb.forget(source['source_id'])
    assert not kb.related('Alice',2)


def test_known_secret_shapes_do_not_enter_retrieval(kb):
    secret='AIza'+'z'*35
    kb.add_text('Credential mistake','api_key='+secret+'\nUseful business notes.')
    result=kb.search('Useful',use_semantic=False)['results'][0]['text']
    assert secret not in result and '[REDACTED_SECRET]' in result


def test_scheduler_refuses_stale_writer(tmp_path):
    path=tmp_path/'scheduler.sqlite3'
    first=Store(path);second=Store(path)
    second.schedule('call',(now()+timedelta(hours=1)).isoformat())
    with pytest.raises(RuntimeError):first.save()
    assert len(Store(path).data['jobs'])==1


def test_office_text_is_indexed_without_execution(kb,tmp_path):
    doc=tmp_path/'memo.docx'
    with zipfile.ZipFile(doc,'w') as archive:
        archive.writestr('word/document.xml','<w:document xmlns:w="word"><w:p><w:t>Invoice ZX421 is paid.</w:t></w:p></w:document>')
    result=kb.ingest(doc)
    assert kb.search('ZX421',use_semantic=False)['results'][0]['source_id']==result['source_id']
    from openpyxl import Workbook
    sheet=tmp_path/'numbers.xlsx';book=Workbook();book.active.append(['Project','Budget']);book.active.append(['Orion',4400]);book.save(sheet)
    kb.ingest(sheet)
    assert '4400' in kb.search('Orion',use_semantic=False)['results'][0]['text']


def test_inbox_import_is_incremental(kb,tmp_path,monkeypatch):
    monkeypatch.setattr(inbox,'APP_HOME',tmp_path)
    folder=tmp_path/'inbox';folder.mkdir();file=folder/'notes.txt';file.write_text('A uniquely identifiable meeting note.')
    os.utime(file,(time.time()-5,time.time()-5))
    assert inbox.scan(kb)[0]['status']=='indexed'
    assert inbox.scan(kb)==[]


def test_platform_service_files_are_parseable():
    assert 'ExecStart=' in service_definition('Linux')
    import plistlib
    assert plistlib.loads(service_definition('Darwin').encode())['ProgramArguments'][-1]=='supervisor'
    assert 'shell.Run' in service_definition('Windows')


def test_cli_backup_excludes_credentials(tmp_path,monkeypatch):
    from hermes_personal_agent import cli
    home=tmp_path/'home';data=home/'data';data.mkdir(parents=True)
    (home/'.env').write_text('GEMINI_API_KEY=secret')
    (data/'telegram.json').write_text('secret')
    (data/'control-token').write_text('secret')
    sources=data/'sources';sources.mkdir();(sources/'report.txt').write_text('actual knowledge')
    monkeypatch.setattr(cli,'APP_HOME',home);monkeypatch.setattr(cli,'STATE',data)
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(data/'knowledge.sqlite3')) as db:
        db.execute('CREATE TABLE proof(value TEXT)');db.execute("INSERT INTO proof VALUES('retained')");db.commit()
    output=tmp_path/'backup.zip';cli.backup(output)
    with zipfile.ZipFile(output) as archive:
        assert 'data/sources/report.txt' in archive.namelist()
        assert 'data/knowledge.sqlite3' in archive.namelist()
        assert not any(name in archive.namelist() for name in ['.env','data/telegram.json','data/control-token'])
        snapshot=tmp_path/'snapshot.sqlite3';snapshot.write_bytes(archive.read('data/knowledge.sqlite3'))
    with closing(sqlite3.connect(snapshot)) as db:assert db.execute('SELECT value FROM proof').fetchone()[0]=='retained'


def test_restore_rejects_unexpected_files_and_traversal(tmp_path,monkeypatch):
    from hermes_personal_agent import cli
    home=tmp_path/'home';home.mkdir()
    monkeypatch.setattr(cli,'APP_HOME',home)
    monkeypatch.setattr(cli,'control',lambda:(_ for _ in ()).throw(OSError()))
    for name in ['../outside.txt','.env','data/telegram.session']:
        archive=tmp_path/'bad.zip'
        with zipfile.ZipFile(archive,'w') as output:
            output.writestr('manifest.json',json.dumps({'version':1}))
            output.writestr(name,'malicious')
        with pytest.raises(ValueError):cli.restore(archive)
    assert not list(home.iterdir())


def test_learning_lease_recovers_without_second_restart(kb):
    kb.add_text('Note','The project identifier is ZY634.')
    claimed=kb.claim_learning()
    assert claimed
    with kb.lock:
        state=kb._load()
        next(j for j in state['jobs'] if j['id']==claimed['id'])['lease_at']='2000-01-01T00:00:00+00:00'
        kb._save(state)
    assert kb.claim_learning()['id']==claimed['id']
