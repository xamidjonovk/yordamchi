"""Exercise the actual HTTP boundary, persistence, upload and task routing."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
import aiohttp
from aiohttp.test_utils import TestClient, TestServer
import pytest
from hermes_personal_agent import web_app, personalization
from hermes_personal_agent.knowledge import Knowledge

@pytest.fixture
async def panel(tmp_path, monkeypatch):
    config={**personalization.CONFIG, 'owner_name':'Test Owner', 'semantic_enabled':False}
    monkeypatch.setattr(personalization,'CONFIG',config)
    monkeypatch.setattr(personalization,'save_config',lambda v:config.update(v))
    runner=AsyncMock(return_value={'ok':True,'text':'Test answer'})
    kb=Knowledge(data_root=tmp_path/'data')
    app=web_app.create_app(token='unit-test-token',port=8787,task_runner=runner,knowledge=kb)
    async with TestClient(TestServer(app),headers={'Host':'127.0.0.1:8787','Authorization':'Bearer unit-test-token'}) as client:
        yield client,kb,runner

async def test_denies_missing_token_host_rebinding_and_cross_origin(panel):
    client,_,runner=panel
    r=await client.get('/api/sources',headers={'Authorization':''});assert r.status==401
    r=await client.get('/api/sources',headers={'Host':'attacker.example:8787'});assert r.status==403
    r=await client.post('/api/chat',json={'text':'Do a task'},headers={'Origin':'https://attacker.example'});assert r.status==403
    runner.assert_not_awaited()
    r=await client.get('/');assert r.status==200
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert r.headers['Cache-Control']=='no-store'

async def test_real_note_search_and_forget(panel):
    client,kb,_=panel
    r=await client.post('/api/note',json={'title':'Dars jadvali','text':'Python darsi juma kuni soat 18 da.'});assert r.status==200
    source=(await r.json())['source_id']
    r=await client.get('/api/search?q=Python');assert (await r.json())['results'][0]['source_id']==source
    r=await client.post('/api/forget',json={'id':source});assert r.status==400
    r=await client.post('/api/forget',json={'id':source,'confirm':True});assert r.status==200
    assert not kb.search('Python')['results']

async def test_upload_preserves_page_source_and_rejects_executables(panel):
    client,kb,_=panel
    data=aiohttp.FormData();data.add_field('file',b'Python course starts tomorrow.',filename='../../schedule.txt')
    r=await client.post('/api/upload',data=data);assert r.status==200
    source=kb.source((await r.json())['source_id']);assert source['title']=='schedule.txt'
    assert 'Python' in source['content']
    data=aiohttp.FormData();data.add_field('file',b'bad',filename='bad.exe')
    r=await client.post('/api/upload',data=data);assert r.status==400

async def test_profile_validation_and_context(panel):
    client,_,_=panel
    for data in [{'timezone':'bad/zone'},{'owner_id':123},{'owner_name':''},{'personal_context':'x'*6001}]:
        r=await client.post('/api/profile',json=data);assert r.status==400
    r=await client.post('/api/profile',json={'owner_name':'Learner','personal_context':'I teach Python','introduction':'I am your AI helper.'});assert r.status==200
    assert 'I teach Python' in personalization.context()
    assert 'AI helper' in personalization.introduction()

async def test_chat_executes_only_once_and_sanitizes_errors(panel):
    client,_,runner=panel
    entered=asyncio.Event();finish=asyncio.Event()
    async def slow(text): entered.set();await finish.wait();return {'ok':True,'text':'Done'}
    runner.side_effect=slow
    first=asyncio.create_task(client.post('/api/chat',json={'text':'Plan my day'}))
    await entered.wait()
    r=await client.post('/api/chat',json={'text':'duplicate'});assert r.status==409
    r=await client.post('/api/reset',json={});assert r.status==409
    finish.set();r=await first;assert (await r.json())['text']=='Done'
    runner.assert_awaited_once_with('Plan my day')
    runner.side_effect=RuntimeError('secret-provider-response')
    r=await client.post('/api/chat',json={'text':'next'});assert r.status==500
    assert 'secret-provider-response' not in await r.text()

async def test_validation_limits(panel):
    client,_,_=panel
    for path,body in [('chat',{'text':'x'*20001}),('note',{'title':'','text':'hi'}),('profile',[]),('learning',{'enabled':'yes'})]:
        r=await client.post('/api/'+path,json=body);assert r.status==400

def test_config_update_preserves_other_process_changes(tmp_path,monkeypatch):
    import json
    from hermes_personal_agent import voice_common
    path=tmp_path/'config.json'
    path.write_text(json.dumps({'owner_name':'New owner','voice':'New voice'}))
    monkeypatch.setattr(voice_common,'CONFIG_PATH',path)
    monkeypatch.setattr(voice_common,'CONFIG',{'owner_name':'Stale owner','voice':'Old voice'})
    voice_common.save_config({'owner_style':'Brief'})
    actual=json.loads(path.read_text())
    assert actual['owner_name']=='New owner' and actual['voice']=='New voice'
    assert actual['owner_style']=='Brief'

def test_explicit_hermes_path_never_falls_back(monkeypatch,tmp_path):
    from hermes_personal_agent import voice_common
    missing=tmp_path/'missing'
    monkeypatch.setenv('HERMES_BIN',str(missing))
    assert voice_common.find_hermes()==missing
