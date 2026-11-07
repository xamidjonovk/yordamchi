"""Local knowledge snapshots only: no OAuth, Telegram session or Gemini key."""
import json
import os
import re
import tempfile
from datetime import datetime,timezone
from pathlib import Path

from hermes_personal_agent.cli import backup
from hermes_personal_agent.voice_common import APP_HOME

directory=Path(os.environ.get('HPA_BACKUP_DIR') or APP_HOME/'backups').expanduser().resolve()
directory.mkdir(parents=True,exist_ok=True,mode=0o700)
name='knowledge-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.zip'
fd,temporary=tempfile.mkstemp(prefix='.snapshot-',suffix='.zip',dir=directory);os.close(fd)
temporary=Path(temporary)
try:
    backup(temporary)
    temporary.replace(directory/name)
finally:
    if temporary.exists():temporary.unlink()
snapshots=sorted(p for p in directory.iterdir() if p.is_file() and re.fullmatch(r'knowledge-\d{8}T\d{6}Z\.zip',p.name))
for obsolete in snapshots[:-7]:obsolete.unlink()
print(json.dumps({'ok':True,'backup':str(directory/name),'retention':7,'includes_credentials':False}))
