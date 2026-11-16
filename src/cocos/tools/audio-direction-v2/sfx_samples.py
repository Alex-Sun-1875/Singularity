"""Original procedural sound-direction studies; no recordings or runtime edits.

Import-safe public API:
    synth_cue('war_slash', variation=1, sample_rate=44100) -> mono float64 array
    build_demo('WAR', sample_rate=44100) -> (stereo array, exact WAV cue list)

The four 15-second demos share sections: basic 0-4s, signature 4-8s,
critical 8-11s, kill 11-15s. Critical and kill retain the profession's timbre.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

import numpy as np
from scipy import signal

RATE = 44100
ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'source-art/audio/direction-studies-v2/sfx'
DURATION = 15.0
FAMILIES = ('WAR', 'BOW', 'FIR', 'THU')
CUE_DURATIONS = {
    'war_swing': .29, 'war_slash': .34, 'war_armor': .48, 'war_finish': .65,
    'bow_draw': .69, 'bow_release': .41, 'bow_pierce': .30, 'bow_heavy': .61,
    'fir_charge': .64, 'fir_burst': .82, 'fir_wall': 2.6,
    'thu_charge': .44, 'thu_crack': .44, 'thu_network': 1.10,
}
DESCRIPTIONS = {
    'war_swing': 'Short steel blade displacement; broad air with a thin steel edge.',
    'war_slash': 'Compact cutting contact, dry crack and a restrained body.',
    'war_armor': 'Inharmonic steel plate contact; damping prevents a long bell.',
    'war_finish': 'A weightier cut with a short descending steel/body tail.',
    'bow_draw': 'Modelled wood strain, string tension, and small hand friction.',
    'bow_release': 'Plucked string and resonant wood, followed by narrow air.',
    'bow_pierce': 'Dry puncture with shaft vibration; distinct from a sword cut.',
    'bow_heavy': 'Heavy arrow contact, wood flex and a compact head resonance.',
    'fir_charge': 'Swelling combustion and compressed ignition pressure.',
    'fir_burst': 'Rounded low-mid combustion burst with coarse ember texture.',
    'fir_wall': 'Low-presence sustained flame with sparse, small embers.',
    'thu_charge': 'Brief rising charge, with bounded high-frequency energy.',
    'thu_crack': 'Dry electric fracture, rapid branches and a short low rumble.',
    'thu_network': 'A single authored network discharge with sparse branch ticks.',
}


def _rng(name: str, variation: int) -> np.random.Generator:
    seed = int.from_bytes(hashlib.sha256(f'direction-v2:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _band(rng, n, rate, low=0., high=8000.):
    x = rng.standard_normal(n)
    high = min(high, rate * .46)
    if low > 0:
        sos = signal.butter(2, [low, high], 'bandpass', fs=rate, output='sos')
    else:
        sos = signal.butter(2, high, 'lowpass', fs=rate, output='sos')
    x = signal.sosfilt(sos, x)
    return x / max(.1, float(np.sqrt(np.mean(x*x))))


def _envelope(t, attack=.002, decay=.12):
    return (1-np.exp(-t/max(.0001, attack))) * np.exp(-t/max(.005, decay))


def _tap(destination, source, seconds, rate, gain=1.):
    start = int(round(seconds*rate))
    source_start = max(0, -start)
    start = max(0, start)
    count = min(len(destination)-start, len(source)-source_start)
    if count > 0:
        destination[start:start+count] += source[source_start:source_start+count]*gain


def _ring(t, frequencies, decay, rng):
    out = np.zeros_like(t)
    for i, freq in enumerate(frequencies):
        out += np.sin(2*np.pi*freq*t+rng.uniform(-.15, .15)) * np.exp(-t/(decay/(1+i*.4))) / (1+i*.6)
    return out * (1-np.exp(-t/.0008))


def _string(rng, n, rate, fundamental):
    """Filtered noise comb models string/wood resonance, not a real recording."""
    delay = max(8, int(round(rate/fundamental)))
    excitation = np.zeros(n)
    pulse = rng.uniform(-1, 1, delay)
    excitation[:min(delay, n)] = pulse[:min(delay, n)]
    denominator = np.zeros(delay+2)
    denominator[0] = 1
    denominator[delay] = -.491
    denominator[delay+1] = -.491
    return signal.lfilter([1.], denominator, excitation)


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Generate one unique deterministic mono cue, peak <= 0.60, no writes."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown cue: {name}')
    if variation < 1 or sample_rate < 22050:
        raise ValueError('variation >= 1 and sample_rate >= 22050 are required')
    rng = _rng(name, variation)
    t = np.arange(round(CUE_DURATIONS[name]*sample_rate))/sample_rate
    n = len(t)
    pitch = rng.uniform(.94, 1.06)
    # Independent texture, partials, and microtiming for each variation.
    if name == 'war_swing':
        air = _band(rng, n, sample_rate, 320, 4800)
        centre = rng.uniform(.085, .105)
        env = np.exp(-.5*((t-centre)/.044)**2)
        edge = np.sin(2*np.pi*(1450*pitch*t-1000*t*t))*.075
        x = (air*.44+edge)*env
    elif name in ('war_slash', 'war_finish'):
        heavy = name == 'war_finish'
        body = np.sin(2*np.pi*(155*pitch*t-68*t*t))*_envelope(t, .001, .075 if not heavy else .14)
        cut = _band(rng, n, sample_rate, 720, 6500)*_envelope(t, .0005, .020)
        steel = _ring(t, np.array([780, 1370, 2110])*pitch, .060 if not heavy else .13, rng)
        x = .36*body+.33*cut+.13*steel
        if heavy:
            x += .20*np.sin(2*np.pi*(92*pitch*t-20*t*t))*_envelope(t, .002, .17)
            _tap(x, _band(rng, n, sample_rate, 400, 2000)*_envelope(t, .001, .05), .032, sample_rate, .10)
    elif name == 'war_armor':
        x = .28*_ring(t, np.array([930, 1597, 2471, 3719])*pitch, .11, rng)
        x += .25*_band(rng, n, sample_rate, 1300, 7500)*_envelope(t, .0006, .016)
        x += .08*np.sin(2*np.pi*220*pitch*t)*_envelope(t, .002, .055)
    elif name == 'bow_draw':
        friction = _band(rng, n, sample_rate, 350, 2300)
        rise = np.sin(np.pi*np.minimum(t/.69, 1))**1.1
        strain = np.sin(2*np.pi*(92*pitch*t+43*t*t))+.25*np.sin(2*np.pi*183*pitch*t)
        x = (.15*friction+.13*strain)*rise
        for at in (.12, .31, .51):
            _tap(x, _ring(t, [220*pitch, 510*pitch], .018, rng), at+rng.uniform(-.015, .015), sample_rate, .045)
    elif name == 'bow_release':
        string = _string(rng, n, sample_rate, 186*pitch)
        wood = _ring(t, np.array([305, 589, 1012])*pitch, .064, rng)
        snap = _band(rng, n, sample_rate, 1800, 7000)*_envelope(t, .0005, .010)
        air = _band(rng, n, sample_rate, 1700, 4700)*np.exp(-.5*((t-.085)/.038)**2)
        x = .49*string+.20*wood+.10*snap+.14*air
    elif name in ('bow_pierce', 'bow_heavy'):
        heavy = name == 'bow_heavy'
        shaft = _ring(t, np.array([285, 547, 1280])*pitch, .07 if not heavy else .12, rng)
        puncture = _band(rng, n, sample_rate, 1500, 8000)*_envelope(t, .0003, .009)
        body = np.sin(2*np.pi*185*pitch*t)*_envelope(t, .001, .037)
        x = .19*shaft+.32*puncture+.20*body
        if heavy:
            x += .20*_ring(t, [118*pitch, 376*pitch], .09, rng)
            _tap(x, .07*_band(rng, n, sample_rate, 450, 1900)*_envelope(t, .001, .024), .026, sample_rate)
    elif name == 'fir_charge':
        flame = _band(rng, n, sample_rate, 90, 1400)
        ripple = .58+.24*np.sin(2*np.pi*19*t)+.18*np.sin(2*np.pi*31*t)
        swell = np.sin(np.pi*np.minimum(t/.64, 1))**.75
        pressure = np.sin(2*np.pi*(105*pitch*t+55*t*t))
        x = (.38*flame*ripple+.15*pressure)*swell
    elif name in ('fir_burst', 'fir_wall'):
        wall = name == 'fir_wall'
        texture = _band(rng, n, sample_rate, 80, 1850)
        flutter = .65+.20*np.sin(2*np.pi*23*t)+.15*np.sin(2*np.pi*37*t+.4)
        if wall:
            env = np.minimum(1, t/.15)*np.minimum(1, (t[-1]-t)/.4)
            x = .16*texture*flutter*env
            count = 11
        else:
            env = _envelope(t, .008, .21)
            body = np.sin(2*np.pi*(115*pitch*t-36*t*t))*_envelope(t, .002, .13)
            x = .45*texture*flutter*env+.28*body
            count = 7
        for at in sorted(rng.uniform(.035, t[-1]*.82, count)):
            ember = _band(rng, n, sample_rate, 1000, 4800)*_envelope(t, .0008, rng.uniform(.006, .016))
            _tap(x, ember, at, sample_rate, (.022 if wall else .055)*math.exp(-at/(3 if wall else .26)))
    elif name == 'thu_charge':
        frequencies = 360*pitch+1750*(t/t[-1])**1.8
        phase = 2*np.pi*np.cumsum(frequencies)/sample_rate
        core = np.sin(phase)+.16*np.sin(phase*2.31)
        pulse = .65+.35*signal.sawtooth(2*np.pi*(32*t+34*t*t), width=.25)
        env = np.maximum(0., np.sin(np.pi*t/t[-1]))**1.2
        x = (.19*core*pulse+.10*_band(rng, n, sample_rate, 1200, 4200))*env
    elif name in ('thu_crack', 'thu_network'):
        network = name == 'thu_network'
        # Short fractures rather than a continuous high-frequency oscillator.
        x = np.zeros(n)
        crack = _band(rng, n, sample_rate, 650, 6200)*_envelope(t, .0003, .018)
        x += .45*crack
        for at in ([.027, .068, .116, .241, .496, .748] if network else [.024, .058, .093]):
            at += rng.uniform(-.003, .003)
            tick = _band(rng, n, sample_rate, rng.uniform(950, 1800), 6600)*_envelope(t, .0004, rng.uniform(.005, .012))
            _tap(x, tick, at, sample_rate, .10 if network else .065)
        rumble = _band(rng, n, sample_rate, 110, 440)
        _tap(x, rumble*_envelope(t, .008, .12 if not network else .21), .026, sample_rate, .10)
        if network:
            # Three group pulses follow the existing 0.25s thunder segment beat.
            for at in (.25, .50):
                _tap(x, .23*crack, at, sample_rate)
    else:
        raise AssertionError(name)
    x = signal.sosfilt(signal.butter(2, 45, 'highpass', fs=sample_rate, output='sos'), x)
    x -= np.mean(x)
    fade = max(2, int(.003*sample_rate))
    x[:fade] *= np.linspace(0, 1, fade)
    x[-fade:] *= np.linspace(1, 0, fade)
    peak = float(np.max(np.abs(x)))
    # A headroom cap, not loudness normalisation: preserve natural cue dynamics.
    x *= min(1., .60/max(peak, 1e-12))
    return x.astype(np.float64)


def build_demo(family: str, sample_rate: int = RATE):
    """Return exact 15s stereo audio and sample-accurate cue records, no writes."""
    family = family.upper()
    if family not in FAMILIES:
        raise ValueError(f'Unknown profession {family}')
    output = np.zeros((round(DURATION*sample_rate), 2))
    cues = []

    def add(name, at, variation=1, gain=.8, section='basic', pan=0., note=''):
        mono = synth_cue(name, variation, sample_rate)
        angle = (max(-1, min(1, pan))+1)*np.pi/4
        stereo = mono[:, None]*np.array([np.cos(angle), np.sin(angle)])[None, :]
        _tap(output, stereo, at, sample_rate, gain)
        cues.append(dict(cue=name, variation=variation, section=section, startSeconds=at,
                         startSample=round(at*sample_rate), durationSeconds=len(mono)/sample_rate,
                         gain=gain, pan=pan, note=note))

    if family == 'WAR':
        # First two cuts release at 0.12s, third at 0.22s; chain 0.38/0.38/0.56.
        for at, delay, variation in ((.35, .12, 1), (.73, .12, 2), (1.11, .22, 3)):
            add('war_swing', at, variation)
            add('war_finish' if variation == 3 else 'war_slash', at+delay, variation, .90)
        add('war_swing', 2.4, 2)
        add('war_armor', 2.52, 1, .78, note='Armoured target; material changes, sword identity remains.')
        for i, at in enumerate((4.55, 4.73, 4.91)):
            add('war_swing', at, i+1, .78, 'signature', note='Three performed cuts, 0.18s spacing.')
            add('war_finish' if i == 2 else 'war_slash', at+.10, i+1, 1. if i == 2 else .74, 'signature')
        add('war_swing', 8.45, 3, .85, 'critical')
        add('war_slash', 8.67, 3, 1., 'critical')
        add('war_armor', 8.679, 3, .22, 'critical', note='Very short steel emphasis; original slash retained.')
        add('war_swing', 11.45, 3, .9, 'kill')
        add('war_finish', 11.67, 1, 1.1, 'kill')
    elif family == 'BOW':
        for i, at in enumerate((.25, 1.65, 2.9)):
            add('bow_draw', at, i+1, .50)
            add('bow_release', at+.45, i+1, .9)
            add('bow_pierce', at+.69, i+1, .9)
        add('bow_draw', 4.25, 2, .60, 'signature')
        add('bow_release', 4.90, 2, 1., 'signature')
        add('bow_heavy', 5.20, 2, 1., 'signature', note='One arrow, three restrained puncture contacts.')
        add('bow_pierce', 5.33, 1, .42, 'signature', -.12)
        add('bow_pierce', 5.46, 3, .30, 'signature', .12)
        add('bow_draw', 8.15, 3, .55, 'critical')
        add('bow_release', 8.80, 3, .95, 'critical')
        add('bow_heavy', 9.06, 3, 1.12, 'critical')
        add('bow_draw', 11.15, 1, .60, 'kill')
        add('bow_release', 11.80, 1, 1., 'kill')
        add('bow_heavy', 12.12, 1, 1.15, 'kill')
        add('bow_pierce', 12.148, 2, .26, 'kill', note='Short puncture accent; no generic victory chime.')
    elif family == 'FIR':
        for i, at in enumerate((.25, 1.40, 2.55)):
            add('fir_charge', at, i+1, .40)
            add('fir_burst', at+.48, i+1, .74)
        add('fir_charge', 4.2, 2, .60, 'signature')
        add('fir_wall', 4.75, 1, .42, 'signature', note='Wall bed at restrained gain, no per-damage-tick explosion.')
        add('fir_burst', 5.00, 2, .90, 'signature')
        add('fir_burst', 5.30, 3, .27, 'signature', .12, 'Secondary ignition, existing 0.30s fire beat.')
        add('fir_charge', 8.20, 3, .52, 'critical')
        add('fir_burst', 8.80, 3, 1.08, 'critical', note='Larger combustion transient retains fire texture.')
        add('fir_charge', 11.20, 1, .65, 'kill')
        add('fir_burst', 11.82, 1, 1.10, 'kill')
        add('fir_wall', 12.00, 2, .17, 'kill', note='Short lingering ember bed.')
    else:
        for i, at in enumerate((.25, 1.55, 2.85)):
            add('thu_charge', at, i+1, .45)
            add('thu_crack', at+.34, i+1, .80)
        add('thu_charge', 4.20, 2, .60, 'signature')
        add('thu_network', 4.60, 2, .95, 'signature', note='One network cue, grouped pulses at 0/.25/.50s, not one sound per edge.')
        add('thu_charge', 8.20, 3, .55, 'critical')
        add('thu_crack', 8.60, 3, 1.10, 'critical')
        add('thu_crack', 8.625, 1, .16, 'critical', .10, 'Subordinate branch, main crack remains identifiable.')
        add('thu_charge', 11.20, 1, .65, 'kill')
        add('thu_network', 11.62, 1, 1.10, 'kill')
    cues.sort(key=lambda cue: cue['startSample'])
    peak = float(np.max(np.abs(output)))
    output *= min(1., .68/max(peak, 1e-12))
    return output, cues


def build_battle_layer(sample_rate: int = RATE):
    """Four spaced attacks for a music overlay; 15s with silence after 12.2s."""
    output = np.zeros((round(15*sample_rate), 2))
    events = [
        ('WAR', 'war_swing', .80, 1, .78, 'windup-release'),
        ('WAR', 'war_slash', .92, 1, .90, 'contact'),
        ('BOW', 'bow_draw', 4.00, 2, .50, 'windup'),
        ('BOW', 'bow_release', 4.45, 2, .90, 'release'),
        ('BOW', 'bow_pierce', 4.69, 2, .95, 'contact'),
        ('FIR', 'fir_charge', 7.30, 3, .50, 'windup'),
        ('FIR', 'fir_burst', 7.76, 2, .23, 'release'),
        ('FIR', 'fir_burst', 8.02, 3, .90, 'contact'),
        ('THU', 'thu_charge', 10.60, 1, .55, 'windup'),
        ('THU', 'thu_crack', 10.98, 2, .30, 'release'),
        ('THU', 'thu_network', 11.08, 1, .95, 'contact'),
    ]
    cues = []
    for family, name, at, variation, gain, phase in events:
        mono = synth_cue(name, variation, sample_rate)
        _tap(output, np.repeat(mono[:, None]/math.sqrt(2), 2, axis=1), at, sample_rate, gain)
        cues.append(dict(profession=family,cue=name,variation=variation,phase=phase,
                         startSeconds=at,startSample=round(at*sample_rate),gain=gain,
                         durationSeconds=len(mono)/sample_rate,pan=0))
    normalisation = min(1., .68/max(float(np.max(np.abs(output))), 1e-12))
    output *= normalisation
    return output, cues, normalisation


def _write_wav(path: Path, samples, rate=RATE):
    """24-bit PCM; all generated files stay in this study's output folder."""
    if not np.all(np.isfinite(samples)) or float(np.max(np.abs(samples))) >= 1:
        raise ValueError('WAV samples must be finite and below digital full scale')
    path.parent.mkdir(parents=True, exist_ok=True)
    integer = np.rint(np.asarray(samples)*8388607).astype(np.int32).reshape(-1)
    data = np.empty((len(integer), 3), np.uint8)
    data[:, 0] = integer & 255
    data[:, 1] = (integer >> 8) & 255
    data[:, 2] = (integer >> 16) & 255
    with wave.open(str(path), 'wb') as file:
        file.setnchannels(1 if samples.ndim == 1 else samples.shape[1])
        file.setsampwidth(3)
        file.setframerate(rate)
        file.writeframes(data.tobytes())


