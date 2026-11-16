"""Build A-direction exploration/combat loops from original project instruments.

The 32-bar scores are authored as loops: note releases and room tails wrap to
the head. No start/end fade from the 30-second listening study is reused.
Only installed NumPy/SciPy/FFmpeg are used; no samples, downloads or AI calls.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'source-art/audio/runtime-integration-v1'
RUNTIME = ROOT / 'src/cocos/assets/resources/audio/music'
RATE = 44100
BPM = 80
BEAT = 60 / BPM
BARS = 32
SECONDS = BARS * 4 * BEAT
FRAMES = round(SECONDS * RATE)
DEFAULT_FFMPEG = Path('C:/Program Files (x86)/Lenovo/LegionZone/2.0.30.11033/SEGamingAI/services/editor/ffmpeg.exe')
TRACKS = {'explore': 'embers-oaths-explore', 'combat': 'embers-oaths-combat'}


def original_instruments():
    path = ROOT / 'src/cocos/tools/audio-direction-v2/music_samples.py'
    spec = importlib.util.spec_from_file_location('_embers_original_instruments', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def score(shared, mode):
    notes = []
    harmony = shared.HARMONY[:8]
    melody = shared.MELODY[:8]

    def add(kind, stem, pitch, beat, held, level, pan=0.):
        notes.append(shared.Note(kind, stem, pitch, round(beat, 5), held, round(level, 5), pan))

    for bar in range(BARS):
        section, local = divmod(bar, 8)
        root, chord = harmony[local]
        beat = bar * 4
        combat = mode == 'combat'
        energy = (1., 1.07, .88, 1.03)[section]
        for i, pitch in enumerate(chord):
            add('strings', 'strings', pitch, beat + i * .018, 3.65,
                (.13 if combat else .11) * energy, (-.55, .25, .53)[i])
        add('cello', 'strings', root, beat + .025, 3.4,
            (.22 if combat else .18) * energy, -.08)
        if combat:
            pitches = (root + 12, chord[0] + 12, chord[1] + 12, chord[0] + 12)
            for i in range(8):
                add('lute', 'plucked', pitches[i % 4], beat + .5 * i, .32,
                    (.17 if i % 2 == 0 else .10) * energy, -.26)
            for offset, level in ((0, .19), (1.5, .075), (2, .12), (3.25, .075)):
                add('drum', 'percussion', 36, beat + offset, .075, level * energy)
            for offset in (.75, 2.75):
                add('frame-drum', 'percussion', 48, beat + offset, .055, .075 * energy, .24)
            if local in (0, 3, 7):
                for offset, pitch, held in melody[local]:
                    add('low-flute', 'melody', pitch - 12, beat + offset, held, .13 * energy, -.03)
        else:
            for i, (offset, pitch) in enumerate(zip((0, .75, 1.5, 2.5, 3.25),
                                                   (root + 12, chord[0] + 12, chord[2], chord[1] + 12, chord[0] + 12))):
                add('lute', 'plucked', pitch, beat + offset, .45,
                    .145 * energy * (1 if i % 2 == 0 else .78), -.32)
            if local in (1, 3, 5, 7):
                for i, pitch in enumerate((chord[1] + 12, chord[2] + 12)):
                    add('harp', 'plucked', pitch, beat + 2.7 + .5 * i, .55, .060 * energy, .38)
            for offset, pitch, held in melody[local]:
                if section == 2 and offset >= 2.:
                    continue
                kind = 'low-flute' if section == 2 else 'flute'
                octave = -12 if section == 2 else 0
                add(kind, 'melody', pitch + octave, beat + offset, held, .22 * energy, .02)
            if local != 4:
                add('drum', 'percussion', 36, beat, .08, .105 * energy)
                add('frame-drum', 'percussion', 48, beat + 2.5, .055, .048 * energy, .22)
        if local == 0 or not combat and local == 4:
            add('bronze', 'bronze', 50 if combat else 62, beat + .06, .15,
                .040 if combat else .048, .38)
    return notes


def circular_room(audio, seed):
    rng = np.random.default_rng(seed)
    length = round(1.55 * RATE)
    t = np.arange(length) / RATE
    for channel in range(2):
        impulse = np.zeros(length, np.float32)
        for delay, gain in ((.029, .23), (.053, .17), (.087, .12), (.137, .085)):
            impulse[round((delay + channel * .006) * RATE)] += gain
        diffuse = sosfilt(butter(2, 3400, fs=RATE, output='sos'), rng.normal(0, 1, length))
        impulse += (diffuse * np.exp(-t * 4.8) * np.minimum(t / .045, 1) * .006).astype(np.float32)
        wet = fftconvolve(audio[:, channel], impulse)
        audio[:, channel] += .15 * wet[:FRAMES]
        audio[:len(wet) - FRAMES, channel] += .15 * wet[FRAMES:]
    return audio


def render(shared, notes, mode):
    audio = np.zeros((FRAMES, 2), np.float32)
    wraps = 0
    for note in notes:
        sound = shared.instrument(note.instrument, note.midi, round(note.held * BEAT, 5)) * note.level
        angle = (note.pan + 1) * np.pi / 4
        stereo = sound[:, None] * np.array((np.cos(angle), np.sin(angle)), np.float32)
        begin = round(note.beat * BEAT * RATE) % FRAMES
        first = min(len(stereo), FRAMES - begin)
        audio[begin:begin + first] += stereo[:first]
        if first < len(stereo):
            audio[:len(stereo) - first] += stereo[first:]
            wraps += 1
    circular_room(audio, 20261116 + (1 if mode == 'combat' else 0))
    # Pre-roll converges the high-pass state to the preceding loop, preserving
    # boundary continuity instead of resetting filter state at the loop head.
    guard = RATE
    filtered = sosfilt(butter(2, 38, btype='highpass', fs=RATE, output='sos'),
                       np.concatenate((audio[-guard:], audio)), axis=0)[guard:]
    return filtered.astype(np.float32), wraps


def command(args):
    result = subprocess.run([str(arg) for arg in args], capture_output=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result


def measure(ffmpeg, path):
    result = command((ffmpeg, '-hide_banner', '-nostdin', '-i', path,
                      '-af', 'loudnorm=I=-21:TP=-3:LRA=11:print_format=json', '-f', 'null', '-'))
    return json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind('{'):])[0]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_meta(path):
    meta = path.with_suffix(path.suffix + '.meta')
    if not meta.exists():
        write_json(meta, {'ver': '1.0.0', 'importer': 'audio-clip', 'imported': True,
                         'uuid': str(uuid.uuid4()), 'files': ['.json', '.mp3'],
                         'subMetas': {}, 'userData': {'downloadMode': 0}})


def export(shared, ffmpeg, mode):
    notes = score(shared, mode)
    audio, wraps = render(shared, notes, mode)
    identifier = TRACKS[mode]
    master = SOURCE / f'music-{mode}-master.flac'
    asset = RUNTIME / (identifier + '.mp3')
    with tempfile.TemporaryDirectory(prefix='sword-fire-music-loop-') as folder:
        folder = Path(folder)
        raw = folder / 'raw.wav'
        wavfile.write(raw, RATE, audio)
        measured = measure(ffmpeg, raw)
        gain = min(10 ** ((-21 - float(measured['input_i'])) / 20),
                   10 ** (-3.5 / 20) / max(1e-9, float(np.max(np.abs(audio)))))
        audio *= gain
        wavfile.write(raw, RATE, audio)
        command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', raw,
                 '-c:a', 'flac', '-sample_fmt', 's32', '-bits_per_raw_sample', 24, master))
        encoders = command((ffmpeg, '-hide_banner', '-encoders')).stdout
        encoder = 'libmp3lame' if 'libmp3lame' in encoders else 'mp3_mf'
        encoded = folder / 'encoded.mp3'
        command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', master,
                 '-c:a', encoder, '-b:a', '128k', '-ar', RATE,
                 '-metadata', f'title=余烬与誓言 · {"探索" if mode == "explore" else "交战"}', encoded))
        command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', encoded, '-c:a', 'copy', asset))
        decoded = folder / 'decoded.wav'
        command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', asset, decoded))
        decoded_rate, pcm = wavfile.read(decoded)
        output_metrics = measure(ffmpeg, asset)
        master_metrics = measure(ffmpeg, master)
    write_meta(asset)
    note_report = {'mode': mode, 'bpm': BPM, 'bars': BARS, 'meter': '4/4',
                   'modeName': 'D Dorian', 'seconds': SECONDS,
                   'loopNotFadeOut': True, 'tailWrappedNotes': wraps,
                   'heldUnit': 'beats', 'notes': [asdict(note) for note in notes]}
    write_json(SOURCE / f'music-{mode}-score.json', note_report)
    differences = np.abs(np.diff(audio, axis=0))
    boundary_step = float(np.max(np.abs(audio[-1] - audio[0])))
    decoded_audio = pcm.astype(np.float64) / 32768
    mono = audio.mean(axis=1)
    report = {
        'mode': mode, 'asset': str(asset.relative_to(ROOT)).replace('\\', '/'),
        'resourcePath': 'audio/music/' + identifier,
        'master': str(master.relative_to(ROOT)).replace('\\', '/'),
        'bpm': BPM, 'bars': BARS, 'modeName': 'D Dorian',
        'authoredSeconds': SECONDS, 'authoredFrames': FRAMES, 'sampleRate': RATE, 'channels': 2,
        'runtimeBytes': asset.stat().st_size, 'encoder': encoder,
        'decodedMp3Seconds': len(pcm) / decoded_rate,
        'decodedMp3ExtraSeconds': len(pcm) / decoded_rate - SECONDS,
        'masterIntegratedLufs': float(master_metrics['input_i']),
        'masterTruePeakDbtp': float(master_metrics['input_tp']),
        'mp3IntegratedLufs': float(output_metrics['input_i']),
        'mp3TruePeakDbtp': float(output_metrics['input_tp']),
        'clippingSamples': int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767)),
        'masterLoopBoundaryStep': boundary_step,
        'masterMaxAdjacentStep': float(np.max(differences)),
        'master99PercentAdjacentStep': float(np.percentile(differences, 99)),
        'decodedMp3BoundaryStep': float(np.max(np.abs(decoded_audio[-1] - decoded_audio[0]))),
        'masterFirst100msRms': float(np.sqrt(np.mean(audio[:4410] ** 2))),
        'masterLast100msRms': float(np.sqrt(np.mean(audio[-4410:] ** 2))),
        'monoRmsVsStereoRmsDb': float(20 * math.log10(max(1e-12, np.sqrt(np.mean(mono ** 2))) / np.sqrt(np.mean(audio ** 2)))),
        'tailWrappedNotes': wraps,
        'production': 'Original loop score based on accepted A timbres/motif, circular note releases and circular room; no start/end fade.',
        'sha256': hashlib.sha256(asset.read_bytes()).hexdigest(),
        'acceptance': {'composition': 'Loop-authored score; not the 30s or 45s study looped',
                       'numerical': 'Measured master/MP3 loudness, clipping, boundary samples and exact authored length',
                       'listening': 'Pending listening in the actual mixed game',
                       'deviceLoopAndInterruption': 'Pending TapTap target-device audition; MP3 padding is not claimed sample-gapless'},
    }
    write_json(SOURCE / f'music-{mode}-technical.json', report)
    print(json.dumps({key: report[key] for key in ('mode', 'runtimeBytes', 'masterIntegratedLufs', 'mp3TruePeakDbtp', 'masterLoopBoundaryStep', 'decodedMp3ExtraSeconds')}, ensure_ascii=False), flush=True)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=DEFAULT_FFMPEG)
    parser.add_argument('--only', choices=tuple(TRACKS))
    args = parser.parse_args(argv)
    if not args.ffmpeg.is_file():
        parser.error('Provide an installed FFmpeg path; downloading is never attempted.')
    SOURCE.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    shared = original_instruments()
    reports = []
    for mode in TRACKS:
        if args.only and mode != args.only:
            continue
        reports.append(export(shared, args.ffmpeg, mode))
    for path in SOURCE.glob('music-*-technical.json'):
        report = json.loads(path.read_text(encoding='utf-8'))
        if not any(item['mode'] == report['mode'] for item in reports):
            reports.append(report)
    has_aftermath = any(report['mode'] == 'aftermath' for report in reports)
    write_json(SOURCE / 'music-manifest.json', {
        'theme': '余烬与誓言 / Embers and Oaths', 'selectedDirection': 'A',
        'productionDate': '2026-11-16', 'bpm': BPM, 'mode': 'D Dorian',
        'sourceReference': 'source-art/audio/direction-studies-v2/music/a-embers-and-oaths/score.json',
        'instrumentSource': 'src/cocos/tools/audio-direction-v2/music_samples.py',
        'generator': 'src/cocos/tools/audio-runtime-v1/make_music_loops.py',
        'authorship': 'Original project score and synthetic acoustic-inspired timbres. No real instrument recordings, third-party samples, new dependencies, AI calls or downloads.',
        'runtime': ('Exploration and combat use two phase-positioned premixed loops; the independent 15-second aftermath is a non-looping settling phrase for the combat-exit state.' if has_aftermath else 'Two premixed loops and two Cocos AudioSources; mode changes request one approximate duration-normalized position match before crossfade, without sample-synchronous multitrack dependence.'),
        'additionalGenerators': ['src/cocos/tools/audio-runtime-v1/make_music_aftermath.py'] if has_aftermath else [],
        'boss': 'Uses the combat track; no independent Boss score is supplied or claimed.',
        'tracks': reports,
    })


if __name__ == '__main__':
    main()
