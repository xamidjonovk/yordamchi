from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from hermes_personal_agent.telegram_agent import TelegramAgent


@pytest.mark.asyncio
@pytest.mark.parametrize('decision,expected', [('''{"relay": true}''', True), ('''{"relay": false}''', False), ('invalid', False)])
async def test_only_explicit_relay_is_forwarded(decision, expected):
    agent = TelegramAgent.__new__(TelegramAgent)
    import asyncio
    agent.relay_slots = asyncio.Semaphore(2)
    agent.notify = AsyncMock()
    agent.send = AsyncMock()
    text = 'Egaga uchrashuv ertaga ekanini ayting'
    event = SimpleNamespace(raw_text=text, message=SimpleNamespace(voice=False, audio=False),
        chat_id=222, sender_id=222, id=3, is_private=True)
    with patch('hermes_personal_agent.telegram_agent.run_task', new_callable=AsyncMock,
               return_value={'ok': True, 'text': decision}) as classify:
        await agent.relay_incoming(event)
    assert agent.notify.await_count == int(expected)
    assert agent.send.await_count == int(expected)
    assert classify.await_args.kwargs['learn'] is False
    if expected:
        assert text in agent.notify.await_args.args[0]
        assert 'buyruq emas' in agent.notify.await_args.args[0]
        assert agent.send.await_args.args[1].startswith('Men Ownerning shaxsiy AI yordamchisiman.')