def audio_metrics(samples, rate=RATE):
    samples = np.asarray(samples)
    peak = float(np.max(np.abs(samples)))
    true_peak = float(np.max(np.abs(signal.resample_poly(samples, 4, 1, axis=0))))
    mono = samples if samples.ndim == 1 else np.mean(samples, axis=1)
    frequency, psd = signal.welch(mono, fs=rate, nperseg=min(2048, len(mono)))
    return dict(durationSeconds=len(samples)/rate, sampleRate=rate,
                channels=1 if samples.ndim == 1 else samples.shape[1],
                peakDbfs=round(20*math.log10(max(peak, 1e-12)), 3),
                oversampledPeakDbfs=round(20*math.log10(max(true_peak, 1e-12)), 3),
                rmsDbfs=round(20*math.log10(max(float(np.sqrt(np.mean(samples*samples))), 1e-12)), 3),
                clippingSamples=int(np.count_nonzero(np.abs(samples) >= 1)),
                spectralCentroidHz=round(float(np.sum(frequency*psd)/max(1e-18, np.sum(psd))), 1),
                finite=bool(np.all(np.isfinite(samples))))


def _run(args):
    return subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('Pass the path of an already-installed FFmpeg with --ffmpeg; nothing is downloaded.')
    encoders = _run([args.ffmpeg, '-hide_banner', '-encoders']).stdout.decode('utf-8', errors='replace')
    encoder = 'libmp3lame' if 'libmp3lame' in encoders else 'mp3_mf'
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = dict(version=2, production='Original deterministic NumPy/SciPy synthesis and physical/foley-style modelling; no real recordings, cloud audio model, or third-party samples.',
                    listeningAcceptance='Pending user audition; numerical verification is not artistic acceptance.',
                    runtimeIntegration='Study only; no game resources, runtime code, or existing audio changed. The project changelog separately records the study deliverables.',
                    deviceAcceptance='Pending TapTap and target-device audition; no platform claim.',
                    sampleRate=RATE, bitDepth=24, mp3Encoder=encoder,
                    sections=[dict(name='basic',startSeconds=0,endSeconds=4),dict(name='signature',startSeconds=4,endSeconds=8),dict(name='critical',startSeconds=8,endSeconds=11),dict(name='kill',startSeconds=11,endSeconds=15)],
                    timingSources=['features/combat/common/MeleeCombo.ts: sword releases .12/.12/.22s', 'features/combat/common/CombatActionTiming.ts: sword ultimate .18s, fire secondary .30s, thunder groups .25s'],
                    assets=[], demos=[])
    hashes = set()
    variation_groups = {}
    for name in CUE_DURATIONS:
        group = []
        for variation in range(1, 4):
            samples = synth_cue(name, variation)
            path = OUT/'clips'/f'{name}_v{variation:02d}.wav'
            _write_wav(path, samples)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest not in hashes, f'Duplicate audio: {path}'
            hashes.add(digest)
            metrics = audio_metrics(samples)
            assert metrics['finite'] and metrics['clippingSamples'] == 0 and metrics['oversampledPeakDbfs'] < -.5
            manifest['assets'].append(dict(cue=name, variation=variation, path=path.relative_to(OUT).as_posix(), description=DESCRIPTIONS[name], sha256=digest, **metrics))
            group.append(samples)
        correlations = []
        for a,b in ((0,1),(0,2),(1,2)):
            count = min(len(group[a]), len(group[b]))
            correlations.append(round(float(np.corrcoef(group[a][:count], group[b][:count])[0,1]), 5))
        variation_groups[name] = dict(uniqueHashes=3, pairwiseWaveformCorrelations=correlations)
    for family in FAMILIES:
        samples, cues = build_demo(family)
        master = OUT/f'{family.lower()}-15s.wav'
        encoded = OUT/f'{family.lower()}-15s.mp3'
        _write_wav(master, samples)
        encoder_output = OUT/f'{family.lower()}-15s.encoder.mp3'
        _run([args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(master), '-c:a', encoder, '-b:a', '160k', '-ar', str(RATE), str(encoder_output)])
        # Media Foundation can packetise several MP3 frames together; remux so
        # the Xing frame count/duration are correct in ordinary audio players.
        _run([args.ffmpeg, '-hide_banner', '-nostdin', '-y', '-i', str(encoder_output), '-c:a', 'copy', str(encoded)])
        encoder_output.unlink()
        decoded = _run([args.ffmpeg, '-hide_banner', '-nostdin', '-i', str(encoded), '-f', 'f32le', '-acodec', 'pcm_f32le', '-ac', '2', '-ar', str(RATE), '-']).stdout
        decoded_samples = np.frombuffer(decoded, dtype='<f4').reshape(-1, 2)
        master_metrics, decoded_metrics = audio_metrics(samples), audio_metrics(decoded_samples)
        assert master_metrics['durationSeconds'] == 15 and decoded_metrics['clippingSamples'] == 0
        assert abs(decoded_metrics['durationSeconds']-15) < .10
        assert decoded_metrics['oversampledPeakDbfs'] < 0
        cue_path = OUT/f'{family.lower()}-15s.cues.json'
        cue_path.write_text(json.dumps(dict(profession=family,reference='Uncompressed WAV timeline; MP3 encoder padding is measured separately.',durationSeconds=15,cues=cues), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        manifest['demos'].append(dict(profession=family,master=master.name,preview=encoded.name,cues=cue_path.name,masterMetrics=master_metrics,decodedMp3Metrics=decoded_metrics,mp3Bytes=encoded.stat().st_size,masterSha256=hashlib.sha256(master.read_bytes()).hexdigest(),mp3Sha256=hashlib.sha256(encoded.read_bytes()).hexdigest()))
    battle, battle_cues, normalisation = build_battle_layer()
    battle_path = OUT/'battle-layer-15s.wav'
    _write_wav(battle_path, battle)
    battle_metrics = audio_metrics(battle)
    assert battle_metrics['durationSeconds'] == 15 and battle_metrics['clippingSamples'] == 0
    assert np.max(np.abs(battle[round(13.5*RATE):])) == 0
    manifest['battleLayer'] = dict(path=battle_path.name,placementIn45sMusicSeconds=15,
                                  globalNormalisationGain=normalisation,
                                  events=battle_cues,metrics=battle_metrics,
                                  quietBySeconds=12.18,
                                  sha256=hashlib.sha256(battle_path.read_bytes()).hexdigest())
    manifest['validation'] = dict(uniqueClipCount=len(hashes),expectedClipCount=42,allClipHashesUnique=len(hashes)==42,variationGroups=variation_groups,allClippingSamplesZero=True,allDemosExactly15Seconds=True,mp3DecodedAndOversampled=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(output=str(OUT),clips=len(hashes),demos=4,encoder=encoder,validation='passed'), ensure_ascii=False))


if __name__ == '__main__':
    main()
