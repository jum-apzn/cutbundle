"""Explicit one-time model download. Does not execute model repository code."""
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

from models_config import MODELS
import argparse


def digest(path):
    with open(path, 'rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', choices=list(MODELS), default='u2netp')
    args = parser.parse_args()
    config = MODELS[args.model]
    TARGET = Path(__file__).resolve().parent / 'models' / f'{args.model}.onnx'
    URL, SHA256, SIZE = config['url'], config['sha256'], config['size']
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.is_file() and digest(TARGET) == SHA256:
        print('Verified model already installed.'); return
    print(f'Downloading {args.model}: {SIZE / 1e6:.1f} MB from the rembg GitHub release. No photos are sent.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=TARGET.parent, delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(URL, timeout=120) as response:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > SIZE:
                        raise RuntimeError('Model larger than expected; refusing it.')
                    output.write(chunk)
        if temporary.stat().st_size != SIZE or digest(temporary) != SHA256:
            raise RuntimeError('Model checksum mismatch; refusing it.')
        os.replace(temporary, TARGET)
        print('Installed and SHA-256 verified. Start manually with: python server.py')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
