"""Fetch a small CC0 VSCO instrument selection over an explicit physical NIC.

Windows authoring utility; no proxy, TUN, package installation or game changes.
Original upstream Git blob identities are verified before using any sample.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import re
import socket
import ssl
import struct

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'source-art/audio/iron-rally-v2/sources/vsco'


def fetch(blob_sha, interface, address):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(35)
    # IP_UNICAST_IF forces the real WLAN interface, overriding the TUN route.
    sock.setsockopt(socket.IPPROTO_IP, 31, struct.pack('!I', interface))
    sock.bind((address, 0))
    sock.connect(('140.82.116.6', 443))
    tls = ssl.create_default_context().wrap_socket(sock, server_hostname='api.github.com')
    client = http.client.HTTPSConnection('api.github.com')
    client.sock = tls
    try:
        client.request('GET', '/repos/sgossner/VSCO-2-CE/git/blobs/' + blob_sha,
                       headers={'User-Agent': 'SwordAndFire-CC0-audio-preparation'})
        response = client.getresponse()
        if response.status != 200:
            raise RuntimeError(f'Official Git blob HTTP {response.status}: {blob_sha}')
        data = json.loads(response.read())
        if data['encoding'] != 'base64':
            raise ValueError('Unexpected GitHub blob encoding')
        return base64.b64decode(data['content'])
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', type=int, required=True)
    parser.add_argument('--address', required=True)
    parser.add_argument('--tree', type=Path, required=True)
    args = parser.parse_args()
    tree = json.loads(args.tree.read_text(encoding='utf-8'))
    entries = {x['path']: x for x in tree['tree'] if x['type'] == 'blob'}
    OUT.mkdir(parents=True, exist_ok=True)
    records = []

    def take(path):
        expected = entries[path]
        target = OUT / path
        raw = target.read_bytes() if target.exists() else fetch(expected['sha'], args.interface, args.address)
        blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
        if blob != expected['sha'] or len(raw) != expected['size']:
            raise ValueError(f'Official Git blob hash/length mismatch: {path}')
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(raw)
        return dict(path=path, bytes=len(raw), gitBlobSha1=blob, sha256=hashlib.sha256(raw).hexdigest())

    for path in ('LICENSE', 'README.md', 'Readme.txt'):
        records.append(take(path))
    license_text = (OUT / 'LICENSE').read_text(encoding='utf-8')
    if 'CC0' not in license_text or 'Creative Commons' not in license_text:
        raise ValueError('Expected upstream CC0 license before retrieving recordings')
    groups = {
        'cello-short': ('Strings/Cello Section/spic/', ('C1', 'B1', 'D2', 'A2', 'C3'), r'_v2_RR[12]\.wav$'),
        'violin-short': ('Strings/Violin Section/Spic/', ('D3', 'A3', 'C4'), r'_v2_rr[12]\.wav$'),
        'cello-long': ('Strings/Cello Section/susvib/', ('C1', 'D2', 'A2'), r'_v3_1\.wav$'),
        'violin-long': ('Strings/Violin Section/susVib/', ('A3', 'C4'), r'_v2\.wav$'),
        'horn-long': ('Brass/F Horn/sus/', ('F2', 'C3', 'D#3'), r'_v3_1\.wav$'),
        'horn-short': ('Brass/F Horn/stac/', ('F2', 'C3'), r'_v3_rr1\.wav$'),
        'trombone': ('Brass/Tenor Trombone/sus/', ('D#1', 'D2', 'C3'), r'_v3_1\.wav$'),
    }
    selected = {}
    for name, (prefix, notes, suffix) in groups.items():
        files = [p for p in entries if p.startswith(prefix) and re.search(suffix, p)
                 and any(f'_{note}_' in p for note in notes)]
        if not files:
            raise ValueError('Missing selected instrument: ' + name)
        selected[name] = files
    selected.update({
        'bass-drum': ['VSCO 1 Percussion/drums/bass/bdrum_ff_1.wav', 'VSCO 1 Percussion/drums/bass/bdrum_fff_1.wav'],
        'snare': ['VSCO 1 Percussion/drums/snare/drum1/snare1_ff_1.wav', 'VSCO 1 Percussion/drums/snare/drum1/snare1_ff_2.wav'],
        'war-drum': ['VSCO 1 Percussion/drums/other/ethnic/giant/mallet/EthnicLargeMallet_hit_ff_1.wav', 'VSCO 1 Percussion/drums/other/ethnic/giant/mallet/EthnicLargeMallet_hit_ff_2.wav'],
        'cymbal': ['Percussion/cymbal-crashshort_v1.wav'],
    })
    files = [p for group in selected.values() for p in group]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for record in pool.map(take, files):
            records.append(record)
            print('Verified ' + record['path'], flush=True)
    (OUT / 'upstream-tree.json').write_bytes(args.tree.read_bytes())
    (OUT / 'source-manifest.json').write_text(json.dumps(dict(
        source='https://github.com/sgossner/VSCO-2-CE', upstreamTree=tree['sha'], license='CC0-1.0',
        author='Versilian Studios / Sam Gossner and contributors; see upstream Readme.txt',
        routing=dict(forcedPhysicalInterface=args.interface, boundIPv4=args.address,
                     originIPv4='140.82.116.6', tlsHost='api.github.com',
                     transport='Immutable upstream Git blob API; raw origin reset the direct TLS connection, no proxy fallback.',
                     proxy=False, tunBypassedWith='Windows IP_UNICAST_IF', proxyFallback=False),
        groups=selected, files=records), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(files=len(records), bytes=sum(x['bytes'] for x in records))))


if __name__ == '__main__':
    main()
