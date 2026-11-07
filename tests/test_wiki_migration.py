import json
import sqlite3
from contextlib import closing

import pytest

from hermes_personal_agent.knowledge import LegacyKnowledge as Knowledge
from hermes_personal_agent.wiki_migration import export_wiki


def test_export_preserves_sources_facts_and_originals_without_mutating_database(tmp_path):
    root = tmp_path / 'data'
    root.mkdir()
    database = root / 'knowledge.sqlite3'
    kb = Knowledge(database, root)
    file = tmp_path / 'document.txt'
    file.write_text('Alice works at Acme.', encoding='utf-8')
    source = kb.ingest(file)['source_id']
    kb.add_fact('Alice', 'employer', 'Acme', source, 'Alice works at Acme.')
    kb.relate('Alice', 'works at', 'Acme', source, 'Alice works at Acme.')
    vault = tmp_path / 'vault'
    result = export_wiki(database, vault)
    assert result['activated'] is False
    assert (result['sources'], result['facts'], result['relations'], result['original_files']) == (1, 1, 1, 1)
    assert (vault / 'raw' / source / 'content.txt').read_text(encoding='utf-8') == 'Alice works at Acme.'
    assert (vault / 'raw' / source / 'original' / 'document.txt').read_text(encoding='utf-8') == 'Alice works at Acme.'
    assert json.loads((vault / 'raw' / 'facts.json').read_text(encoding='utf-8'))[0]['source_id'] == source
    page = next(path for path in (vault / 'wiki').glob('*.md') if path.name != 'index.md')
    assert 'Alice works at Acme.' in page.read_text(encoding='utf-8')
    assert '../raw/' + source + '/content.txt' in page.read_text(encoding='utf-8')
    with closing(sqlite3.connect(database)) as db:
        assert db.execute('select count(*) from sources').fetchone()[0] == 1
    with pytest.raises(ValueError):
        export_wiki(database, vault)


def test_export_rejects_destination_containing_database(tmp_path):
    database = tmp_path / 'knowledge.sqlite3'
    Knowledge(database, tmp_path)
    with pytest.raises(ValueError):
        export_wiki(database, tmp_path)


def test_forgotten_sources_do_not_appear_in_derived_wiki(tmp_path):
    database = tmp_path / 'knowledge.sqlite3'
    kb = Knowledge(database, tmp_path)
    source = kb.add_text('Note', 'Alice lives in Paris.')['source_id']
    kb.add_fact('Alice', 'city', 'Paris', source, 'Alice lives in Paris.')
    kb.forget(source)
    vault = tmp_path / 'vault'
    export_wiki(database, vault)
    assert list((vault / 'wiki').glob('*.md')) == [vault / 'wiki' / 'index.md']
    assert (vault / 'raw' / source / 'content.txt').is_file()
