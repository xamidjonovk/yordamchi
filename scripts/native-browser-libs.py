"""Extract missing Chromium dependencies into this user's project, without sudo.

Uses the host's signed APT metadata, skips installed packages, never runs package
maintainer scripts, and never changes dpkg state or the system library paths.
"""
import os
import re
import shutil
import subprocess
import sysconfig
from pathlib import Path

if os.geteuid()==0:raise SystemExit('Use the dedicated non-root project account')
project=Path.home()/'hermes-personal'
root=project/'system-libs';packages=root/'packages';packages.mkdir(parents=True,exist_ok=True)
initial=['libatk1.0-0t64','libatk-bridge2.0-0t64','libcups2t64','libatspi2.0-0t64',
         'libxcomposite1','libxdamage1','libxfixes3','libxrandr2','libgbm1',
         'libcairo2','libpango-1.0-0','libasound2t64','fonts-liberation']
pending=list(initial);seen=set();needed=[]
while pending:
    name=pending.pop()
    if name in seen:continue
    seen.add(name)
    if not re.fullmatch(r'[a-z0-9][a-z0-9+.-]+',name):raise RuntimeError('Unexpected package name')
    installed=subprocess.run(['dpkg-query','-W','-f=${db:Status-Status}',name],capture_output=True,text=True)
    if installed.returncode==0 and installed.stdout=='installed':continue
    available=subprocess.run(['apt-cache','show',name],capture_output=True,text=True)
    if available.returncode or not available.stdout.strip():
        if name.endswith('t64'):pending.append(name[:-3]);continue
        raise RuntimeError('APT package unavailable: '+name)
    needed.append(name)
    deps=subprocess.check_output(['apt-cache','depends','--important',name],text=True)
    pending.extend(re.findall(r'^\s*(?:PreDepends|Depends): ([a-z0-9][a-z0-9+.-]+)\s*$',deps,re.M))
if needed:
    subprocess.run(['apt-get','download',*needed],cwd=packages,check=True)
    for package in packages.glob('*.deb'):subprocess.run(['dpkg-deb','--extract',str(package),str(root)],check=True)
multiarch=sysconfig.get_config_var('MULTIARCH')
library_path=':'.join(str(root/part/multiarch) for part in ['usr/lib','lib'])
environment=f'LD_LIBRARY_PATH="{library_path}"\n'
if (root/'etc/fonts').is_dir():environment+=f'FONTCONFIG_PATH="{root}/etc/fonts"\n'
environment+=f'XDG_DATA_DIRS="{root}/usr/share:/usr/local/share:/usr/share"\n'
(root/'environment').write_text(environment)
fonts=root/'usr/share/fonts';destination=Path.home()/'.local/share/fonts/hermes-private'
if fonts.is_dir():
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():destination.symlink_to(fonts,target_is_directory=True)
print('USER_ONLY_BROWSER_LIBRARIES_READY',len(needed))
