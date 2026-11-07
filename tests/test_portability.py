import json
from pathlib import Path

import pytest
from filelock import FileLock

from hermes_personal_agent import desktop_config, private_transfer
from hermes_personal_agent.desktop_app import DesktopApi


def test_desktop_uses_configured_remote(tmp_path, monkeypatch):
    desktop_config.save('new-vps', '~/agent/hpa', tmp_path)
    api=DesktopApi(tmp_path)
    calls=[]
    def run(command, **kwargs):
        calls.append(command)
        return json.dumps({'ok': True})
    monkeypatch.setattr(api,'_run',run)
    api._rpc('server','runtime')
    assert calls[0][-2:] == ['new-vps','~/agent/hpa desktop-rpc']


@pytest.mark.parametrize('alias,wrapper', [('-oProxyCommand=bad','~/agent/hpa'),('good','~/agent/hpa;id'),('good','~/../other/hpa')])
def test_desktop_rejects_shell_and_ssh_option_injection(alias,wrapper):
    with pytest.raises(ValueError): desktop_config.validate(alias,wrapper)


def test_private_transfer_refuses_supervisor_even_when_controller_offline(tmp_path, monkeypatch):
    state=tmp_path/'data';state.mkdir()
    monkeypatch.setattr(private_transfer,'STATE',state)
    monkeypatch.setattr(private_transfer,'control',lambda: (_ for _ in ()).throw(OSError()))
    with FileLock(str(state/'supervisor.lock')):
        with pytest.raises(ValueError,match='supervisor'):
            private_transfer.export_private(tmp_path/'backup.zip',confirm=True)


def test_coolify_compose_is_standby_and_has_persistent_volumes():
    path=Path(__file__).parents[1]/'compose.coolify.yaml'
    text=path.read_text(encoding='utf-8')
    assert 'HPA_AUTOSTART:-false' in text
    assert 'agent-data:/home/agent/.hpa' in text
    assert 'hermes-data:/home/agent/.hermes' in text
    assert '\n    ports:' not in text
