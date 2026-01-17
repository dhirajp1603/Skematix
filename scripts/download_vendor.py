#!/usr/bin/env python3
import os
import sys
from urllib.request import urlretrieve

urls = [
    'https://cdn.jsdelivr.net/npm/three@0.150.0/build/three.module.js',
    'https://cdn.jsdelivr.net/npm/three@0.150.0/examples/jsm/loaders/GLTFLoader.js',
    'https://cdn.jsdelivr.net/npm/three@0.150.0/examples/jsm/loaders/DRACOLoader.js',
    'https://cdn.jsdelivr.net/npm/three@0.150.0/examples/jsm/controls/OrbitControls.js',
    'https://www.gstatic.com/draco/v1/decoders/draco_decoder.js',
    'https://www.gstatic.com/draco/v1/decoders/draco_decoder.wasm',
]

outdir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'vendor')
outdir = os.path.abspath(outdir)
os.makedirs(outdir, exist_ok=True)

ok = []
for url in urls:
    name = url.split('/')[-1]
    out = os.path.join(outdir, name)
    try:
        print(f'Downloading {url} -> {out}')
        urlretrieve(url, out)
        print('Saved', out)
        ok.append(name)
    except Exception as e:
        print('ERROR', url, e)

print('\nDownloaded files:')
for f in sorted(os.listdir(outdir)):
    print('-', f)

if len(ok) != len(urls):
    print('\nSome files failed to download. You can re-run this script or download manually.')
    sys.exit(2)

print('\nAll files downloaded successfully.')
sys.exit(0)
