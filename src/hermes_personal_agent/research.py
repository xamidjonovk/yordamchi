"""Fetch a cited public source into the knowledge archive; discovery uses Hermes browser/search."""
import ipaddress
import socket
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from .documents import TextHTML, extract


def public_url(url):
    parsed=urlsplit(url)
    if parsed.scheme not in {'http','https'} or not parsed.hostname or parsed.username:
        raise ValueError('Use a public http(s) URL without credentials')
    addresses=socket.getaddrinfo(parsed.hostname,parsed.port or (443 if parsed.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Private, loopback and metadata addresses are not public research sources')


def fetch(url,knowledge):
    current=url
    with httpx.Client(timeout=25,follow_redirects=False,headers={'User-Agent':'HermesPersonalAgent/0.3 (personal research)'}) as client:
        for _ in range(6):
            public_url(current)
            with client.stream('GET',current) as response:
                if response.is_redirect:
                    current=urljoin(current,response.headers['location']);continue
                response.raise_for_status()
                content=bytearray()
                for block in response.iter_bytes():
                    content.extend(block)
                    if len(content)>10_000_000:raise ValueError('Research source exceeds 10 MB')
                mime=response.headers.get('content-type','')
            break
        else:raise ValueError('Too many redirects')
    if 'pdf' in mime:
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.pdf';path.write_bytes(content)
            parts=extract(path);text='\n\n'.join(t for _,t in parts)
    else:
        raw=bytes(content).decode('utf-8',errors='replace')
        if 'html' in mime:
            parser=TextHTML();parser.feed(raw);text=' '.join(parser.text)
        elif mime.startswith('text/') or 'json' in mime:text=raw
        else:raise ValueError('Source is not text, HTML, JSON or PDF')
        parts=None
    return knowledge.add_text(current,text,kind='research',uri=current,trust='web',parts=parts,
                              metadata={'requested_url':url})
