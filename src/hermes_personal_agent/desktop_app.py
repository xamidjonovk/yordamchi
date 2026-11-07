"""Native desktop control panel. Closing the window never stops the agent."""
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from filelock import FileLock, Timeout

from .voice_common import APP_HOME


class DesktopApi:
    def __init__(self, local_home=None, remote_alias=None):
        self._home = Path(local_home or APP_HOME).resolve()
        from .desktop_config import load, validate
        config=load(self._home)
        config=validate(remote_alias or config['ssh_alias'],config['remote_wrapper'])
        self._remote = config['ssh_alias']
        self._remote_wrapper = config['remote_wrapper']
        self._window = None
        self._cache = {}
        self._refreshing = set()
        self._lock = threading.RLock()
        self._operation_lock = threading.Lock()
        self._operation = None
        self._files = {}

    def _run(self, command, *, input=None, timeout=35, local=False):
        env = dict(os.environ, HPA_HOME=str(self._home), PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
        result = subprocess.run(command, input=input, capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=timeout, env=env,
            creationflags=0x08000000 if os.name == 'nt' else 0)
        if result.returncode:
            raise RuntimeError((result.stderr.strip() or result.stdout.strip() or 'Buyruq bajarilmadi')[-500:])
        return result.stdout

    def _rpc(self, environment, action, args=None, timeout=35):
        if environment not in ('local', 'server'):
            raise ValueError('Noto‘g‘ri muhit')
        request = json.dumps({'action': action, 'args': args or {}}, ensure_ascii=False)
        if environment == 'local':
            command = [sys.executable, '-m', 'hermes_personal_agent.cli', 'desktop-rpc']
        else:
            command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=7', self._remote,
                       self._remote_wrapper + ' desktop-rpc']
        output = self._run(command, input=request, timeout=timeout)
        try:
            result = json.loads(output)
        except ValueError:
            raise RuntimeError('Xizmatdan noto‘g‘ri javob keldi. Ulanishni yangilang.') from None
        if isinstance(result, dict) and result.get('ok') is False:
            raise RuntimeError(result.get('error') or result.get('detail') or 'Amal bajarilmadi')
        return result

    def _refresh(self, environment):
        with self._lock:
            if environment in self._refreshing:
                return
            self._refreshing.add(environment)
        def work():
            try:
                data = self._rpc(environment, 'snapshot')
                record = {'data': data, 'error': None, 'time': time.time()}
            except Exception as exc:
                record = {'data': self._cache.get(environment, {}).get('data'),
                          'error': str(exc)[:400], 'time': time.time()}
            with self._lock:
                self._cache[environment] = record
                self._refreshing.discard(environment)
        threading.Thread(target=work, daemon=True).start()

    def _phase(self, phase, text, **extra):
        with self._lock:
            self._operation = {'phase': phase, 'text': text, 'updated_at': time.time(), **extra}

    def _check_idle(self, environment):
        state = self._rpc(environment, 'runtime')
        if (state.get('call') != 'idle' or state.get('owner_task_active') or state.get('owner_queue')
                or state.get('background_tasks') or state.get('running_jobs')):
            raise RuntimeError('Faol qo‘ng‘iroq yoki vazifa bor. Avval uni yakunlang.')
        return state

    def _wait(self, environment, ready):
        deadline = time.monotonic() + 70
        while time.monotonic() < deadline:
            state = self._rpc(environment, 'runtime', timeout=15)
            if (ready and state.get('ready')) or (not ready and not state.get('running')):
                return state
            time.sleep(1.2)
        raise RuntimeError('Xizmat kutilgan vaqtda tayyor bo‘lmadi. Jurnalni tekshiring.')

    def _stop(self, environment):
        if environment == 'server':
            self._run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=7', self._remote,
                'systemctl --user disable --now hermes-personal-agent.service'], timeout=65)
        else:
            self._run([sys.executable, '-m', 'hermes_personal_agent.cli', 'stop'], timeout=20)
        self._wait(environment, False)

    def _activate(self, target, start):
        try:
            other = 'server' if target == 'local' else 'local'
            if start:
                self._phase('checking', 'Faol qo‘ng‘iroq va vazifalar tekshirilmoqda…', target=target)
                target_state = self._check_idle(target)
                other_state = self._check_idle(other)
                for identity in ('owner_id', 'agent_id'):
                    if target_state.get(identity) and other_state.get(identity) and target_state[identity] != other_state[identity]:
                        raise RuntimeError('Muhitlar turli Telegram akkauntlariga bog‘langan. Sozlamalarni tekshiring.')
                if other_state.get('running'):
                    self._phase('stopping_other', 'Ikkinchi muhit to‘xtatilmoqda…', target=target)
                # Also disarm the other host's login/reboot startup.
                self._stop(other)
                if target_state.get('ready'):
                    self._phase('done', 'Yordamchi allaqachon ishlayapti.', target=target)
                    return
                # Preserve each host's knowledge, but never replay already seen owner commands.
                self._rpc(target, 'prepare-activation', {
                    'owner_seen_id': max(target_state.get('owner_seen_id', 0), other_state.get('owner_seen_id', 0)),
                    'owner_id': target_state.get('owner_id'), 'agent_id': target_state.get('agent_id')})
                self._phase('starting', 'Yordamchi ishga tushirilmoqda…', target=target)
                if target == 'local':
                    # Wait for the supervisor lock as well as the controller.
                    with FileLock(str(self._home / 'data/supervisor.lock'), timeout=40):
                        pass
                    self._run([sys.executable, '-m', 'hermes_personal_agent.cli', 'start'])
                else:
                    self._run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=7', self._remote,
                        'systemctl --user enable --now hermes-personal-agent.service'], timeout=65)
                self._phase('waiting', 'Telegram va ovoz xizmati ulanmoqda…', target=target)
                self._wait(target, True)
                self._phase('done', 'Yordamchi tayyor. Muloqotni boshlashingiz mumkin.', target=target)
            else:
                self._check_idle(target)
                self._phase('stopping', 'Yordamchi xavfsiz to‘xtatilmoqda…', target=target)
                self._stop(target)
                self._phase('done', 'Yordamchi to‘xtatildi.', target=target)
        except Exception as exc:
            self._phase('error', str(exc)[:500], target=target)
        finally:
            self._operation_lock.release()
            self._refresh('local')
            self._refresh('server')

    def invoke(self, action, args=None):
        args = args or {}
        try:
            if action == 'poll':
                for env in ('local', 'server'):
                    if time.time() - self._cache.get(env, {}).get('time', 0) > (4 if env == 'local' else 10):
                        self._refresh(env)
                with self._lock:
                    return {'ok': True, 'environments': dict(self._cache), 'operation': self._operation,
                            'refreshing': list(self._refreshing)}
            if action == 'refresh':
                self._refresh(args.get('environment', 'local'))
                return {'ok': True}
            environment = args.pop('environment', 'local')
            if environment not in ('local', 'server'):
                raise ValueError('Noto‘g‘ri muhit')
            if action in ('runtime-start', 'runtime-stop'):
                if not self._operation_lock.acquire(blocking=False):
                    raise RuntimeError('Boshqa boshqaruv amali bajarilmoqda. Kuting.')
                self._phase('checking', 'Muhitlar tekshirilmoqda…', target=environment)
                threading.Thread(target=self._activate, args=(environment, action == 'runtime-start'), daemon=True).start()
                return {'ok': True}
            if action == 'pick-file':
                import webview
                files = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False)
                if not files:
                    return {'ok': True, 'cancelled': True}
                path = Path(files[0]).resolve()
                token = uuid.uuid4().hex
                self._files[token] = path
                return {'ok': True, 'token': token, 'name': path.name, 'size': path.stat().st_size}
            if action == 'import-file':
                path = self._files.pop(args['token'], None)
                if path is None:
                    raise ValueError('Faylni qayta tanlang')
                if path.stat().st_size > 100 * 1024 * 1024:
                    raise ValueError('Fayl 100 MB dan kichik bo‘lsin')
                args = {'name': path.name, 'data': base64.b64encode(path.read_bytes()).decode('ascii')}
                result = self._rpc(environment, 'memory-upload', args, timeout=180)
            else:
                allowed = {'memory-text', 'memory-search', 'memory-source', 'memory-facts', 'memory-forget', 'memory-wiki-pages', 'memory-wiki-page',
                           'memory-resolve', 'agent', 'call', 'hangup', 'settings-save'}
                if action not in allowed:
                    raise ValueError('Noma’lum amal')
                result = self._rpc(environment, action, args, timeout=60)
            self._refresh(environment)
            return {'ok': True, 'result': result}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)[:500]}


