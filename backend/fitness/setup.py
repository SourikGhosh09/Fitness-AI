"""Initialize the database and supplied tutorial assets using the owner's authorization."""
import hashlib
import json
from pathlib import Path
from alembic import command
from alembic.config import Config
from . import db,media_assets
from .importer import run as import_dataset,COMMIT
from .tutorials import grant_rights

def initialize(database):
    root=media_assets.data_dir()
    authorization=json.loads((root/'media-authorization.json').read_text())
    inventory=json.loads((root/'tutorial-media-manifest.json').read_text())
    raw=(root/'exercises.json').read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if authorization['dataset_sha256']!=sha or inventory['dataset_sha256']!=sha:
        raise ValueError('Authorized source dataset does not match the installed dataset')
    if authorization['archive_sha256']!=inventory['archive_sha256'] or authorization['source_commit']!=COMMIT:
        raise ValueError('Media authorization does not match this source snapshot')
    rows=json.loads(raw)
    expected={r[k] for r in rows for k in ('image','gif_url')}
    if set(inventory['assets'])!=expected:
        raise ValueError('Asset inventory does not match the source exercise mappings')
    if sorted(authorization['exercise_ids'])!=sorted('source:'+r['id'] for r in rows):
        raise ValueError('Authorization scope does not match the source exercise IDs')
    for rel in expected:
        if media_assets.resolve_asset(rel,verify=True) is None:
            raise ValueError('Missing or altered tutorial asset: '+rel)
    report=import_dataset(root/'exercises.json',database)
    with database.begin() as conn:
        grants=grant_rights(conn,authorization['exercise_ids'],authorization['rights_reference'],authorization['recorded_by'],expires_at=None,reuse_existing=True)
    return {**report,'verified_local_assets':len(expected),'new_media_grants':len(grants),'authorization_basis':'owner declaration supplied with archive','exercise_safety_review':'separate; unchanged'}

if __name__=='__main__':
    backend=Path(__file__).resolve().parents[1]
    config=Config(str(backend/'alembic.ini'))
    config.set_main_option('script_location',str(backend/'alembic'))
    command.upgrade(config,'head')
    print(json.dumps(initialize(db.make_engine()),indent=2))
