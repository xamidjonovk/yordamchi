import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from telethon.tl.types import User, Channel
from hermes_personal_agent import voice_control
from hermes_personal_agent.voice_service import CallBridge, Service, live_config


def test_contact_prompt_does_not_expose_owner_tools():
    config = live_config(False)
    assert [f.name for f in config.tools[0].function_declarations] == ['relay_to_owner', 'end_call']
    assert 'Men Ownerning shaxsiy AI yordamchisiman' in config.system_instruction
    assert 'not the owner' in config.system_instruction
    assert 'hermes_task' in [f.name for f in live_config(True).tools[0].function_declarations]


def test_call_command_routes_recipient_and_purpose():
    with patch.object(voice_control, 'control', return_value={'ok': True}) as control:
        voice_control.main(['call', '--chat', '@example_contact', '--purpose', 'Salomlashish'])
    control.assert_called_once_with('agent', {'op': 'call', 'chat': '@example_contact', 'purpose': 'Salomlashish'})


@pytest.mark.asyncio
async def test_outgoing_call_is_bound_to_requested_user():
    service = Service.__new__(Service)
    service.owner_id = 111
    service.client = SimpleNamespace(get_entity=AsyncMock(return_value=User(id=222, first_name='Person')))
    service.calls = object()
    service.call_task = service.bridge = None
    service.call_lock = asyncio.Lock()
    service.agent = None
    with patch.object(CallBridge, 'run', new_callable=AsyncMock):
        result = await service.start_call(target='@person', reason='Discuss meeting')
        await service.call_task
    assert result['ok'] and 'not yet confirmed' in result['message']
    assert service.bridge.owner_id == 222 and not service.bridge.is_owner
    assert service.bridge.reason == 'Discuss meeting'


@pytest.mark.asyncio
async def test_bot_recipient_rejected_before_dialing():
    service = Service.__new__(Service)
    service.owner_id = 111
    service.client = SimpleNamespace(get_entity=AsyncMock(return_value=User(id=222, bot=True)))
    service.call_task = None
    service.call_lock = asyncio.Lock()
    with pytest.raises(ValueError):
        await service.start_call(target='@bot')
    assert service.call_task is None


@pytest.mark.asyncio
async def test_call_relay_only_sends_to_owner_and_deduplicates():
    relay = AsyncMock()
    bridge = CallBridge(None, 222, is_owner=False, relay=relay)
    bridge.session = SimpleNamespace(send_tool_response=AsyncMock())
    call = SimpleNamespace(name='relay_to_owner', id='1', args={'message': 'Ertaga uchrashamiz'})
    await bridge.tool(call)
    await bridge.tool(call)
    relay.assert_awaited_once_with(222, 'Ertaga uchrashamiz')
    assert bridge.session.send_tool_response.await_count == 2


@pytest.mark.asyncio
async def test_incoming_contact_call_uses_restricted_contact_bridge():
    service = Service.__new__(Service)
    service.owner_id = 111
    service.call_task = None
    service.agent = SimpleNamespace(store=SimpleNamespace(data={'paused': False}))
    service.start_call = AsyncMock(return_value={'ok': True})
    assert (await service.accept_incoming(222))['ok']
    assert service.start_call.await_args.kwargs['target'] == 222
    assert 'kiruvchi' in service.start_call.await_args.kwargs['reason']


@pytest.mark.asyncio
async def test_incoming_call_cannot_replace_active_call():
    service = Service.__new__(Service)
    service.call_task = asyncio.create_task(asyncio.sleep(10))
    service.start_call = AsyncMock()
    try:
        assert not (await service.accept_incoming(222))['ok']
        service.start_call.assert_not_awaited()
    finally:
        service.call_task.cancel()
        await asyncio.gather(service.call_task, return_exceptions=True)
