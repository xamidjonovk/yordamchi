"""Create a fresh, reviewed teaching repository WITHOUT private Git history."""
import argparse
import json
import subprocess
import zipfile
from pathlib import Path
from build_release import build
from privacy_scan import scan

def export(destination):
    root=Path(__file__).resolve().parents[1]
    destination=Path(destination).resolve()
    if destination.exists(): raise ValueError('Destination exists. Choose a new empty path; nothing was overwritten.')
    result=build(root)
    destination.mkdir(parents=True)
    with zipfile.ZipFile(result['archive']) as archive:
        for name in archive.namelist():
            relative=Path(*Path(name).parts[1:]);target=(destination/relative).resolve()
            if destination not in target.parents: raise ValueError('Unsafe archive path')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(name))
    audit=scan(destination)
    if not audit['ok']: raise ValueError('Public export scan failed')
    subprocess.run(['git','init','-b','main',str(destination)],check=True,capture_output=True)
    # No original author email, private remote, hooks, reflog or commit objects are copied.
    subprocess.run(['git','-C',str(destination),'add','.'],check=True,capture_output=True)
    import os
    env=dict(os.environ,GIT_AUTHOR_NAME='Project Contributors',GIT_AUTHOR_EMAIL='contributors@example.invalid',
             GIT_COMMITTER_NAME='Project Contributors',GIT_COMMITTER_EMAIL='contributors@example.invalid')
    subprocess.run(['git','-C',str(destination),'-c','commit.gpgsign=false','-c','core.hooksPath=/dev/null',
                    'commit','-m','Prepare portable personal assistant for learners'],check=True,env=env,capture_output=True)
    return {'repository':str(destination),'files':audit['files_checked'],'old_history_included':False,'published':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination');args=parser.parse_args()
    print(json.dumps(export(args.destination),indent=2))
