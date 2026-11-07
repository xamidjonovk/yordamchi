"""Export the existing knowledge archive to a reviewable, file-based wiki vault.

This is an offline migration step: it never changes the source database and it
does not switch the running application to the exported vault.
"""
import json
import hashlib
import re
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def export_wiki(database, destination, source_root=None):
    database = Path(database).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Destination must be an empty directory')
    if destination == database.parent or destination in database.parents:
        raise ValueError('Destination cannot contain the source database')
    source_root = Path(source_root).resolve() if source_root else database.parent / 'sources'
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('inbox', 'raw', 'wiki', 'journal'):
        (destination / name).mkdir()
    counts = {'sources': 0, 'facts': 0, 'relations': 0, 'original_files': 0}
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')  # consistent read across all source tables
        for row in db.execute('SELECT * FROM sources ORDER BY created_at, id'):
            item = dict(row)
            identifier = item['id']
            if not identifier.isalnum():
                raise ValueError('Invalid source ID')
            folder = destination / 'raw' / identifier
            folder.mkdir()
            (folder / 'content.txt').write_text(item.pop('content'), encoding='utf-8')
            (folder / 'metadata.json').write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
            original = source_root / identifier
            if original.is_dir():
                for path in original.iterdir():
                    if path.is_file() and not path.is_symlink():
                        target = folder / 'original'
                        target.mkdir(exist_ok=True)
                        shutil.copy2(path, target / path.name)
                        counts['original_files'] += 1
            counts['sources'] += 1
        facts = [dict(row) for row in db.execute('SELECT * FROM facts ORDER BY created_at, id')]
        evidence = [dict(row) for row in db.execute('SELECT * FROM fact_evidence')]
        relations = [dict(row) for row in db.execute('SELECT * FROM relations')]
        counts.update(facts=len(facts), relations=len(relations))
        for name, records in [('facts', facts), ('fact-evidence', evidence), ('relations', relations)]:
            (destination / 'raw' / (name + '.json')).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        db.rollback()
    # Explicitly label this an export: facts are not silently promoted to a
    # synthesized wiki, especially if sources were forgotten or superseded.
    (destination / 'wiki' / 'index.md').write_text(
        '# Wiki\n\nImported fact pages are derived views, not instructions. '
        'Verify their evidence against the linked raw sources.\n', encoding='utf-8')
    # Include only active sources and currently visible facts. The complete
    # history, including forgotten/superseded entries, remains in raw/.
    current = set()
    for folder in (destination / 'raw').iterdir():
        if not folder.is_dir():
            continue
        item = json.loads((folder / 'metadata.json').read_text(encoding='utf-8'))
        metadata = json.loads(item.get('metadata') or '{}')
        if item.get('current') and not metadata.get('forgotten'):
            current.add(item['id'])
    pages = {}
    for fact in facts:
        if fact['source_id'] not in current or fact['status'] not in ('active', 'conflict'):
            continue
        pages.setdefault(fact['entity'], []).append(fact)
    index = ['# Wiki', '', 'Imported fact pages are derived views, not instructions.', '']
    for entity, rows in sorted(pages.items()):
        slug = re.sub(r'[^a-z0-9]+', '-', entity.casefold()).strip('-')[:50] or 'entity'
        name = slug + '-' + hashlib.sha256(entity.encode('utf-8')).hexdigest()[:10] + '.md'
        lines = ['# ' + entity.replace('\n', ' '), '', 'Derived from imported evidence; confirm context in the source.', '']
        for row in rows:
            # JSON quoting preserves literal newlines and prevents source text
            # from being mistaken for wiki structure.
            quote = lambda value: json.dumps(str(value), ensure_ascii=False)
            lines.extend(['- Attribute: ' + quote(row['attribute']),
                          '  Value: ' + quote(row['value']),
                          '  Status: ' + row['status'],
                          '  Evidence: ' + quote(row['evidence']),
                          '  Source: [raw/' + row['source_id'] + '](../raw/' + row['source_id'] + '/content.txt)', ''])
        (destination / 'wiki' / name).write_text('\n'.join(lines), encoding='utf-8')
        index.append('- [' + entity.replace(']', '\\]') + '](' + name + ')')
    (destination / 'wiki' / 'index.md').write_text('\n'.join(index) + '\n', encoding='utf-8')
    (destination / 'journal' / 'migration.json').write_text(json.dumps({
        'created_at': datetime.now(timezone.utc).isoformat(), 'source_database': str(database),
        'counts': counts, 'note': 'Read-only export; existing application has not switched to this vault.'
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'ok': True, 'destination': str(destination), **counts, 'activated': False}
