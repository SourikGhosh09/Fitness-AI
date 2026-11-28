"""Tutorial files from local verified assets, falling back to the pinned public source."""
import hashlib
import json
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from urllib.request import urlopen

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


def remote_url(source_path):
    """Pinned raw URL in the public source dataset; the same snapshot the source link shows."""
    from .importer import COMMIT,SOURCE
    return SOURCE.replace('github.com','raw.githubusercontent.com')+'/'+COMMIT+'/'+source_path

def available(source_path):
    """True when the manifest pins this asset, so it can be served locally or fetched remotely."""
    return source_path in manifest().get('assets',{})

def fetch_remote(source_path,timeout=15):
    """Download a manifest-pinned asset from the public source and verify it byte for byte."""
    info=manifest().get('assets',{}).get(source_path)
    if not info:return None
    cache=Path(tempfile.gettempdir())/'fitness-tutorial-media'/source_path
    if cache.is_file() and cache.stat().st_size==info['bytes'] and hashlib.sha256(cache.read_bytes()).hexdigest()==info['sha256']:
        return cache
    try:
        with urlopen(remote_url(source_path),timeout=timeout) as response:
            data=response.read(info['bytes']+1)
    except (OSError,ValueError):return None
    if len(data)!=info['bytes'] or hashlib.sha256(data).hexdigest()!=info['sha256']:
        return None
    cache.parent.mkdir(parents=True,exist_ok=True)
    cache.write_bytes(data)
    return cache
