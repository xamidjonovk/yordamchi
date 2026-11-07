"""Incremental import of files deliberately placed in the instance's inbox."""
from pathlib import Path
from .voice_common import APP_HOME


def scan(knowledge,limit=40):
    roots=[(APP_HOME/'inbox').resolve(), (knowledge.path/'inbox').resolve()]
    for root in roots: root.mkdir(exist_ok=True)
    results=[]
    observations=knowledge.observations()
    for root in roots:
      for source in root.rglob('*'):
        if len(results)>=limit:break
        if not source.is_file() or source.is_symlink() or any(p.startswith('.') for p in source.relative_to(root).parts):continue
        if root not in source.resolve().parents:continue
        stat=source.stat()
        import time
        if time.time()-stat.st_mtime<2:continue
        row=observations.get(str(source))
        if row and row['mtime']==stat.st_mtime and row['size']==stat.st_size:continue
        try:
            result=knowledge.ingest(source);status='indexed';error=None
        except Exception as problem:
            result={};status='needs_attention';error=str(problem)[:300]
        knowledge.observe(str(source),{'path':str(source),'mtime':stat.st_mtime,'size':stat.st_size,'status':status,'error':error})
        results.append({'file':str(source),'status':status,'error':error,**result})
    return results
