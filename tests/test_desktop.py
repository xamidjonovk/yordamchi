import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from hermes_personal_agent.desktop_app import DesktopApi
from hermes_personal_agent import desktop_rpc
from hermes_personal_agent.agent_store import Store


def test_snapshot_read_does_not_interrupt_running_jobs(tmp_path, monkeypatch):
    store = Store(tmp_path / 'scheduler.sqlite3')
    store.data['jobs'].append({'id': 'in-progress', 'status': 'running'})
    store.save()
    monkeypatch.setattr(desktop_rpc, 'STATE', tmp_path)
    assert desktop_rpc.scheduler_snapshot()['jobs'][0]['status'] == 'running'
    assert desktop_rpc.scheduler_snapshot()['jobs'][0]['status'] == 'running'


def test_switch_refuses_if_other_host_cannot_be_checked(tmp_path, monkeypatch):
    api = DesktopApi(tmp_path)
    def check(environment):
        if environment == 'server':
            raise RuntimeError('SSH unavailable')
        return {'ready': False}
    monkeypatch.setattr(api, '_check_idle', check)
    stop = Mock(); run = Mock()
    monkeypatch.setattr(api, '_stop', stop)
    monkeypatch.setattr(api, '_run', run)
    monkeypatch.setattr(api, '_refresh', Mock())
    api._operation_lock.acquire()
    api._activate('local', True)
    assert api._operation['phase'] == 'error'
    stop.assert_not_called(); run.assert_not_called()


def test_already_running_target_does_not_launch_duplicate(tmp_path, monkeypatch):
    api = DesktopApi(tmp_path)
    monkeypatch.setattr(api, '_check_idle', lambda env: {'ready': env == 'local', 'running': env == 'local'})
    stop = Mock(); run = Mock()
    monkeypatch.setattr(api, '_stop', stop)
    monkeypatch.setattr(api, '_run', run)
    monkeypatch.setattr(api, '_refresh', Mock())
    api._operation_lock.acquire()
    api._activate('local', True)
    stop.assert_called_once_with('server')
    run.assert_not_called()
    assert api._operation['phase'] == 'done'


def test_active_call_blocks_environment_switch(tmp_path, monkeypatch):
    api = DesktopApi(tmp_path)
    monkeypatch.setattr(api, '_rpc', lambda *a, **k: {'call': 'connected', 'running': True})
    with pytest.raises(RuntimeError, match='Faol'):
        api._check_idle('local')


def test_settings_reject_secret_paths_and_invalid_limits():
    with pytest.raises(ValueError):
        desktop_rpc.validate_settings({'openai_env_file': 'anything'})
    with pytest.raises(ValueError):
        desktop_rpc.validate_settings({'max_call_minutes': -1})
    with pytest.raises(ValueError):
        desktop_rpc.validate_settings({'semantic_enabled': 'false'})


def test_credentials_cannot_be_uploaded_under_renamed_temporary_path():
    with pytest.raises(ValueError, match='Maxfiy'):
        desktop_rpc.dispatch('memory-upload', {'name': 'auth.json', 'data': 'e30='})


def test_unknown_bridge_actions_are_rejected(tmp_path):
    api = DesktopApi(tmp_path)
    assert api.invoke('shell', {'command': 'anything'})['ok'] is False
    assert api.invoke('runtime-start', {'environment': 'untrusted'})['ok'] is False


def test_activation_checkpoint_preserves_history_and_never_moves_backwards(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop_rpc, 'STATE', tmp_path)
    monkeypatch.setattr(desktop_rpc, 'CONFIG', {'owner_id': 111, 'agent_id': 222})
    store = Store(tmp_path / 'scheduler.sqlite3')
    store.data['owner_seen_id'] = 50
    store.data['jobs'].append({'id':'keep', 'status':'scheduled'})
    store.save()
    for marker in (100, 10):
        desktop_rpc.dispatch('prepare-activation', {'owner_seen_id': marker, 'owner_id':111,'agent_id':222})
    result = desktop_rpc.scheduler_snapshot()
    assert result['owner_seen_id'] == 100
    assert result['jobs'][0]['id'] == 'keep'
    with pytest.raises(ValueError):
        desktop_rpc.dispatch('prepare-activation', {'owner_seen_id':200,'owner_id':999,'agent_id':222})
