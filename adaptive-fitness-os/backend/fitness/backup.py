"""Consistent SQLite backups with embedded checksums and quarantine on restore.

PostgreSQL installations use pg_dump/PITR as documented in BACKUP.md.
Backups contain sensitive data; keep them on encrypted storage, outside source control.
"""
import argparse,hashlib,json,os,sqlite3,tempfile,time,zipfile
from pathlib import Path
from sqlalchemy.engine import make_url

def backup(database_url,destination):
    url=make_url(database_url)
    if url.get_backend_name()!='sqlite' or not url.database or url.database==':memory:':raise ValueError('This command supports file-backed SQLite; use the PostgreSQL runbook for PostgreSQL')
    source=Path(url.database).resolve();dest=Path(destination).resolve()
    if not source.is_file():raise ValueError('Source database does not exist')
    if dest.exists():raise ValueError('Backup destination already exists')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        snapshot=Path(tmp)/'fitness.sqlite'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(snapshot) as out:
            src.backup(out)
            if out.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity check failed')
        raw=snapshot.read_bytes()
        manifest={'version':1,'created_at':time.time(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'contains':'accounts, workout history, consent, learning examples, neural weights, evaluations and deployment state','encrypted':False}
        fd=os.open(dest,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(fd,'wb') as output,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('manifest.json',json.dumps(manifest));archive.writestr('fitness.sqlite',raw)
        except BaseException:
            dest.unlink(missing_ok=True);raise
    return {'backup':str(dest),'sha256':manifest['sha256'],'encrypted':False}

def restore(archive_path,destination):
    dest=Path(destination).resolve()
    if dest.exists():raise ValueError('Restore requires a new destination; existing databases are never overwritten')
    with zipfile.ZipFile(archive_path) as archive:
        if sorted(archive.namelist())!=['fitness.sqlite','manifest.json']:raise ValueError('Invalid backup members')
        if archive.getinfo('manifest.json').file_size>65536 or archive.getinfo('fitness.sqlite').file_size>2*1024**3:raise ValueError('Backup exceeds restore bounds')
        manifest=json.loads(archive.read('manifest.json'));raw=archive.read('fitness.sqlite')
        if manifest.get('version')!=1 or len(raw)!=manifest['bytes'] or hashlib.sha256(raw).hexdigest()!=manifest['sha256']:raise ValueError('Backup checksum mismatch')
    dest.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(dest,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw)
        with sqlite3.connect(dest) as c:
            if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Restored database failed integrity check')
            tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'learning_deployment' in tables:
                c.execute("UPDATE learning_deployment SET model_id=NULL, mode='shadow'")
                c.execute('UPDATE learning_consent SET enabled=0')
                c.execute('DELETE FROM learning_examples')
                c.execute("UPDATE learning_models SET status='quarantined'")
            if 'notion_links' in tables:
                c.execute('UPDATE notion_links SET enabled=0')
                # Quarantine imported mappings AND outbound jobs. Reconcile the
                # current deletion ledger before manually resuming any worker.
                for name in ('notion_imports','notion_pages','notion_purges','notion_worker_state'):
                    if name in tables:c.execute('DELETE FROM '+name)
            if 'survey_participants' in tables:c.execute('UPDATE survey_participants SET revoked=1')
            if 'api_keys' in tables:c.execute('UPDATE api_keys SET revoked=1')
            if 'user_contributions' in tables:c.execute('DELETE FROM user_contributions')
    except BaseException:
        dest.unlink(missing_ok=True);raise
    return {'restored_to':str(dest),'mode':'quarantined','next':'Reconcile account deletions since the backup before serving. All access tokens revoked; shared learning is off; models must be retrained after fresh consent.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
    a=s.add_parser('create');a.add_argument('destination')
    a=s.add_parser('restore');a.add_argument('archive');a.add_argument('--output',required=True)
    a=p.parse_args()
    try:result=backup(os.getenv('DATABASE_URL','sqlite:///./fitness.db'),a.destination) if a.action=='create' else restore(a.archive,a.output)
    except (ValueError,OSError,sqlite3.Error,zipfile.BadZipFile) as e:p.exit(2,str(e)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
