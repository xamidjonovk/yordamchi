"""Selectable live voice transports; task billing remains with Hermes."""
import asyncio
import base64
import contextlib
import json
import os
from types import SimpleNamespace as NS

import aiohttp
from dotenv import dotenv_values
from google import genai


class OpenAILiveError(RuntimeError):
    pass


def openai_key(config):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key and config.get('openai_env_file'):
        key = (dotenv_values(config['openai_env_file']).get('OPENAI_API_KEY') or '').strip()
    if not key:
        raise OpenAILiveError('missing_api_key')
    return key


def message(**kw):
    return NS(server_content=None, data=None, tool_call=None, go_away=None, **kw)


class OpenAILiveSession:
    input_rate = 24000

    def __init__(self, ws):
        self.ws = ws
        self.queue = asyncio.Queue(maxsize=500)
        self.closed = asyncio.Event()
        self.active = False
        self.history = []
        self.new_input = []
        self.delegations = set()
        self.usage = None

    async def send_realtime_input(self, *, audio):
        await self.ws.send_json({'type': 'session.input_audio.append',
                                 'audio': base64.b64encode(audio.data).decode('ascii')})

    async def send_client_content(self, *, turns, turn_complete=True):
        self.active = True
        text = ' '.join(p.get('text', '') for p in turns['parts'])
        await self.ws.send_json({'type': 'session.instructions.append', 'delegation_id': None,
                                 'content': text[:600]})

    async def send_tool_response(self, *, function_responses):
        for response in function_responses:
            text = json.dumps(response.response, ensure_ascii=False)
            # A Live context append is limited to 500 tokens. Keep each chunk small.
            for start in range(0, min(len(text), 1800), 400):
                await self.ws.send_json({'type': 'session.commentary.append',
                    'delegation_id': response.id, 'content': text[start:start + 400]})

    def translate(self, event):
        kind = event.get('type')
        if kind == 'error':
            raise OpenAILiveError(str(event.get('error', {}).get('code', 'api_error')))
        if kind == 'session.closed':
            self.usage = event.get('usage')
            self.closed.set()
            return message()
        if not self.active:
            return None
        if kind == 'session.output_audio.delta':
            msg = message()
            msg.data = base64.b64decode(event['delta'], validate=True)
            if len(msg.data) % 2:
                raise OpenAILiveError('unaligned_pcm')
            return msg
        if kind in ('session.input_transcript.delta', 'session.output_transcript.delta'):
            text = event.get('delta', '')
            is_input = kind == 'session.input_transcript.delta'
            self.history.append({'role': 'caller' if is_input else 'assistant', 'text': text})
            self.history = self.history[-100:]
            if is_input:
                self.new_input.append(text)
            content = NS(input_transcription=NS(text=text) if is_input else None,
                         output_transcription=None if is_input else NS(text=text),
                         turn_complete=False, interrupted=False)
            msg = message()
            msg.server_content = content
            return msg
        if kind == 'session.delegation.created':
            delegation = event['delegation']
            if delegation.get('target') != 'client' or delegation['id'] in self.delegations:
                return None
            self.delegations.add(delegation['id'])
            new_input = ''.join(self.new_input)
            self.new_input.clear()
            msg = message()
            msg.tool_call = NS(function_calls=[NS(id=delegation['id'], name='live_delegate',
                args={'new_input': new_input[-12000:], 'history': self.history[-40:]})])
            return msg
        return None

    async def pump(self):
        try:
            async for frame in self.ws:
                if frame.type == aiohttp.WSMsgType.TEXT:
                    msg = self.translate(json.loads(frame.data))
                    if msg is not None:
                        await self.queue.put(msg)
                    if self.closed.is_set():
                        return
                elif frame.type == aiohttp.WSMsgType.ERROR:
                    raise OpenAILiveError('websocket_error')
            if not self.closed.is_set():
                raise OpenAILiveError('connection_closed')
        except Exception as exc:
            await self.queue.put(exc)

    async def receive(self):
        while True:
            item = await self.queue.get()
            if isinstance(item, Exception):
                raise item
            if self.closed.is_set():
                raise OpenAILiveError('session_closed')
            yield item


@contextlib.asynccontextmanager
async def connect_voice(config, gemini_config):
    provider = config.get('voice_provider', 'gemini')
    if provider == 'gemini':
        client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
        try:
            async with client.aio.live.connect(model=config['model'], config=gemini_config) as session:
                yield session
        finally:
            await client.aio.aclose()
        return
    if provider != 'openai':
        raise ValueError('Unknown voice provider')
    instruction = str(gemini_config.system_instruction)
    instruction += ('\nFor actions or message relays, delegate to the client backend. '
                    'Do not claim actions succeeded until the backend confirms them. '
                    'The named Gemini-style functions in the instructions describe backend capabilities; '
                    'request client delegation rather than inventing function results.')
    async with aiohttp.ClientSession() as client:
        async with client.ws_connect('wss://api.openai.com/v1/live/sessions',
                headers={'Authorization': 'Bearer ' + openai_key(config)},
                heartbeat=20, max_msg_size=8 * 1024 * 1024) as ws:
            await ws.send_json({'type': 'session.start', 'session': {
                'model': config.get('openai_live_model', 'gpt-live-1'), 'instructions': instruction,
                'audio': {'format': {'type': 'audio/pcm', 'rate': 24000},
                          'output': {'voice': config.get('openai_live_voice', 'marin')}},
                'delegation': {'type': 'client'}}})
            async with asyncio.timeout(25):
                while True:
                    event = await ws.receive_json()
                    if event.get('type') == 'error':
                        raise OpenAILiveError(str(event.get('error', {}).get('code', 'setup_error')))
                    if event.get('type') == 'session.started':
                        if event.get('session', {}).get('model') != config.get('openai_live_model', 'gpt-live-1'):
                            raise OpenAILiveError('unexpected_model')
                        break
            session = OpenAILiveSession(ws)
            pump = asyncio.create_task(session.pump())
            try:
                yield session
            finally:
                with contextlib.suppress(Exception):
                    await ws.send_json({'type': 'session.close'})
                    await asyncio.wait_for(session.closed.wait(), 3)
                pump.cancel()
                await asyncio.gather(pump, return_exceptions=True)
