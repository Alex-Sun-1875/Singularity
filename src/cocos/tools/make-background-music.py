"""Render the original 32-bar exploration cue; no model or downloaded samples.

Build-time only: reuse NumPy/SciPy and the installed FFmpeg. The game ships a
single compressed recording, with no synthesizer or Python runtime dependency.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parents[1] / 'source-art/audio/dawn-embers-v1'
RUNTIME = PROJECT / 'assets/resources/audio/music/dawn-embers.mp3'
RATE = 44100
BPM = 80
BEAT = 60 / BPM
BARS = 32
SECONDS = BARS * 4 * BEAT
FRAMES = round(SECONDS * RATE)
RNG = np.random.default_rng(110_2026)


def envelope(t, held, attack, release):
    onset = np.sin(np.minimum(t / attack, 1) * np.pi / 2) ** 2
    end = np.cos(np.clip((t - held) / release, 0, 1) * np.pi / 2) ** 2
    return onset * end


def instrument(kind, pitch, held):
    """Acoustic-inspired timbres, with explicit note releases and band limits."""
    release = {'lute': 1.6, 'harp': 2.4, 'flute': .32, 'strings': .85,
               'cello': .65, 'bell': 3.8, 'drum': .48}[kind]
    duration = min(held + release, 8)
    t = np.arange(round(duration * RATE), dtype=np.float64) / RATE
    f = 440 * 2 ** ((pitch - 69) / 12)
    y = np.zeros_like(t)
    if kind in ('lute', 'harp'):
        decay = 1.7 if kind == 'lute' else 1.05
        for h in range(1, 13):
            if f * h > RATE * .42:
                break
            # Pick position suppresses some harmonics; upper partials decay faster.
            weight = math.sin(h * .29 * math.pi) / h ** 1.6
            y += weight * np.sin(2 * np.pi * f * h * t) * np.exp(-t * decay * (1 + h * .22))
        y *= envelope(t, held, .004, release)
    elif kind == 'flute':
        phase = 2 * np.pi * f * t + .28 * (1 - np.exp(-t * 2)) * np.sin(2 * np.pi * 5.05 * t)
        y = np.sin(phase) + .13 * np.sin(phase * 2) + .065 * np.sin(phase * 3)
        breath = sosfilt(butter(2, [900, 4800], 'bandpass', fs=RATE, output='sos'), RNG.normal(0, .028, len(t)))
        y = (y * .63 + breath) * envelope(t, held, .12, release)
        y *= 1 + .035 * np.sin(2 * np.pi * 3.7 * t)
    elif kind in ('strings', 'cello'):
        for detune, phase in [(-.0021, .4), (0, 1.8), (.0017, 3.1)]:
            fundamental = 2 * np.pi * f * (1 + detune) * t
            fundamental += .22 * np.sin(2 * np.pi * (4.6 + detune * 60) * t + phase)
            for h in range(1, 11):
                if f * h > 6500:
                    break
                y += np.sin(fundamental * h + phase) / h ** 1.7 / 3
        y *= envelope(t, held, .45 if kind == 'strings' else .22, release) * .55
        y *= .94 + .06 * np.sin(2 * np.pi * .7 * t)
    elif kind == 'bell':
        for ratio, level in [(1, .7), (2.01, .23), (2.76, .13), (4.07, .06), (5.43, .025)]:
            y += level * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * (.85 + ratio * .34))
        y *= envelope(t, held, .006, release)
    else:
        phase = 2 * np.pi * (58 * t + 32 * .022 * (1 - np.exp(-t / .022)))
        skin = sosfilt(butter(2, 1200, fs=RATE, output='sos'), RNG.normal(0, .13, len(t)))
        y = (.65 * np.sin(phase) + skin) * np.exp(-t * 10) * np.minimum(t / .002, 1)
    return y.astype(np.float32)


def score():
    notes = []

    def add(kind, pitch, beat, duration, level, pan=0):
        notes.append(dict(instrument=kind, midi=pitch, beat=round(beat, 4),
                          beats=duration, level=round(level, 4), pan=pan))

    # D Dorian: D E F G A B C. Eight-bar returns, with gently changing voicings.
    harmony = [
        (38, [62, 65, 69, 76]), (43, [62, 67, 71, 76]),
        (41, [60, 65, 69, 76]), (36, [60, 64, 67, 74]),
        (40, [62, 64, 67, 71]), (45, [60, 64, 69, 74]),
        (43, [62, 67, 69, 71]), (38, [62, 65, 69, 76]),
    ]
    melody = [
        [(1, 74, 1.2), (2.5, 77, 1)],
        [(0, 76, 1.5), (2, 74, .8), (3, 71, .7)],
        [(0, 69, 1.6), (2, 72, .7), (3, 76, .7)],
        [(0, 79, 1.5), (2, 76, .8), (3, 74, .7)],
        [(.5, 71, 1), (2, 74, .7), (3, 76, .7)],
        [(0, 76, 1.5), (2, 72, .7), (3, 69, .7)],
        [(0, 71, 1), (1.5, 74, 1.2), (3, 69, .7)],
        [(0, 76, 1), (1.5, 74, 2.1)],
    ]
    for bar in range(BARS):
        section = bar // 8
        local = bar % 8
        root, chord = harmony[local]
        energy = [1, 1.1, .8, 1.03][section]
        # Humanized eight-note fingerpicking; root + close chord tones stay quiet.
        arpeggio = [root + 12, chord[0], chord[2], chord[1], root + 24, chord[2], chord[3], chord[1]]
        for i, pitch in enumerate(arpeggio):
            time = bar * 4 + i * .5 + (0 if i == 0 else RNG.uniform(-.012, .012))
            add('lute', pitch, time, .47, .14 * energy * (1 if i % 2 == 0 else .76), -.32)
        add('cello', root, bar * 4 + .025, 3.65, .14 * energy, .08)
        for i, pitch in enumerate(chord[:3]):
            add('strings', pitch - 12, bar * 4 + i * .018, 3.8, .057 * energy, [-.45, .3, .5][i])
        # Harp appears around phrase boundaries, leaving space under the melody.
        if local in (0, 2, 4, 6):
            for i, pitch in enumerate([chord[1], chord[2], chord[3]]):
                add('harp', pitch + 12, bar * 4 + 2.5 + i * .5, .7, .065 * energy, .38)
        for offset, pitch, length in melody[local]:
            if section == 2:
                if offset > 2:
                    continue
                pitch -= 12
            elif section == 1 and local >= 4:
                pitch += 0 if local == 7 else 12
            add('flute', pitch, bar * 4 + offset + .02, length, .17 * energy, -.08)
        if section == 1 and local in (1, 3, 5):
            add('strings', chord[2] + 12, bar * 4 + .6, 2.6, .032, .36)
        if section != 2 or local in (2, 6):
            add('drum', 36, bar * 4, .1, .09 * energy)
            add('drum', 36, bar * 4 + 2, .1, .045 * energy, .12)
        if local in (0, 4):
            add('bell', 74 if local == 0 else 81, bar * 4 + .03, .15, .045, .48)
    return notes


def render(notes):
    mix = np.zeros((FRAMES, 2), np.float32)
    cache = {}
    for note in notes:
        key = (note['instrument'], note['midi'], note['beats'])
        if key not in cache:
            cache[key] = instrument(key[0], key[1], key[2] * BEAT)
        signal = cache[key] * note['level']
        angle = (note['pan'] + 1) * np.pi / 4
        stereo = signal[:, None] * np.array([np.cos(angle), np.sin(angle)], np.float32)
        begin = round(note['beat'] * BEAT * RATE) % FRAMES
        count = min(len(signal), FRAMES - begin)
        mix[begin:begin + count] += stereo[:count]
        if count < len(signal):
            mix[:len(signal) - count] += stereo[count:]
    # Circular room convolution preserves the previous phrase's reverb at loop-in.
    for channel in range(2):
        impulse = np.zeros(FRAMES, np.float32)
        for delay, gain in [(.037, .09), (.067, .07), (.103, .055), (.157, .04)]:
            impulse[round((delay + channel * .007) * RATE)] = gain
        length = round(RATE * 2.6)
        t = np.arange(length) / RATE
        diffuse = RNG.normal(0, 1, length) * np.exp(-t * 3.1) * np.minimum(t / .06, 1)
        diffuse = sosfilt(butter(2, 3800, fs=RATE, output='sos'), diffuse)
        impulse[:length] += (diffuse * .00065).astype(np.float32)
        wet = np.fft.irfft(np.fft.rfft(mix[:, channel]) * np.fft.rfft(impulse), n=FRAMES)
        mix[:, channel] += wet.astype(np.float32)
    # Gentle high pass; pre-roll makes the filter state continuous at the boundary.
    guard = RATE
    extended = np.concatenate([mix[-guard:], mix, mix[:guard]])
    mix = sosfilt(butter(2, 40, 'highpass', fs=RATE, output='sos'), extended, axis=0)[guard:guard + FRAMES]
    mix *= .73 / max(np.max(np.abs(mix)), .001)
    return mix.astype(np.float32)


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ffmpeg', required=True)
    args = parser.parse_args()
    encoders = run([args.ffmpeg, '-hide_banner', '-encoders']).stdout
    mp3_encoder = 'libmp3lame' if 'libmp3lame' in encoders else 'mp3_mf'
    SOURCE.mkdir(parents=True, exist_ok=True)
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    notes = score()
    (SOURCE / 'score.json').write_text(json.dumps(dict(title='破晓余烬', bpm=BPM,
        meter='4/4', mode='D Dorian', bars=BARS, seconds=SECONDS,
        sections=['灯下启程', '越过河谷', '铁誓回声', '未熄之火'], notes=notes),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    mix = render(notes)
    with tempfile.TemporaryDirectory(prefix='sword-fire-music-') as folder:
        raw = Path(folder) / 'raw.wav'
        wavfile.write(raw, RATE, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
        base = [args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(raw)]
        measured = run(base + ['-af', 'loudnorm=I=-20:TP=-1.5:LRA=10:print_format=json', '-f', 'null', '-'])
        values = json.JSONDecoder().raw_decode(measured.stderr[measured.stderr.rfind('{'):])[0]
        normalization = ('loudnorm=I=-20:TP=-1.5:LRA=10:linear=true'
            f":measured_I={values['input_i']}:measured_TP={values['input_tp']}"
            f":measured_LRA={values['input_lra']}:measured_thresh={values['input_thresh']}"
            f":offset={values['target_offset']}")
        master = SOURCE / 'dawn-embers-master.flac'
        run(base + ['-af', normalization, '-ar', str(RATE), '-c:a', 'flac', str(master)])
        encoded = Path(folder) / 'encoded.mp3'
        run([args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(master),
             '-c:a', mp3_encoder, '-b:a', '128k', '-ar', str(RATE),
             '-metadata', 'title=破晓余烬 — 剑与火探索主题', str(encoded)])
        # Media Foundation groups MPEG frames per packet. Re-mux parsed frames so
        # Xing duration reflects every frame instead of the encoder packet count.
        run([args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(encoded),
             '-c:a', 'copy', str(RUNTIME)])
        decoded = Path(folder) / 'decoded.wav'
        run([args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(RUNTIME), str(decoded)])
        rate, pcm = wavfile.read(decoded)
        normalized = pcm.astype(np.float64) / 32768
        verification = run([args.ffmpeg, '-hide_banner', '-nostdin', '-i', str(RUNTIME),
            '-af', 'loudnorm=I=-20:TP=-1.5:LRA=10:print_format=json', '-f', 'null', '-'])
        measured_output = json.JSONDecoder().raw_decode(verification.stderr[verification.stderr.rfind('{'):])[0]
        report = dict(durationSeconds=len(pcm) / rate, sampleRate=rate, channels=pcm.shape[1],
            runtimeBytes=RUNTIME.stat().st_size, encoder=mp3_encoder, peakDbfs=20 * math.log10(np.max(np.abs(normalized))),
            integratedLufs=float(measured_output['input_i']), truePeakDbtp=float(measured_output['input_tp']),
            loopBoundaryStep=float(np.max(np.abs(normalized[-1] - normalized[0]))),
            maxAdjacentSampleStep=float(np.max(np.abs(np.diff(normalized, axis=0)))),
            clippingSamples=int(np.sum(np.abs(pcm.astype(np.int32)) >= 32767)),
            sha256=hashlib.sha256(RUNTIME.read_bytes()).hexdigest(),
            production='Original authored score, deterministic NumPy/SciPy timbres, FFmpeg mastering; no AI music model or third-party recordings.',
            listeningAcceptance='pending user audition', taptapDeviceAcceptance='pending')
        (SOURCE / 'audio-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
