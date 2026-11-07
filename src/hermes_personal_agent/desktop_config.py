"""Local, non-secret desktop SSH destination configuration."""
import json
import os
import re
import tempfile
from pathlib import Path

from .voice_common import APP_HOME

DEFAULT_ALIAS = 'hermes-personal-vps'
DEFAULT_WRAPPER = '~/hermes-personal/hpa'


def validate(alias, wrapper):
    # ssh receives this as an argv item, but a leading dash is still an option.
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', alias):
        raise ValueError('SSH alias must contain only letters, digits, underscore, dot or hyphen')
    # The wrapper is interpreted by the remote shell; disallow all shell syntax.
    if not re.fullmatch(r'~/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+', wrapper) or any(
            component in {'.', '..'} for component in wrapper[2:].split('/')):
        raise ValueError('Remote wrapper must be a safe path beneath the remote home, for example ~/hermes-personal/hpa')
    return {'ssh_alias': alias, 'remote_wrapper': wrapper}


def load(home=None):
    path=Path(home or APP_HOME)/'desktop.json'
    data=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    return validate(data.get('ssh_alias',DEFAULT_ALIAS),data.get('remote_wrapper',DEFAULT_WRAPPER))


def save(alias, wrapper=DEFAULT_WRAPPER, home=None):
    data=validate(alias,wrapper); root=Path(home or APP_HOME); root.mkdir(parents=True,exist_ok=True)
    fd, name=tempfile.mkstemp(prefix='.desktop-',suffix='.tmp',dir=root)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(name,root/'desktop.json')
    finally:
        if os.path.exists(name): os.unlink(name)
    return data
