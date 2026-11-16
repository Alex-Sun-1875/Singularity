"""Render the accepted journey study's five-bar aftermath as a runtime one-shot.

The two existing 96-second loop assets are protected by before/after hashes.
No new dependencies, downloads, external recordings or AI generation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile

import numpy as np
from scipy.io import wavfile


ROOT = Path(__file__).resolve().parents[4]
SCORE_SOURCE = ROOT / 'source-art/audio/direction-studies-v2/music/a-adaptive-demo/score.json'
SOURCE = ROOT / 'source-art/audio/runtime-integration-v1'
RUNTIME = ROOT / 'src/cocos/assets/resources/audio/music'
RATE = 44100
SECONDS = 15
START_BEAT = 40
TARGET_LUFS = -23
IDENTIFIER = 'embers-oaths-aftermath'


def load_loop_tool():
    path = Path(__file__).with_name('make_music_loops.py')
    spec = importlib.util.spec_from_file_location('_runtime_loop_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    loops = load_loop_tool()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=loops.DEFAULT_FFMPEG)
    args = parser.parse_args(argv)
    if not args.ffmpeg.is_file():
        parser.error('Provide an existing FFmpeg binary. No download is attempted.')
    protected = {name: sha256(RUNTIME / f'embers-oaths-{name}.mp3') for name in ('explore', 'combat')}
    original = json.loads(SCORE_SOURCE.read_text(encoding='utf-8'))
    shared = loops.original_instruments()
    notes = [shared.Note(**{**note, 'beat': round(note['beat'] - START_BEAT, 5)})
             for note in original['notes'] if note['beat'] >= START_BEAT]
    if not notes or original['seconds'] != 45 or original['bpm'] != 80:
        raise ValueError('Expected the original 45-second, 80 BPM journey score.')
    stems = shared.render(notes, SECONDS, room_seed=900)
    # Preserve the study's falling plucked-layer energy across the combat exit.
    timeline = np.arange(SECONDS * RATE) / RATE + 30
    fraction = np.clip((timeline - 29.25) / (31.5 - 29.25), 0, 1)
    combat_window = .5 + .5 * np.cos(np.pi * fraction)
    stems['plucked'] *= (.83 + .17 * combat_window)[:, None]
    audio = np.sum(np.stack(list(stems.values())), axis=0)
    if len(audio) != SECONDS * RATE or not np.isfinite(audio).all():
        raise ValueError('Expected finite, exact 15-second PCM.')
    SOURCE.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    master = SOURCE / 'music-aftermath-master.flac'
    asset = RUNTIME / f'{IDENTIFIER}.mp3'
    with tempfile.TemporaryDirectory(prefix='sword-fire-aftermath-') as temporary:
        folder = Path(temporary)
        raw = folder / 'raw.wav'
        wavfile.write(raw, RATE, audio)
        measured = loops.measure(args.ffmpeg, raw)
        gain = min(10 ** ((TARGET_LUFS - float(measured['input_i'])) / 20),
                   10 ** (-3.5 / 20) / max(1e-9, float(np.max(np.abs(audio)))))
        audio *= gain
        wavfile.write(raw, RATE, audio)
        loops.command((args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', raw,
                       '-c:a', 'flac', '-sample_fmt', 's32', '-bits_per_raw_sample', 24, master))
        encoders = loops.command((args.ffmpeg, '-hide_banner', '-encoders')).stdout
        encoder = 'libmp3lame' if 'libmp3lame' in encoders else 'mp3_mf'
        encoded = folder / 'encoded.mp3'
        loops.command((args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', master,
                       '-c:a', encoder, '-b:a', '128k', '-ar', RATE,
                       '-metadata', 'title=余烬与誓言 · 战后余温', encoded))
        loops.command((args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', encoded,
                       '-c:a', 'copy', asset))
        decoded = folder / 'decoded.wav'
        loops.command((args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', asset, decoded))
        decoded_rate, pcm = wavfile.read(decoded)
        master_metrics = loops.measure(args.ffmpeg, master)
        encoded_metrics = loops.measure(args.ffmpeg, asset)
    loops.write_meta(asset)
    after = {name: sha256(RUNTIME / f'embers-oaths-{name}.mp3') for name in protected}
    if after != protected:
        raise RuntimeError('An existing loop asset changed during aftermath authoring.')
    mono = audio.mean(axis=1)
    report = {
        'mode': 'aftermath', 'kind': 'one-shot-aftermath', 'loop': False,
        'asset': asset.relative_to(ROOT).as_posix(), 'resourcePath': 'audio/music/' + IDENTIFIER,
        'master': master.relative_to(ROOT).as_posix(),
        'sourceScore': SCORE_SOURCE.relative_to(ROOT).as_posix(),
        'sourceSegmentSeconds': [30, 45], 'sourceSegmentBeats': [40, 60],
        'bpm': 80, 'bars': 5, 'meter': '4/4', 'modeName': 'D Dorian',
        'harmonicReturn': ['F', 'G', 'Am', 'Dm', 'Dm'],
        'authoredSeconds': SECONDS, 'authoredFrames': len(audio), 'sampleRate': RATE, 'channels': 2,
        'runtimeBytes': asset.stat().st_size, 'encoder': encoder,
        'decodedMp3Seconds': len(pcm) / decoded_rate,
        'decodedMp3ExtraSeconds': len(pcm) / decoded_rate - SECONDS,
        'targetIntegratedLufs': TARGET_LUFS,
        'masterIntegratedLufs': float(master_metrics['input_i']),
        'masterTruePeakDbtp': float(master_metrics['input_tp']),
        'mp3IntegratedLufs': float(encoded_metrics['input_i']),
        'mp3TruePeakDbtp': float(encoded_metrics['input_tp']),
        'clippingSamples': int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767)),
        'masterFirst100msRms': float(np.sqrt(np.mean(audio[:4410] ** 2))),
        'masterLast100msRms': float(np.sqrt(np.mean(audio[-4410:] ** 2))),
        'masterLastSamplePeak': float(np.max(np.abs(audio[-1]))),
        'monoRmsVsStereoRmsDb': float(20 * math.log10(max(1e-12, np.sqrt(np.mean(mono ** 2))) / np.sqrt(np.mean(audio ** 2)))),
        'retainedLoopHashes': protected, 'existingLoopsByteIdentical': True,
        'instrumentation': ['strings', 'cello', 'harp', 'flute', 'bronze'],
        'percussionNotes': sum(note.stem == 'percussion' for note in notes),
        'production': 'Original journey aftermath score and accepted A acoustic-inspired synthesis; one complete five-bar settling phrase with naturally released tails, not a third long loop.',
        'sha256': sha256(asset),
        'acceptance': {'numerical': 'Measured exact PCM duration, encoded duration, loudness/true peak, clipping, mono and quiet ending; existing loops protected by hash.',
                       'listening': 'Pending audition of runtime transitions and final game mix.',
                       'runtime': 'Asset supplied for root-agent state-machine integration; not claimed integrated by this generator.',
                       'device': 'TapTap target-device audio remains pending.'},
    }
    if report['clippingSamples'] or report['mp3TruePeakDbtp'] > -3:
        raise ValueError('Unsafe aftermath encoded audio peak.')
    loops.write_json(SOURCE / 'music-aftermath-score.json', {
        'mode': 'aftermath', 'kind': 'one-shot', 'loop': False,
        'sourceScore': report['sourceScore'], 'sourceSegmentSeconds': [30, 45],
        'seconds': SECONDS, 'bpm': 80, 'bars': 5, 'heldUnit': 'beats',
        'notes': [asdict(note) for note in notes],
    })
    loops.write_json(SOURCE / 'music-aftermath-technical.json', report)
    manifest_path = SOURCE / 'music-manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['tracks'] = [item for item in manifest['tracks'] if item['mode'] != 'aftermath'] + [report]
    manifest['additionalGenerators'] = ['src/cocos/tools/audio-runtime-v1/make_music_aftermath.py']
    manifest['runtime'] = 'Exploration and combat use two phase-positioned premixed loops; the independent 15-second aftermath is a non-looping settling phrase for the combat-exit state.'
    loops.write_json(manifest_path, manifest)
    print(json.dumps({key: report[key] for key in ('mode', 'authoredSeconds', 'runtimeBytes', 'masterIntegratedLufs', 'mp3TruePeakDbtp', 'masterLast100msRms', 'existingLoopsByteIdentical')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
