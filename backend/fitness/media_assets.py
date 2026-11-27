"""Local tutorial files from the supplied archive, verified against an asset manifest."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

def data_dir():
    return Path(os.environ.get('FITNESS_DATA_DIR',Path(__file__).resolve().parents[2]/'data')).resolve()

@lru_cache(maxsize=4)
def _manifest(path,mtime_ns):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def manifest():
    path=data_dir()/'tutorial-media-manifest.json'
    try:return _manifest(str(path),path.stat().st_mtime_ns)
    except (OSError,ValueError):return {'assets':{}}

def resolve_asset(source_path,verify=False):
    root=(data_dir()/'tutorial-media').resolve()
    path=(root/source_path).resolve()
    info=manifest().get('assets',{}).get(source_path)
    if not info or not path.is_relative_to(root) or not path.is_file():
        return None
    if path.stat().st_size!=info['bytes']:
        return None
    if verify and hashlib.sha256(path.read_bytes()).hexdigest()!=info['sha256']:
        return None
    return path
