import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from telethon.errors import SessionPasswordNeededError
from hermes_personal_agent import setup_wizard as setup
from hermes_personal_agent import dashboard

@pytest.fixture
def wizard(tmp_path,monkeypatch):
    state=tmp_path/'data';state.mkdir()
    config={'hermes_provider':'openai-codex','owner_id':None,'agent_id':None}
    monkeypatch.setattr(setup,'APP_HOME',tmp_path);monkeypatch.setattr(setup,'STATE',state)
    monkeypatch.setattr(setup,'CONFIG',config);monkeypatch.setattr(setup,'save_config',config.update)
    client=SimpleNamespace(connect=AsyncMock(),disconnect=AsyncMock(),is_user_authorized=AsyncMock(return_value=False),
        send_code_request=AsyncMock(return_value=SimpleNamespace(phone_code_hash='private-code-hash')),
        sign_in=AsyncMock(),get_me=AsyncMock(return_value=SimpleNamespace(id=123,bot=False,username='assistant_example')),
        get_entity=AsyncMock(return_value=SimpleNamespace(id=456,bot=False,username='owner_example',first_name='Owner')))
    instance=setup.SetupWizard(client_factory=lambda *a,**k:client)
    instance.ensure_stopped=AsyncMock()
    return instance,client,state

@pytest.mark.asyncio
async def test_telegram_two_factor_and_owner_verification_without_secret_response(wizard):
    instance,client,state=wizard
    result=await instance.telegram_code({'api_id':'12345','api_hash':'a'*32,'phone':'+15550001111'})
    assert result=={'phase':'code'}
    assert not (state/'telegram.json').exists()
    status=json.dumps(instance.status())
    assert 'private-code-hash' not in status and 'a'*32 not in status and '+15550001111' not in status
    client.sign_in.side_effect=SessionPasswordNeededError(request=None)
    assert (await instance.telegram_verify({'code':'12345'}))['phase']=='password'
    client.sign_in.side_effect=None
    assert (await instance.telegram_verify({'password':'test-password'}))['phase']=='owner'
    assert (await instance.telegram_owner('@owner_example'))['phase']=='connected'
    assert instance.status()['telegram_connected']
    assert instance.client is None and instance.telegram_lock is None
    client.disconnect.assert_awaited_once()

@pytest.mark.asyncio
async def test_existing_other_phone_never_overwrites_credentials(wizard):
    instance,client,state=wizard
    (state/'telegram.json').write_text('{"keep":"original"}')
    client.is_user_authorized.return_value=True
    client.get_me.return_value.phone='15550002222'
    with pytest.raises(ValueError,match='boshqa'):
        await instance.telegram_code({'api_id':'123','api_hash':'a'*32,'phone':'+15550001111'})
    assert json.loads((state/'telegram.json').read_text())=={'keep':'original'}
    assert instance.client is None

@pytest.mark.asyncio
async def test_rejects_invalid_api_and_same_owner(wizard):
    instance,client,_=wizard
    with pytest.raises(ValueError):await instance.telegram_code({'api_id':'bad','api_hash':'bad','phone':'bad'})
    client.connect.assert_not_awaited()
    await instance.telegram_code({'api_id':'123','api_hash':'a'*32,'phone':'+15550001111'})
    client.get_entity.return_value.id=123
    with pytest.raises(ValueError,match='alohida'):await instance.telegram_owner('owner_example')
    assert instance.client is client
    client.get_entity.return_value.id=456
    assert (await instance.telegram_owner('owner_corrected'))['phase']=='connected'
    assert instance.client is None

@pytest.mark.asyncio
async def test_login_expiry_releases_session_lock(wizard):
    instance,client,_=wizard
    await instance.telegram_code({'api_id':'123','api_hash':'a'*32,'phone':'+15550001111'})
    instance.expires=0
    with pytest.raises(ValueError,match='vaqti'):await instance.telegram_verify({'code':'12345'})
    assert instance.client is None and instance.telegram_lock is None

@pytest.mark.asyncio
async def test_browser_voice_needs_no_key_and_disables_telegram_calls(wizard):
    instance,_,_=wizard
    result=await instance.voice('browser')
    assert result['mode']=='browser'
    assert setup.CONFIG['live_voice_enabled'] is False

@pytest.mark.asyncio
async def test_model_correction_needs_no_new_oauth_but_requires_new_probe(wizard):
    instance,_,_=wizard
    setup.CONFIG.update(ai_connected=True,ai_verified=True,hermes_model='old-model')
    instance.configure=AsyncMock()
    await instance.change_model('gpt-6.1-sol')
    instance.configure.assert_awaited_once_with('model.default','gpt-6.1-sol')
    assert setup.CONFIG['hermes_model']=='gpt-6.1-sol' and not setup.CONFIG['ai_verified']

def test_auth_parser_only_exposes_official_urls_and_device_code(wizard):
    instance,_,_=wizard
    instance.parse_auth_output('https://evil.example/login https://auth.openai.com/codex/device\nABCD-12345\naccess_token=private-value')
    assert instance.auth['urls']==['https://auth.openai.com/codex/device']
    assert instance.auth['code']=='ABCD-12345'
    assert 'private-value' not in json.dumps(instance.status())

@pytest.mark.asyncio
async def test_claude_requires_explicit_credit_acknowledgement(wizard):
    instance,_,_=wizard
    with pytest.raises(ValueError,match='kredit'):await instance.start_auth('anthropic','claude-sonnet-4-6',False)

