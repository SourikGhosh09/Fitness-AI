"""Restore compressed catalog/model and verify pinned upstream tutorial assets."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '7455efae41b330c265e7cd4b78dfa848e7ce5ebd'
URL = f'https://codeload.github.com/hasaneyldrm/exercises-dataset/zip/{COMMIT}'

def prepare(root=ROOT, archive=None, skip_media=False):
    data = root / 'data'
    for name in ('exercises.json', 'knowledge/exercise-model.json'):
        packed = data / (name + '.gz')
        if packed.exists():
            with gzip.open(packed, 'rb') as stream:
                (data / name).write_bytes(stream.read())
    manifest = json.loads((data / 'tutorial-media-manifest.json').read_text())
    if hashlib.sha256((data / 'exercises.json').read_bytes()).hexdigest() != manifest['dataset_sha256']:
        raise ValueError('Catalog digest mismatch')
    if skip_media:
        return
    assets = manifest['assets']
    def valid(path, expected):
        return path.is_file() and path.stat().st_size == expected['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest() == expected['sha256']
    needed = {rel: expected for rel, expected in assets.items() if not valid(data / 'tutorial-media' / rel, expected)}
    if not needed:
        print(f'Verified {len(assets)} tutorial files')
        return
    with tempfile.TemporaryDirectory() as temporary:
        bundle = Path(archive) if archive else Path(temporary) / 'upstream.zip'
        if not archive:
            with urlopen(URL, timeout=120) as response, bundle.open('wb') as output:
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > 200 * 1024 * 1024:
                        raise ValueError('Archive exceeds expected download limit')
                    output.write(chunk)
        with zipfile.ZipFile(bundle) as source:
            for rel, expected in needed.items():
                if Path(rel).is_absolute() or '..' in Path(rel).parts:
                    raise ValueError('Unsafe manifest path')
                matches = [entry for entry in source.infolist() if entry.filename.split('/', 1)[-1] == rel]
                if len(matches) != 1 or matches[0].file_size != expected['bytes']:
                    raise ValueError('Missing or unexpected archive asset: ' + rel)
                content = source.read(matches[0])
                if hashlib.sha256(content).hexdigest() != expected['sha256']:
                    raise ValueError('Tutorial digest mismatch: ' + rel)
                target = data / 'tutorial-media' / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    print(f'Verified {len(assets)} tutorial files')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', help='Optional existing original source ZIP')
    parser.add_argument('--skip-media', action='store_true')
    args = parser.parse_args()
    prepare(archive=args.archive, skip_media=args.skip_media)
