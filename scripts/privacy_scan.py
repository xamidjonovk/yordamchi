"""Local publication gate. Reports locations/categories, never secret values.

Use --history for reachable Git objects, --private-root to compare known local
credentials without printing them. A clean scan is evidence, not a guarantee.
"""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

SKIP = {'.git', '.venv', '.validation', '.private-local', '.deployment', '.transfer',
        '.state', '__pycache__', 'dist', '.pytest_cache', '.impeccable'}
RULES = {
    'provider-key': r'\b(?:AIza[\w-]{30,}|sk-(?:proj-)?[\w-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'telegram-token': r'\b\d{8,12}:[A-Za-z0-9_-]{30,}',
    'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'phone': r'(?<!\w)\+998[\s-]*\d{2}[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}\b',
    'credential-assignment': r'''(?i)["']?(?:api_hash|access_token|refresh_token|password)["']?\s*[:=]\s*["'][A-Za-z0-9_./+\-=]{20,}["']''',
}
SENSITIVE_NAMES = {'telegram.json', 'auth.json', 'control-token', 'config.json', 'voice_config.json', '.env'}

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)

def known_values(roots):
    values = set()
    fields = {'api_hash', 'api_id', 'phone', 'owner_id', 'agent_id', 'owner_username', 'agent_username'}
    for root in roots:
        root = Path(root)
        for file in [root/'.env', root/'config.json', root/'voice_config.json', root/'data/telegram.json', root/'.state/telegram.json', root/'.state/telegram-credentials.json']:
            if not file.is_file(): continue
            raw = file.read_text(encoding='utf-8')
            if file.suffix == '.json':
                try:
                    for key, value in json.loads(raw).items():
                        if key in fields and value and len(str(value)) >= 5: values.add(str(value))
                except ValueError: pass
            else:
                for line in raw.splitlines():
                    if '=' in line and not line.lstrip().startswith('#'):
                        value=line.split('=', 1)[1].strip().strip('"\'')
                        if len(value) >= 12: values.add(value)
    return values

def inspect(data, location, known=()):
    text = data.decode('utf-8', errors='replace')
    findings=[]
    for label, pattern in RULES.items():
        for match in re.finditer(pattern, text):
            findings.append({'path': location, 'line': text.count('\n', 0, match.start())+1, 'kind': label})
    for value in known:
        if value.casefold() in text.casefold(): findings.append({'path': location, 'kind': 'known-private-value'})
    return findings

def scan(root, history=False, known=()):
    root=Path(root).resolve(); findings=[]; count=0
    if history:
        for line in git(root, 'rev-list', '--objects', '--all').decode().splitlines():
            oid, _, path=line.partition(' ')
            if not path or git(root, 'cat-file', '-t', oid).strip() != b'blob': continue
            count+=1; findings+=inspect(git(root, 'cat-file', 'blob', oid), oid[:12]+':'+path, known)
            if Path(path).name in SENSITIVE_NAMES or '.session' in Path(path).name:
                findings.append({'path': oid[:12]+':'+path, 'kind':'private-file'})
    else:
        design=root/'.impeccable/design.json'
        if design.is_file():
            count+=1;findings+=inspect(design.read_bytes(),'.impeccable/design.json',known)
        for directory,dirs,names in os.walk(root,followlinks=False):
            dirs[:]=[name for name in dirs if name not in SKIP and not name.endswith('.egg-info')]
            for name in names:
                file=Path(directory)/name;relative=file.relative_to(root)
                if file.is_symlink(): findings.append({'path':str(relative),'kind':'symlink'}); continue
                if file.name in SENSITIVE_NAMES or '.session' in file.name:
                    findings.append({'path':str(relative),'kind':'private-file'})
                count+=1; findings+=inspect(file.read_bytes(), str(relative), known)
    return {'files_checked':count,'findings':findings,'ok':not findings}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--history',action='store_true'); parser.add_argument('--private-root',action='append',default=[])
    args=parser.parse_args(); result=scan(args.root,args.history,known_values(args.private_root))
    print(json.dumps(result,indent=2)); raise SystemExit(0 if result['ok'] else 1)
