"""Serverless deployments must never silently persist to ephemeral SQLite."""
import pytest
from sqlalchemy.pool import NullPool
from fitness import db

@pytest.mark.parametrize('url', [None, 'sqlite:////tmp/fitness.db',
                                'postgresql://user:secret@example.invalid/db'])
def test_vercel_rejects_missing_ephemeral_or_unencrypted_database(monkeypatch,url):
    monkeypatch.setenv('VERCEL','1')
    monkeypatch.delenv('DATABASE_URL',raising=False)
    with pytest.raises(ValueError,match='Vercel requires'):
        db.make_engine(url)

@pytest.mark.parametrize('scheme',['postgres','postgresql','postgresql+psycopg'])
def test_vercel_accepts_provider_url_without_connecting(monkeypatch,scheme):
    monkeypatch.setenv('VERCEL','1')
    database=db.make_engine(f'{scheme}://user:secret@example.invalid/db?sslmode=require')
    assert database.url.drivername=='postgresql+psycopg'
    assert database.url.query['sslmode']=='require'
    assert isinstance(database.pool,NullPool)
    args,kwargs=database.dialect.create_connect_args(database.url)
    assert kwargs['sslmode']=='require'
    database.dispose()

def test_local_sqlite_still_enforces_foreign_keys(monkeypatch):
    monkeypatch.delenv('VERCEL',raising=False)
    database=db.make_engine('sqlite:///:memory:')
    with database.connect() as connection:
        assert connection.exec_driver_sql('PRAGMA foreign_keys').scalar()==1
    database.dispose()
