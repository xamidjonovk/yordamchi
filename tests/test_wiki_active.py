import json
import zipfile
from pathlib import Path

from hermes_personal_agent.knowledge import Knowledge, LegacyKnowledge
from hermes_personal_agent import cli, desktop_rpc


def test_legacy_migration_is_readable_and_does_not_modify_old_database(tmp_path):
    old = tmp_path / 'knowledge.sqlite3'
    legacy = LegacyKnowledge(old, tmp_path)
    source = legacy.add_text('Person', 'Alice works at Acme.')['source_id']
    legacy.add_fact('Alice', 'employer', 'Acme', source, 'Alice works at Acme.')
    legacy.relate('Alice', 'works at', 'Acme', source, 'Alice works at Acme.')
    before = old.read_bytes()
    new = Knowledge(old, tmp_path)
    assert old.read_bytes() == before
    assert new.source(source)['content'] == 'Alice works at Acme.'
    assert new.facts('Alice')[0]['value'] == 'Acme'
    assert new.related('Alice')[0]['object'] == 'acme'
    assert 'Alice works at Acme.' in new.search('Alice')['results'][0]['text']
    page = next(p['name'] for p in new.wiki_pages() if p['name'] != 'index.md')
    assert source in new.wiki_page(page)['content']
    assert Knowledge(old, tmp_path).stats()['sources'] == 1


def test_backup_and_restore_preserve_file_vault(tmp_path, monkeypatch):
    home=tmp_path/'home'; data=home/'data'; data.mkdir(parents=True)
    kb=Knowledge(data_root=data)
    source=kb.add_text('Note','Project Orion launches in May.')['source_id']
    kb.add_fact('Orion','launch','May',source,'Project Orion launches in May.')
    monkeypatch.setattr(cli,'STATE',data); monkeypatch.setattr(cli,'APP_HOME',home)
    archive=tmp_path/'backup.zip'; cli.backup(archive)
    with zipfile.ZipFile(archive) as z:
        assert 'data/vault/manifest.json' in z.namelist()
        assert 'data/vault/raw/'+source+'/content.txt' in z.namelist()
        assert any(n.startswith('data/vault/wiki/') for n in z.namelist())
    other=tmp_path/'restore'; other.mkdir()
    monkeypatch.setattr(cli,'APP_HOME',other)
    monkeypatch.setattr(cli,'control',lambda: (_ for _ in ()).throw(OSError()))
    # connect() is tied to the module's STATE; restoration must not modify the source instance.
    import hermes_personal_agent.database as db
    target=other/'data'; target.mkdir()
    monkeypatch.setattr(db,'STATE',target)
    cli.restore(archive)
    restored=Knowledge(data_root=target)
    assert restored.facts('Orion')[0]['value']=='May'
    assert restored.source(source)['content']=='Project Orion launches in May.'


def test_wiki_paths_are_restricted_and_forgotten_content_is_excluded(tmp_path):
    kb=Knowledge(data_root=tmp_path)
    source=kb.add_text('A','Alice lives in Paris.')['source_id']
    kb.add_fact('Alice','city','Paris',source,'Alice lives in Paris.')
    assert kb.search('Paris')['results']
    kb.forget(source)
    assert not kb.search('Paris')['results']
    assert len(kb.wiki_pages()) == 1
    import pytest
    with pytest.raises(ValueError): kb.wiki_page('../raw/secret.md')


def test_desktop_exposes_wiki_pages(tmp_path, monkeypatch):
    kb=Knowledge(data_root=tmp_path)
    source=kb.add_text('Note','Alice lives in Paris.')['source_id']
    kb.add_fact('Alice','city','Paris',source,'Alice lives in Paris.')
    import hermes_personal_agent.knowledge as module
    monkeypatch.setattr(module,'Knowledge',lambda: kb)
    pages=desktop_rpc.dispatch('memory-wiki-pages')['pages']
    page=next(p for p in pages if p['name']!='index.md')
    assert source in desktop_rpc.dispatch('memory-wiki-page',{'name':page['name']})['content']


def test_concurrent_writers_preserve_all_sources(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    Knowledge(data_root=tmp_path)
    def write(number):
        return Knowledge(data_root=tmp_path).add_text('Note', 'unique text '+str(number))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(write,range(20)))
    assert len({r['source_id'] for r in results})==20
    assert Knowledge(data_root=tmp_path).stats()['sources']==20


async def test_memory_worker_puts_hermes_extracted_fact_in_wiki(tmp_path, monkeypatch):
    import asyncio
    from hermes_personal_agent import hermes_tasks, inbox
    kb=Knowledge(data_root=tmp_path)
    source=kb.add_text('Note','Alice works at Acme.')['source_id']
    monkeypatch.setattr(hermes_tasks,'knowledge',lambda: kb)
    monkeypatch.setattr(inbox,'scan',lambda _: [])
    monkeypatch.setitem(hermes_tasks.CONFIG,'learning_interval_seconds',0.01)
    async def fake_task(*args, **kwargs):
        return {'ok':True,'text':json.dumps({'facts':[{'entity':'Alice','attribute':'employer','value':'Acme','evidence':'Alice works at Acme.','confidence':0.95}],'relations':[]})}
    monkeypatch.setattr(hermes_tasks,'run_task',fake_task)
    worker=asyncio.create_task(hermes_tasks.memory_worker())
    try:
        async with asyncio.timeout(3):
            while not kb.facts('Alice'):
                await asyncio.sleep(0.01)
    finally:
        worker.cancel()
        await asyncio.gather(worker,return_exceptions=True)
    assert kb.facts('Alice')[0]['source_id']==source
    page=next(p['name'] for p in kb.wiki_pages() if p['name']!='index.md')
    assert 'Acme' in kb.wiki_page(page)['content']
