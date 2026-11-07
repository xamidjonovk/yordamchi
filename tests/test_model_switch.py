import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from hermes_personal_agent import hermes_tasks as tasks


@pytest.mark.asyncio
async def test_model_change_starts_new_session_without_resuming_old():
    old = {'session_id': 'old', 'turns': 2, 'started': '2026-01-01T00:00:00+00:00'}
    captured = []
    class Process:
        returncode = 0
        async def communicate(self, prompt):
            return b'{"type":"result","session_id":"new","exit_code":0,"text":"OK"}\n', b''
    async def launch(*args, **kwargs):
        captured.extend(args)
        return Process()
    kb = SimpleNamespace(context=lambda task: '', add_text=lambda *a, **kw: {'source_id': 'test'})
    with patch.object(tasks, 'session_record', return_value=old), \
         patch.object(tasks, 'subscription_session', return_value=True), \
         patch.object(tasks, 'session_model', return_value='gpt-6.1-sol'), \
         patch.object(tasks, 'knowledge', return_value=kb), \
         patch.object(tasks, 'save_session') as save, \
         patch.object(tasks.asyncio, 'create_subprocess_exec', side_effect=launch), \
         patch.dict(tasks.CONFIG, {'hermes_model': 'gpt-6.1-terra'}):
        result = await tasks._run_task('test', 'owner', learn=True, source_trust='owner')
    assert result['ok']
    assert '--resume' not in captured
    assert captured[captured.index('--model') + 1] == 'gpt-6.1-terra'
    assert captured[captured.index('--reasoning') + 1] == 'low'
    save.assert_called_once_with('owner', 'new', None)
