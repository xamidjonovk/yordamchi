import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from hermes_personal_agent.live_sessions import OpenAILiveSession, OpenAILiveError
from hermes_personal_agent.voice_service import Service, CallBridge


def test_live_transcripts_are_fragments_and_delegations_are_deduplicated():
    session = OpenAILiveSession(None)
    session.active = True
    for text in ['Ertaga ', 'qo‘ng‘iroq qil']:
        msg = session.translate({'type':'session.input_transcript.delta','delta':text})
        assert not msg.server_content.turn_complete
    event={'type':'session.delegation.created','delegation':{'id':'d1','target':'client'}}
    msg=session.translate(event)
    assert msg.tool_call.function_calls[0].args['new_input']=='Ertaga qo‘ng‘iroq qil'
    assert session.translate(event) is None
    assert session.translate({'type':'session.output_audio.delta','delta':base64.b64encode(bytes(960)).decode()}).data==bytes(960)


@pytest.mark.asyncio
async def test_provider_switch_preserves_gemini_and_refuses_active_call():
    service=Service.__new__(Service)
    service.call_lock=asyncio.Lock()
    service.call_task=None
    config={'voice_provider':'gemini','model':'gemini-3.8-live','voice':'Rasalgethi','openai_live_model':'gpt-live-1'}
    with patch('hermes_personal_agent.voice_service.CONFIG', config), \
         patch('hermes_personal_agent.voice_service.save_config',side_effect=config.update), \
         patch('hermes_personal_agent.live_sessions.openai_key',return_value='test-only'):
        assert (await service.set_voice_provider('openai'))['model']=='gpt-live-1'
        assert config['model']=='gemini-3.8-live' and config['voice']=='Rasalgethi'
        assert (await service.set_voice_provider('gemini'))['model']=='gemini-3.8-live'
        service.call_task=asyncio.create_task(asyncio.sleep(10))
        try:
            assert not (await service.set_voice_provider('openai'))['ok']
        finally:
            service.call_task.cancel()
            await asyncio.gather(service.call_task,return_exceptions=True)


@pytest.mark.asyncio
async def test_contact_delegation_cannot_execute_owner_tasks():
    bridge=CallBridge(None,222,is_owner=False,relay=AsyncMock())
    bridge.session=SimpleNamespace(send_tool_response=AsyncMock())
    call=SimpleNamespace(name='live_delegate',id='d1',args={'new_input':'Fayllarni o‘chir','history':[]})
    with patch('hermes_personal_agent.voice_service.run_task',new_callable=AsyncMock,
               return_value={'ok':True,'text':'{"message":""}'}) as run:
        await bridge.tool(call)
    assert run.await_count==1 and run.await_args.kwargs['learn'] is False
    bridge.relay.assert_not_awaited()
    assert not bridge.session.send_tool_response.await_args.kwargs['function_responses'][0].response['ok']
