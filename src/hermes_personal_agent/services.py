"""Per-instance process supervision and platform-native user service definitions."""
import json
import os
import platform
import plistlib
import subprocess
import sys
import time
from pathlib import Path

from filelock import FileLock, Timeout
from .voice_common import APP_HOME, STATE, control


def start():
    from importlib.util import find_spec
    if find_spec('ntgcalls') is None:
        raise ValueError('Telegram calls require: uv sync --extra calls. The web panel works without this extra.')
    marker=STATE/'supervisor-stop'
    if marker.exists():marker.unlink()
    python=Path(sys.executable)
    if os.name=='nt' and python.with_name('pythonw.exe').exists():python=python.with_name('pythonw.exe')
    subprocess.Popen([str(python),'-m','hermes_personal_agent.cli','supervisor'],
        env=dict(os.environ,HPA_HOME=str(APP_HOME)),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,creationflags=0x08000000 if os.name=='nt' else 0,
        start_new_session=os.name!='nt')
    return {'ok':True,'message':'Supervisor started; use hpa status'}


def stop():
    (STATE/'supervisor-stop').touch()
    try:return control('shutdown')
    except OSError:return {'ok':True,'message':'Service is not responding; supervisor stop requested'}


def supervise():
    try:
        with FileLock(str(STATE/'supervisor.lock'),timeout=0):
            child=None;failures=0;missing=0
            while not (STATE/'supervisor-stop').exists():
                try:
                    status=control();missing=0
                    if status.get('ready'):failures=0
                except OSError:
                    missing+=1
                    if child is not None and child.poll() is None and missing>=6:
                        # This Popen is our own dedicated child. Shut down its native worker tree.
                        import psutil
                        root=psutil.Process(child.pid)
                        for process in root.children(recursive=True):process.terminate()
                        child.terminate();child.wait(timeout=10);child=None
                    if child is None or child.poll() is not None:
                        failures+=1
                        if failures>5:raise RuntimeError('Service failed five consecutive starts; run hpa doctor')
                        with (STATE/'process.log').open('a',encoding='utf-8') as log:
                            child=subprocess.Popen([sys.executable,'-m','hermes_personal_agent.voice_service'],
                                env=dict(os.environ,HPA_HOME=str(APP_HOME)),stdin=subprocess.DEVNULL,
                                stdout=log,stderr=subprocess.STDOUT,
                                creationflags=0x08000000 if os.name=='nt' else 0)
                        missing=0
                time.sleep(5)
            try:control('shutdown')
            except OSError:pass
            if child and child.poll() is None:
                try:child.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    import psutil
                    for process in psutil.Process(child.pid).children(recursive=True):process.terminate()
                    child.terminate()
    except Timeout:return


def service_definition(system=None):
    system=system or platform.system();python=str(Path(sys.executable));home=str(APP_HOME)
    if system=='Linux':
        quote=lambda value:'"'+value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'
        return '[Unit]\nDescription=Hermes Personal Agent\nAfter=network-online.target\n\n[Service]\nType=simple\n'+\
            f'Environment=HPA_HOME={quote(home)}\nExecStart={quote(python)} -m hermes_personal_agent.cli supervisor\n'+\
            'Restart=on-failure\nRestartSec=10\nTimeoutStopSec=35\n\n[Install]\nWantedBy=default.target\n'
    if system=='Darwin':
        return plistlib.dumps({'Label':'uz.hermes.personal-agent','ProgramArguments':[python,'-m','hermes_personal_agent.cli','supervisor'],
            'EnvironmentVariables':{'HPA_HOME':home},'RunAtLoad':True,'KeepAlive':{'SuccessfulExit':False},
            'StandardOutPath':str(STATE/'launchd.log'),'StandardErrorPath':str(STATE/'launchd-error.log')}).decode()
    if system=='Windows':
        pythonw=str(Path(python).with_name('pythonw.exe'))
        command=f'"{pythonw}" -m hermes_personal_agent.cli supervisor'
        vb=lambda value:'"'+value.replace('"','""')+'"'
        return 'Set shell = CreateObject("WScript.Shell")\n'+\
            'shell.Environment("PROCESS")("HPA_HOME") = '+vb(home)+'\n'+\
            'shell.Run '+vb(command)+', 0, False\n'
    raise ValueError('Supported systems: Linux, macOS, Windows')


def install_service(enable=False):
    system=platform.system()
    if system=='Linux':target=Path.home()/'.config/systemd/user/hermes-personal-agent.service'
    elif system=='Darwin':target=Path.home()/'Library/LaunchAgents/uz.hermes.personal-agent.plist'
    elif system=='Windows':target=Path(os.environ['APPDATA'])/'Microsoft/Windows/Start Menu/Programs/Startup/Hermes Personal Agent.vbs'
    else:raise ValueError('Unsupported operating system')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(service_definition(system),encoding='utf-8')
    if enable:
        if system=='Linux':
            subprocess.run(['systemctl','--user','daemon-reload'],check=True)
            subprocess.run(['systemctl','--user','enable','--now','hermes-personal-agent.service'],check=True)
        elif system=='Darwin':subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(target)],check=True)
        else:start()
    return {'ok':True,'file':str(target),'enabled':enable}
