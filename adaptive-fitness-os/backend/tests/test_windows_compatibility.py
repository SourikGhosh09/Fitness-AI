"""File handles and worker exclusion must work on Windows as well as POSIX."""
import hashlib
import json
import subprocess
import sys
import zipfile

import pytest

from fitness import db
from fitness.backup import restore
from fitness.notion_worker import worker_lock


def test_worker_lock_excludes_other_process_and_releases_after_error(tmp_path):
    url = 'sqlite:///' + str(tmp_path / 'worker.db')
    database = db.make_engine(url)
    script = (
        'import sys\n'
        'from fitness import db\n'
        'from fitness.notion_worker import worker_lock\n'
        'with worker_lock(db.make_engine(sys.argv[1])) as acquired:\n'
        '    print(acquired)\n'
    )

    def other_worker():
        return subprocess.run(
            [sys.executable, '-c', script, url], capture_output=True,
            text=True, check=True, timeout=30,
        ).stdout.strip()

    try:
        with pytest.raises(RuntimeError, match='worker failed'):
            with worker_lock(database) as acquired:
                assert acquired
                assert other_worker() == 'False'
                raise RuntimeError('worker failed')
        assert other_worker() == 'True'
    finally:
        database.dispose()


def test_invalid_database_restore_closes_handle_before_cleanup(tmp_path):
    raw = b'This is not a SQLite database'
    archive = tmp_path / 'invalid.zip'
    destination = tmp_path / 'restored.db'
    with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('fitness.sqlite', raw)
        output.writestr('manifest.json', json.dumps({
            'version': 1, 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
        }))
    import sqlite3
    with pytest.raises(sqlite3.DatabaseError):
        restore(archive, destination)
    assert not destination.exists()