@pytest.mark.asyncio
async def test_completed_auth_persists_selected_route_and_requires_model_probe(wizard,monkeypatch,tmp_path):
    instance,_,_=wizard
    executable=tmp_path/'hermes';executable.write_text('fixture')
    monkeypatch.setattr(setup,'find_hermes',lambda:executable)
    instance.configure=AsyncMock()
    launched=[]
    class Process:
        returncode=0
        stdout=SimpleNamespace(read=AsyncMock(side_effect=[b'https://auth.openai.com/codex/device ABCD-12345',b'']))
        async def wait(self):return 0
    async def create(*args,**kwargs):launched.append(args);return Process()
    monkeypatch.setattr(setup.asyncio,'create_subprocess_exec',create)
    from hermes_personal_agent import hermes_tasks
    monkeypatch.setattr(hermes_tasks,'reset_session',lambda:None)
    await instance.start_auth('openai-codex','gpt-6.1-terra')
    await instance.auth_task
    assert instance.auth['phase']=='connected'
    assert setup.CONFIG['hermes_provider']=='openai-codex' and setup.CONFIG['ai_connected']
    assert launched[0][1:]==('auth','add','openai-codex','--type','oauth','--no-browser')
    assert not instance.auth['code'] and not instance.auth['urls']
    with pytest.raises(ValueError,match='sinash'):await instance.finish()

def test_message_rules_idempotency_and_seen_state(tmp_path,monkeypatch):
    monkeypatch.setattr(dashboard,'CONFIG',{'inbox_enabled':True,'important_keywords':'muhim,urgent'})
    inbox=dashboard.MessageInbox(tmp_path/'inbox.sqlite3')
    event=SimpleNamespace(id=1,chat_id=2,sender_id=3,raw_text='Muhim: ertaga dars',mentioned=False,
        message=SimpleNamespace(out=False,date=SimpleNamespace(isoformat=lambda:'2026-11-07T10:00:00+05:00')))
    inbox.capture(event);inbox.capture(event)
    assert len(inbox.rows())==1
    inbox.seen('2:1');assert inbox.rows()[0]['seen']==1
    event.id=2;event.raw_text='oddiy xabar';inbox.capture(event)
    assert len(inbox.rows())==1
    event.message.out=True;event.raw_text='urgent outgoing';inbox.capture(event)
    assert len(inbox.rows())==1

def test_offline_schedule_does_not_overwrite_running_runtime(tmp_path,monkeypatch):
    from filelock import FileLock,Timeout
    from hermes_personal_agent import desktop_rpc
    monkeypatch.setattr(dashboard,'STATE',tmp_path)
    monkeypatch.setattr(desktop_rpc,'runtime',lambda:{'running':False})
    with FileLock(str(tmp_path/'runtime.lock')):
        with pytest.raises(Timeout):dashboard.change_job({'op':'cancel','id':'anything'})

def test_local_job_time_is_interpreted_in_profile_zone(monkeypatch):
    from hermes_personal_agent import desktop_rpc
    monkeypatch.setattr(dashboard,'CONFIG',{'timezone':'Asia/Tashkent','live_voice_enabled':True})
    monkeypatch.setattr(desktop_rpc,'runtime',lambda:{'running':True})
    captured=[]
    monkeypatch.setattr(desktop_rpc,'controller',lambda action,data,timeout:captured.append(data) or {'ok':True})
    dashboard.change_job({'op':'schedule','kind':'message','local_at':'2030-02-10T09:00','text':'Dars'})
    assert captured[0]['at']=='2030-02-10T09:00:00+05:00'

def test_inbox_backup_can_be_restored(tmp_path,monkeypatch):
    from hermes_personal_agent import cli
    home=tmp_path/'home';state=home/'data';state.mkdir(parents=True)
    inbox=dashboard.MessageInbox(state/'message-inbox.sqlite3')
    inbox.add(1,2,'Example','Test reminder','2026-11-07T09:00:00+05:00','Test fixture')
    monkeypatch.setattr(cli,'APP_HOME',home);monkeypatch.setattr(cli,'STATE',state)
    monkeypatch.setattr(cli,'control',lambda:(_ for _ in ()).throw(OSError()))
    archive=tmp_path/'backup.zip'
    cli.backup(archive)
    inbox.seen('1:2');assert inbox.rows()[0]['seen']==1
    cli.restore(archive)
    assert inbox.rows()[0]['seen']==0

@pytest.mark.asyncio
async def test_anthropic_runner_never_inherits_api_billing_key(monkeypatch):
    from hermes_personal_agent import hermes_tasks as tasks
    captured={}
    class Process:
        returncode=0
        async def communicate(self,prompt):return b'{"type":"result","exit_code":0,"text":"OK"}',b''
    async def launch(*args,**kwargs):captured.update(args=args,env=kwargs['env']);return Process()
    monkeypatch.setattr(tasks.asyncio,'create_subprocess_exec',launch)
    monkeypatch.setitem(tasks.CONFIG,'hermes_provider','anthropic')
    monkeypatch.setenv('ANTHROPIC_API_KEY','test-key')
    monkeypatch.setenv('ANTHROPIC_TOKEN','test-token')
    result=await tasks._run_task('probe','test',learn=False,source_trust='owner')
    assert result['ok']
    assert captured['args'][captured['args'].index('--provider')+1]=='anthropic'
    assert 'ANTHROPIC_API_KEY' not in captured['env'] and 'ANTHROPIC_TOKEN' not in captured['env']
