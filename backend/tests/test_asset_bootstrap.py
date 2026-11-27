"""Deployment must reject altered tutorials before trusting downloaded bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
import pytest

spec = importlib.util.spec_from_file_location('prepare_assets', Path(__file__).resolve().parents[2] / 'scripts/prepare_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)

def fixture(root, content=b'GIF89a'):
    data = root / 'data'
    data.mkdir()
    (data / 'exercises.json').write_bytes(b'[]')
    manifest = {'dataset_sha256': hashlib.sha256(b'[]').hexdigest(), 'assets': {
        'videos/sample.gif': {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}}}
    (data / 'tutorial-media-manifest.json').write_text(json.dumps(manifest))
    return data

def test_restores_only_verified_manifest_assets(tmp_path):
    data = fixture(tmp_path)
    archive = tmp_path / 'source.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('upstream/videos/sample.gif', b'GIF89a')
        z.writestr('upstream/../../unexpected', b'not an authorized asset')
    assets.prepare(tmp_path, archive)
    assert (data / 'tutorial-media/videos/sample.gif').read_bytes() == b'GIF89a'
    assert sorted(p.relative_to(data / 'tutorial-media').as_posix() for p in (data / 'tutorial-media').rglob('*') if p.is_file()) == ['videos/sample.gif']

def test_corrupt_download_is_rejected(tmp_path):
    data = fixture(tmp_path)
    archive = tmp_path / 'source.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('upstream/videos/sample.gif', b'GIF00a')
    with pytest.raises(ValueError, match='digest mismatch'):
        assets.prepare(tmp_path, archive)
    assert not (data / 'tutorial-media/videos/sample.gif').exists()
