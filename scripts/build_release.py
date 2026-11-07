"""Build a redistributable source archive from an explicit public-file allowlist."""
import hashlib
import json
import tomllib
import zipfile
from pathlib import Path


def build(root=None):
    root=Path(root or Path(__file__).resolve().parents[1])
    from privacy_scan import scan
    audit=scan(root)
    if not audit['ok']:
        raise ValueError('Privacy scan failed. Run scripts/privacy_scan.py for file locations.')
    version=tomllib.loads((root/'pyproject.toml').read_text())['project']['version']
    output=root/'dist';output.mkdir(exist_ok=True)
    files=[]
    for name in ['README.md','LICENSE','SECURITY.md','PRODUCT.md','DESIGN.md','pyproject.toml','uv.lock','Dockerfile','compose.yaml','compose.coolify.yaml','docker-compose.prod.yml','.dockerignore','.gitignore','.gitattributes','.env.example','install.cmd','start-web.cmd']:
        files.append(root/name)
    for directory in ['src','scripts','tests','docs','.github']:
        files.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'})
    archive=output/f'hermes-personal-agent-{version}.zip'
    prefix=f'hermes-personal-agent-{version}'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as package:
        for file in sorted(files):package.write(file,prefix+'/'+file.relative_to(root).as_posix())
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n')
    return {'archive':str(archive),'files':len(files),'sha256':digest,'private_data_included':False}


if __name__=='__main__':print(json.dumps(build(),indent=2))