def main():
    import webview
    lock = FileLock(str(APP_HOME / 'desktop.lock'))
    signal = APP_HOME / 'desktop-focus'
    try:
        lock.acquire(timeout=0)
    except Timeout:
        signal.touch()
        return
    api = DesktopApi()
    ui = Path(__file__).parent / 'desktop/index.html'
    window = webview.create_window('Shaxsiy yordamchi', url=str(ui), js_api=api,
        width=1440, height=940, min_size=(900, 650), background_color='#F5F6F8', text_select=True)
    api._window = window
    alive = threading.Event()
    alive.set()
    window.events.closed += lambda: alive.clear()
    window.events.closing += lambda: not (api._operation and api._operation.get('phase') not in ('done', 'error'))
    def focus_listener():
        last = signal.stat().st_mtime if signal.exists() else 0
        while alive.wait(1):
            if not alive.is_set():
                break
            modified = signal.stat().st_mtime if signal.exists() else 0
            if modified > last:
                window.restore()
                window.show()
                last = modified
            time.sleep(.5)
    threading.Thread(target=focus_listener, daemon=True).start()
    try:
        webview.start(gui='edgechromium', debug=False, icon=str(Path(__file__).parent / 'desktop/app.ico'))
    finally:
        alive.clear()
        lock.release()


if __name__ == '__main__':
    main()
