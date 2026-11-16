"""Original listening studies, build time only; importing never writes files.

Reuses the existing dawn-embers score's Dorian vocabulary and instrumentation,
with modal plucked strings, breath-shaped woodwind and ensemble string models.
These are synthesized timbres, not recordings of real acoustic instruments.
No downloaded recordings, soundfonts, AI model calls or runtime dependencies.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt


REPO = Path(__file__).resolve().parents[4]
OUTPUT = REPO / 'source-art/audio/direction-studies-v2/music'
RATE = 44100
BPM = 80
BEAT = 60 / BPM
SEED = 2026111602
STEMS = ('melody', 'plucked', 'strings', 'percussion', 'bronze')
DEFAULT_FFMPEG = Path('C:/Program Files (x86)/Lenovo/LegionZone/2.0.30.11033/SEGamingAI/services/editor/ffmpeg.exe')


@dataclass(frozen=True)
class Note:
    instrument: str
    stem: str
    midi: int
    beat: float
    held: float
    level: float
    pan: float = 0


def fade_envelope(t, held, attack, release):
    onset = np.sin(np.clip(t / attack, 0, 1) * np.pi / 2) ** 2
    ending = np.cos(np.clip((t - held) / release, 0, 1) * np.pi / 2) ** 2
    return onset * ending


def filtered_noise(rng, count, low, high):
    return sosfilt(butter(2, [low, high], fs=RATE, btype='bandpass', output='sos'), rng.normal(0, 1, count))


@lru_cache(maxsize=384)
def instrument(kind: str, midi: int, held: float):
    """Band-limited modal resonators, bowed ensemble and breath-shaped flutes."""
    rng = np.random.default_rng(SEED + midi * 103 + sum(map(ord, kind)) * 7 + round(held * 100))
    release = {'lute': 1.2, 'harp': 1.55, 'flute': .42, 'low-flute': .55,
               'strings': .8, 'cello': .65, 'bronze': 2.2, 'drum': .62,
               'frame-drum': .28, 'shaker': .12}[kind]
    t = np.arange(round((held + release) * RATE), dtype=np.float64) / RATE
    f = 440 * 2 ** ((midi - 69) / 12)
    result = np.zeros(len(t), np.float64)
    if kind in ('lute', 'harp'):
        # Pluck position, frequency-dependent decay and stiff-string dispersion.
        for partial in range(1, min(36, int(10000 / f)) + 1):
            position = .21 if kind == 'lute' else .29
            weight = math.sin(np.pi * partial * position) / partial ** 1.13
            decay = (1.7 if kind == 'lute' else 1.05) + partial * (.12 if kind == 'lute' else .09)
            detune = 1 + .000025 * partial ** 2
            result += weight * np.sin(2 * np.pi * f * partial * detune * t) * np.exp(-t * decay)
        # Short wooden body resonances and a tiny finger excitation, not a click.
        exc = filtered_noise(rng, len(t), 650, 6200) * np.exp(-t * 85)
        body = sum(.035 * np.sin(2 * np.pi * mode * t) * np.exp(-t * 16) for mode in (185, 295, 430))
        result = result * .53 + exc * .055 + body
        result *= fade_envelope(t, held, .0035, release)
    elif kind in ('flute', 'low-flute'):
        vibrato = (.0017 if kind == 'flute' else .0011) * (1 - np.exp(-t / .28))
        # Integrating the instantaneous frequency avoids phase discontinuities.
        drift = .0005 * np.sin(t * 2 * np.pi * .73 + .4)
        frequency = f * (1 + vibrato * np.sin(2 * np.pi * 4.7 * t) + drift)
        phase = np.cumsum(frequency) * (2 * np.pi / RATE)
        color = [1, .19, .11, .042, .018] if kind == 'flute' else [1, .31, .075, .027, .014]
        for harmonic, weight in enumerate(color, 1):
            result += weight * np.sin(phase * harmonic + .08 * harmonic)
        breath = filtered_noise(rng, len(t), 700 if kind == 'flute' else 350, 4800)
        result = .53 * result + .037 * breath
        result *= fade_envelope(t, held, .075 if kind == 'flute' else .12, release)
        result *= .98 + .02 * np.sin(2 * np.pi * 2.3 * t)
    elif kind in ('strings', 'cello'):
        # Five independent beating voices, evolving bow brightness and bow noise.
        for voice, cents in enumerate((-6.4, -2.6, .4, 3.1, 7.3)):
            vibrato = .00125 * np.sin(2 * np.pi * (4.25 + voice * .17) * t + voice * .92)
            wander = .00038 * np.sin(2 * np.pi * (.31 + voice * .035) * t + voice)
            phase = np.cumsum(f * 2 ** (cents / 1200) * (1 + vibrato + wander)) * 2 * np.pi / RATE
            for harmonic in range(1, min(19, int(6500 / f)) + 1):
                bow_position = .12 if kind == 'strings' else .18
                weight = math.sin(np.pi * harmonic * bow_position) / harmonic ** 1.7
                result += .2 * weight * np.sin(phase * harmonic + voice * .61)
        bow = filtered_noise(rng, len(t), 250, 3200) * .012
        result = (result + bow) * fade_envelope(t, held, .34 if kind == 'strings' else .19, release)
        result *= 1 + .035 * np.sin(t * 2 * np.pi * .67)
    elif kind == 'bronze':
        # Unequal partials: an old bronze bowl, not a tuned synth sine bell.
        for ratio, level in ((1, .62), (1.51, .17), (2.11, .12), (2.77, .095), (4.08, .032)):
            result += level * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * (.65 + ratio * .44))
        result *= fade_envelope(t, held, .008, release)
    elif kind in ('drum', 'frame-drum'):
        base = 72 if kind == 'drum' else 156
        decay = 8.5 if kind == 'drum' else 17
        phase = 2 * np.pi * (base * t + 19 * .035 * (1 - np.exp(-t / .035)))
        membrane = .76 * np.sin(phase) + .16 * np.sin(phase * 1.59)
        noise = filtered_noise(rng, len(t), 200, 3000) * np.exp(-t * 38)
        result = (membrane * np.exp(-t * decay) + noise * .14) * np.minimum(t / .003, 1)
        result *= fade_envelope(t, held, .003, release)
    else:
        result = filtered_noise(rng, len(t), 2600, 10000) * np.exp(-t * 44)
        result *= fade_envelope(t, held, .012, release) * .5
    return result.astype(np.float32)


# Shared original melody in the opening D-F-E-D vocabulary of dawn-embers.
# No borrowed game melody. Bar four is a deliberate one-bar melodic breath.
MELODY = (
    ((.5, 74, .65), (1.5, 77, .75), (2.5, 76, .6), (3.25, 74, .55)),
    ((0, 69, 1.4), (2, 71, 1.1)),
    ((.5, 74, 1.1), (2, 76, .65), (3, 79, .7)),
    ((0, 77, 1.2), (2, 76, .65), (3, 74, .6)),
    (),
    ((.5, 74, .65), (1.5, 77, .75), (2.5, 76, .6), (3.25, 74, .55)),
    ((0, 71, 1.15), (1.5, 69, .8), (3, 67, .65)),
    ((0, 69, 1.25), (2, 72, .7), (3, 74, .6)),
    ((0, 76, 1.4), (2, 74, 1.15)),
    ((0, 74, 1.35),),
)
HARMONY = (
    (38, (50, 57, 65)), (43, (50, 59, 67)),
    (41, (53, 60, 69)), (36, (52, 55, 62)),
    (40, (52, 59, 67)), (45, (52, 57, 64)),
    (43, (50, 57, 62)), (38, (50, 57, 65)),
    (45, (52, 57, 64)), (38, (50, 57, 65)),
)


def make_score(direction):
    notes = []

    def add(kind, stem, pitch, beat, held, level, pan=0):
        notes.append(Note(kind, stem, pitch, round(beat, 5), held, level, pan))

    for bar, (root, chord) in enumerate(HARMONY):
        final = bar == 9
        b = bar * 4
        energy = .8 if bar == 4 else 1.08 if 5 <= bar <= 7 else 1
        hold = 1.25 if final else 3.3
        for pos, pitch in enumerate(chord):
            add('strings', 'strings', pitch, b + pos * .018, hold,
                (.19 if direction == 'B' else .11 if direction == 'A' else .065) * energy,
                (-.55, .25, .53)[pos])
        add('cello', 'strings', root, b + .025, hold,
            (.29 if direction == 'B' else .18 if direction == 'A' else .12) * energy, -.08)
        if direction == 'B':
            pattern = ((0, root + 12), (2.5, chord[1])) if not final else ((0, root + 12),)
        else:
            pattern = tuple((beat, pitch) for beat, pitch in zip(
                (0, .75, 1.5, 2.5, 3.25),
                (root + 12, chord[0] + 12, chord[2], chord[1] + 12, chord[0] + 12)))
            if final:
                pattern = pattern[:2]
        for i, (offset, pitch) in enumerate(pattern):
            add('lute', 'plucked', pitch, b + offset, .45,
                (.145 if direction == 'A' else .07 if direction == 'B' else .22) * energy * (1 if i % 2 == 0 else .78), -.32)
        if direction in ('A', 'C') and bar in (1, 3, 5, 7):
            for i, pitch in enumerate((chord[1] + 12, chord[2] + 12)):
                add('harp', 'plucked', pitch, b + 2.7 + .5 * i, .55,
                    .062 if direction == 'A' else .105, .38)
        for offset, pitch, length in MELODY[bar]:
            kind, octave = ('low-flute', -12) if direction == 'B' else ('flute', 0)
            add(kind, 'melody', pitch + octave, b + offset, length,
                .22 if direction == 'A' else .17 if direction == 'B' else .255, .02)
            if direction == 'B':
                add('cello', 'melody', pitch - 24, b + offset + .04, length, .14, -.12)
        if not final:
            if direction == 'B':
                for offset, level in ((0, .23), (1.5, .075), (2.5, .12)):
                    add('drum', 'percussion', 36, b + offset, .08, level * energy, -.12 if offset == 1.5 else 0)
            elif direction == 'A':
                if bar != 4:
                    add('drum', 'percussion', 36, b, .08, .115 * energy)
                    add('frame-drum', 'percussion', 48, b + 2.5, .055, .055 * energy, .22)
            else:
                add('frame-drum', 'percussion', 48, b, .06, .105)
                add('frame-drum', 'percussion', 48, b + 2, .05, .06, .2)
                if bar >= 2:
                    for offset in (.5, 1.5, 2.5, 3.5):
                        add('shaker', 'percussion', 60, b + offset, .055, .075, .35)
        if bar in (0, 4, 8):
            add('bronze', 'bronze', 50 if direction == 'B' else 62, b + .06, .15,
                .055 if direction == 'A' else .09 if direction == 'B' else .028, .38)
    return notes


def room(signal, seed, wet=.13):
    """Finite early reflections and a filtered diffuse room; tail remains in file."""
    rng = np.random.default_rng(seed)
    count = round(1.55 * RATE)
    t = np.arange(count) / RATE
    impulse = np.zeros((count, 2), np.float32)
    for channel in range(2):
        for delay, gain in ((.029, .23), (.053, .17), (.087, .12), (.137, .085)):
            impulse[round((delay + channel * .006) * RATE), channel] += gain
        diffuse = sosfilt(butter(2, 3400, fs=RATE, output='sos'), rng.normal(0, 1, count))
        impulse[:, channel] += (diffuse * np.exp(-t * 4.8) * np.minimum(t / .045, 1) * .006).astype(np.float32)
    for channel in range(2):
        signal[:, channel] += wet * fftconvolve(signal[:, channel], impulse[:, channel])[:len(signal)]
    return signal


def render(notes, seconds, room_seed=0):
    frames = round(seconds * RATE)
    stems = {stem: np.zeros((frames, 2), np.float32) for stem in STEMS}
    truncated = []
    for note in notes:
        sound = instrument(note.instrument, note.midi, round(note.held * BEAT, 5)) * note.level
        angle = (note.pan + 1) * np.pi / 4
        stereo = sound[:, None] * np.array((np.cos(angle), np.sin(angle)), np.float32)
        begin = round(note.beat * BEAT * RATE)
        length = min(len(stereo), frames - begin)
        if length <= 0:
            continue
        if length < len(stereo) and float(np.max(np.abs(stereo[length:]))) > .0001:
            truncated.append(asdict(note))
        stems[note.stem][begin:begin + length] += stereo[:length]
    if truncated:
        raise ValueError(f'Unfinished note tails at end: {truncated}')
    for index, (name, stem) in enumerate(stems.items()):
        room(stem, SEED + room_seed + index, .075 if name == 'percussion' else .17)
        stem[:] = sosfilt(butter(2, 38, fs=RATE, btype='highpass', output='sos'), stem, axis=0)
        # Last scored note finishes naturally before this very short output guard.
        fade_in = min(round(.018 * RATE), frames)
        fade_out = min(round(.15 * RATE), frames)
        stem[:fade_in] *= np.linspace(0, 1, fade_in, dtype=np.float32)[:, None]
        stem[-fade_out:] *= np.linspace(1, 0, fade_out, dtype=np.float32)[:, None]
    return stems


def make_demo():
    """15 seconds each exploration, combat, aftermath at the same 80 BPM grid."""
    exploration = make_score('A')
    notes = [note for note in exploration if note.beat < 20]
    # Hold a restrained ostinato rather than bringing a melody into hit transients.
    for bar in range(5, 10):
        root, chord = HARMONY[bar % 10]
        b = bar * 4
        for i, pitch in enumerate(chord):
            notes.append(Note('strings', 'strings', pitch, b + .012 * i, 3.15, .15, (-.52, .18, .5)[i]))
        notes.append(Note('cello', 'strings', root, b, 3.0, .24, -.06))
        for i in range(8):
            pitch = (root + 12, chord[0] + 12, chord[1] + 12, chord[0] + 12)[i % 4]
            notes.append(Note('lute', 'plucked', pitch, b + .5 * i, .3, .17 if i % 2 == 0 else .10, -.24))
        for offset, amp in ((0, .19), (1.5, .08), (2, .12), (3, .09)):
            notes.append(Note('drum', 'percussion', 36, b + offset, .075, amp))
        for offset in (.75, 2.75):
            notes.append(Note('frame-drum', 'percussion', 48, b + offset, .055, .085, .24))
        if bar in (5, 8):
            for offset, pitch, held in ((.5, 62, .6), (1.5, 65, .65), (2.5, 64, .6), (3.25, 62, .5)):
                notes.append(Note('low-flute', 'melody', pitch, b + offset, held, .13, -.04))
    # A complete five-bar return: more air, no drum groove and a resolved D minor.
    after_harmony = ((41, (53, 60, 69)), (43, (50, 59, 67)), (45, (52, 57, 64)),
                     (38, (50, 57, 65)), (38, (50, 57, 65)))
    for index, (root, chord) in enumerate(after_harmony):
        b = 40 + index * 4
        final = index == 4
        held = .95 if final else 3.0
        for i, pitch in enumerate(chord):
            notes.append(Note('strings', 'strings', pitch, b + i * .018, held, .09, (-.5, .2, .45)[i]))
        notes.append(Note('cello', 'strings', root, b, held, .15, -.06))
        for i, pitch in enumerate((chord[0] + 12, chord[1] + 12)):
            notes.append(Note('harp', 'plucked', pitch, b + .75 * i, .45, .11 if not final else .075, -.28 + i * .5))
        if index in (1, 2, 3):
            phrase = {1: ((.5, 74, 1.1), (2, 77, .8)),
                      2: ((0, 76, 1.2), (2, 74, 1.0)),
                      3: ((0, 69, 1.0), (1.5, 74, 1.0))}[index]
            for offset, pitch, duration in phrase:
                notes.append(Note('flute', 'melody', pitch, b + offset, duration, .17))
        if index == 0:
            notes.append(Note('bronze', 'bronze', 62, b + .15, .15, .045, .35))
    stems = render(notes, 45, 900)
    # Musical layers overlap naturally across boundaries. Additional slow gain
    # ramps prevent a newly entering beat from sounding like an abrupt edit.
    timeline = np.arange(round(45 * RATE)) / RATE
    ramp = lambda a, b: .5 - .5 * np.cos(np.pi * np.clip((timeline - a) / (b - a), 0, 1))
    combat_window = ramp(14.25, 16.5) * (1 - ramp(29.25, 31.5))
    for name in ('percussion', 'plucked'):
        stems[name] *= (.83 + .17 * combat_window)[:, None]
    cues = [
        {'id': 'exploration', 'fromSeconds': 0, 'toSeconds': 15,
         'note': 'Warm exploration; leave opening motif unobstructed.'},
        {'id': 'combat', 'fromSeconds': 15, 'toSeconds': 30,
         'note': 'Restraint in lead register; intended window for later class SFX overlay.'},
        {'id': 'aftermath', 'fromSeconds': 30, 'toSeconds': 45,
         'note': 'Percussion releases into quiet theme return and complete ending.'},
    ]
    return notes, stems, cues


def command(args):
    result = subprocess.run([str(arg) for arg in args], capture_output=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result


def measure(ffmpeg, path):
    result = command((ffmpeg, '-hide_banner', '-nostdin', '-i', path,
                      '-af', 'loudnorm=I=-20:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'))
    return json.JSONDecoder().raw_decode(result.stderr[result.stderr.rfind('{'):])[0]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_study(ffmpeg, folder, identifier, title, notes, stems, seconds, cues=None):
    folder.mkdir(parents=True, exist_ok=True)
    stem_folder = folder / 'stems'
    stem_folder.mkdir(exist_ok=True)
    mixed = np.sum(np.stack(list(stems.values())), axis=0)
    temp = folder / '_measurement.wav'
    wavfile.write(temp, RATE, mixed)
    loudness = measure(ffmpeg, temp)
    temp.unlink()
    # A single linear gain preserves performance dynamics and exact stem balance.
    target_lufs = -20 if seconds == 30 else -22
    requested_db = target_lufs - float(loudness['input_i'])
    peak = float(np.max(np.abs(mixed)))
    ceiling_gain = 10 ** (-3 / 20) / max(peak, 1e-9)
    gain = min(10 ** (requested_db / 20), ceiling_gain)
    mixed *= gain
    paths = {}
    reconstructed = np.zeros_like(mixed)
    for stem, audio in stems.items():
        audio *= gain
        path = stem_folder / (stem + '.flac')
        temporary_stem = stem_folder / '_float.wav'
        wavfile.write(temporary_stem, RATE, audio)
        # Common gain remains unchanged; 24-bit FLAC avoids large float masters.
        command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', temporary_stem,
                 '-c:a', 'flac', '-sample_fmt', 's32', '-bits_per_raw_sample', '24',
                 '-compression_level', '8', path))
        temporary_stem.unlink()
        # Raw PCM is binary, so decoding uses a separate bytes-mode process.
        raw = subprocess.run([str(ffmpeg), '-v', 'error', '-i', str(path),
                              '-f', 'f32le', '-c:a', 'pcm_f32le', '-'],
                             capture_output=True, check=True).stdout
        reconstructed += np.frombuffer(raw, np.float32).reshape(-1, 2)
        paths[stem] = str(path.relative_to(OUTPUT)).replace('\\', '/')
    master = folder / (identifier + '.wav')
    master_pcm = (np.clip(mixed, -1, 1) * 32767).round().astype(np.int16)
    wavfile.write(master, RATE, master_pcm)
    stem_error = float(np.max(np.abs(reconstructed - master_pcm.astype(np.float32) / 32767)))
    allowed_error = .5 / 32767 + len(stems) / (2 ** 23) + 1e-7
    mp3 = folder / (identifier + '.mp3')
    encoder_list = command((ffmpeg, '-hide_banner', '-encoders')).stdout
    encoder = 'libmp3lame' if 'libmp3lame' in encoder_list else 'mp3_mf'
    encoded = folder / '_encoded.mp3'
    command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', master,
             '-c:a', encoder, '-b:a', '160k', '-ar', RATE,
             '-metadata', 'title=' + title, encoded))
    # Media Foundation's grouped packets need parsed-frame remuxing for Xing.
    command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', encoded, '-c:a', 'copy', mp3))
    encoded.unlink()
    decoded = folder / '_decoded.wav'
    command((ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', mp3, decoded))
    rate, pcm = wavfile.read(decoded)
    decoded.unlink()
    normalized = pcm.astype(np.float64) / 32768
    metrics = measure(ffmpeg, master)
    encoded_metrics = measure(ffmpeg, mp3)
    report = {
        'id': identifier, 'title': title,
        'sampleRate': RATE, 'channels': 2, 'authoredSeconds': seconds,
        'wavFrames': len(mixed), 'decodedMp3Seconds': len(pcm) / rate,
        'peakDbfs': round(20 * math.log10(max(float(np.max(np.abs(mixed))), 1e-12)), 3),
        'integratedLufs': float(metrics['input_i']), 'truePeakDbtp': float(metrics['input_tp']),
        'truePeakMeasurementSource': 'PCM16 WAV master',
        'mp3IntegratedLufs': float(encoded_metrics['input_i']),
        'mp3TruePeakDbtp': float(encoded_metrics['input_tp']),
        'targetLufs': target_lufs, 'linearMasterGain': gain,
        'wavClippingSamples': int(np.sum(np.abs(mixed) >= 1)),
        'mp3ClippingSamples': int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767)),
        'mp3PeakDbfs': round(20 * math.log10(max(float(np.max(np.abs(normalized))), 1e-12)), 3),
        'first50msRms': float(np.sqrt(np.mean(mixed[:round(.05 * RATE)] ** 2))),
        'last50msRms': float(np.sqrt(np.mean(mixed[-round(.05 * RATE):] ** 2))),
        'mp3Bytes': mp3.stat().st_size,
        'sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (master, mp3)},
        'stems': paths, 'stemFormat': '24-bit stereo FLAC, same gain and exact frame alignment; no per-stem normalization',
        'sumOfStemsMatchesMasterWithinQuantizationError': stem_error <= allowed_error,
        'summedStemVsPcm16MasterMaxError': stem_error,
        'allowedQuantizationError': allowed_error,
        'stemFilesBytes': sum((OUTPUT / path).stat().st_size for path in paths.values()),
        'bpm': BPM, 'meter': '4/4', 'mode': 'D Dorian',
        'synthesis': 'Original procedural acoustic-inspired models, no real instrument recordings',
        'technicalChecks': 'Exact frame count, note-tail fit, loudness/peak, clipping and MP3 decode measured',
        'listeningAcceptance': 'pending user audition',
        'runtimeIntegration': 'not integrated; listening study only',
        'taptapDeviceAcceptance': 'not performed',
    }
    write_json(folder / 'score.json', {'id': identifier, 'bpm': BPM, 'beatSeconds': BEAT,
                                      'seconds': seconds, 'notes': [asdict(note) for note in notes]})
    if cues:
        write_json(folder / 'cues.json', {'seconds': seconds, 'cues': cues,
                   'softTransitionWindowsSeconds': [[14.25, 16.5], [29.25, 31.5]],
                   'sfxOverlayRecommendedSeconds': [15.8, 28.5],
                   'musicOnlyWav': str(master.relative_to(OUTPUT)).replace('\\', '/')})
    write_json(folder / 'technical-report.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=DEFAULT_FFMPEG)
    parser.add_argument('--only', choices=('A', 'B', 'C', 'demo'))
    args = parser.parse_args(argv)
    if not args.ffmpeg.is_file():
        parser.error('Provide --ffmpeg pointing to an existing FFmpeg binary; no download is attempted.')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    definitions = (
        ('A', 'a-embers-and-oaths', 'A 余烬与誓言', 'Warm ancient fantasy: plucked strings, woodwind, bowed ensemble and old bronze.'),
        ('B', 'b-dark-expedition', 'B 暗色远征', 'Low airy woodwind, dark strings, irregular low drums and spare plucks.'),
        ('C', 'c-bright-adventure', 'C 明亮冒险', 'Brighter woodwind and fingerpicked strings with light frame-drum pulse.'),
    )
    reports = []
    for direction, identifier, title, intent in definitions:
        if args.only and args.only != direction:
            continue
        notes = make_score(direction)
        stems = render(notes, 30, ord(direction))
        report = write_study(args.ffmpeg, OUTPUT / identifier, identifier, title, notes, stems, 30)
        report['intent'] = intent
        reports.append(report)
        print(json.dumps({key: report[key] for key in ('id', 'authoredSeconds', 'integratedLufs', 'peakDbfs', 'wavClippingSamples')}, ensure_ascii=False), flush=True)
    if not args.only or args.only == 'demo':
        notes, stems, cues = make_demo()
        report = write_study(args.ffmpeg, OUTPUT / 'a-adaptive-demo', 'a-adaptive-demo',
                             '余烬与誓言：探索、交战、战后', notes, stems, 45, cues)
        reports.append(report)
        print(json.dumps({key: report[key] for key in ('id', 'authoredSeconds', 'integratedLufs', 'peakDbfs', 'wavClippingSamples')}, ensure_ascii=False), flush=True)
    manifest = {
        'title': '剑与火音乐方向小样 v2', 'productionDate': '2026-11-16',
        'provenance': 'Original authored music and deterministic local synthesis; no cloud generation, third-party recordings, soundfonts or downloads.',
        'previousReference': 'source-art/audio/dawn-embers-v1/score.json',
        'sharedComparison': {'bpm': BPM, 'bars': 10, 'seconds': 30, 'mode': 'D Dorian',
                             'motifPitchClasses': ['D', 'F', 'E', 'D'],
                             'melodyTimingIsShared': True,
                             'darkVersionMelodyOctave': -1,
                             'note': 'B uses low flute an octave down with cello support; same phrase timing and harmony.'},
        'demo': {'seconds': 45, 'sections': ['0–15 exploration', '15–30 combat', '30–45 aftermath'],
                 'note': 'Demonstrates authored transitions, not a currently integrated adaptive-music system.'},
        'generator': 'src/cocos/tools/audio-direction-v2/music_samples.py',
        'acceptance': {'technical': 'See each measured technical-report.json',
                       'musical': 'Pending user listening; no claim of having listened',
                       'platform': 'Not integrated or TapTap/device tested'},
        'studies': reports,
    }
    # Re-entrant --only reruns retain reports from the other already-rendered studies.
    for path in sorted(OUTPUT.glob('*/technical-report.json')):
        report = json.loads(path.read_text(encoding='utf-8'))
        if not any(item['id'] == report['id'] for item in manifest['studies']):
            manifest['studies'].append(report)
    write_json(OUTPUT / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
