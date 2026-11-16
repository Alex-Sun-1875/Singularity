"""Thunder v4: a dry arc front plus an audible, compact electric shock body.

Original NumPy/SciPy models; no samples, AI calls, downloads or runtime edits.
Importing is side-effect free. The public API returns mono float64 audio and
preserves v3 timings, leaving the orchestration layer to match audition loudness.
Human listening is required to judge impact, naturalness and preference.
"""
from __future__ import annotations

import hashlib

import numpy as np
from scipy import signal


RATE = 44100
CUE_DURATIONS = {'thu_charge': .44, 'thu_crack': .44, 'thu_network': 1.10}
DESCRIPTIONS = {
    'thu_charge': 'Separated small pre-discharge arcs with a short pressure contact; no tonal rise or sustained hum.',
    'thu_crack': 'A dry leading fracture, an audible 20–100ms low-mid electric shock body, and two subordinate short aftercracks.',
    'thu_network': 'A strong first discharge with a compact thunder body, followed by weaker grouped arcs at 0.25 and 0.50 seconds.',
}
DESIGN_NOTES = {
    'direction': 'More explosive and full-bodied than v3, retaining a natural dry electric-arc identity.',
    'provenance': 'Original deterministic NumPy/SciPy synthesis. No recordings, downloaded soundbanks, local AI or cloud generation.',
    'structure': {
        'front': 'One 2–5ms broadband fracture with a small pressure impulse; the leading discharge remains strongest.',
        'body': 'A separate 20–100ms low-mid turbulent shock and rapidly damped non-harmonic structure modes, rather than merely a louder click.',
        'aftercracks': 'Two much quieter local cracks; neither a repeating gunfire train nor a sustained high hiss.',
        'tail': 'Body resolves within roughly 0.16 seconds; no long distant-thunder rumble.',
    },
    'differenceFromV3': 'v3 concentrated most single-hit energy in about 20ms. v4 adds independent short pressure and low-mid body sources so matching loudness still leaves a broader attack/body envelope.',
    'network': 'Existing 0/.25/.50-second groups remain aligned. The later groups are subordinate and have less body than the main arc.',
    'excluded': ['ascending laser whistle', 'sawtooth buzz', 'continuous oscillator carrier', 'long high-frequency spray', 'sub-bass rumble'],
    'timing': 'Original .44/.44/1.10-second file lengths preserved; near-silent padding retains existing cue schedules.',
    'variants': 'Three deterministic variants alter turbulent excitation, short damping and branch microtiming; no large pitch shifts.',
    'mix': 'Peak cap 0.64 preserves headroom; no individual-cue loudness normalization. Root audition assembly matches loudness.',
    'acceptance': 'Envelope and peak measurements are technical evidence only; explosive quality and realism remain pending human audition.',
}


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'thunder-impact-v4:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _time(seconds, rate):
    return np.arange(max(2, round(seconds * rate)), dtype=np.float64) / rate


def _place(destination, source, at, rate, gain=1.):
    begin = round(at * rate)
    skip = max(0, -begin)
    begin = max(0, begin)
    count = min(len(destination) - begin, len(source) - skip)
    if count > 0:
        destination[begin:begin + count] += source[skip:skip + count] * gain


def _band_noise(rng, count, rate, low, high):
    high = min(high, rate * .44)
    low = min(low, high * .75)
    noise = signal.sosfilt(signal.butter(2, [low, high], btype='bandpass', fs=rate,
                                         output='sos'), rng.standard_normal(count))
    return noise / max(.03, float(np.sqrt(np.mean(noise * noise))))


def _packet(rng, rate, seconds, low, high, attack, decay):
    t = _time(seconds, rate)
    texture = _band_noise(rng, len(t), rate, low, high)
    envelope = (1 - np.exp(-t / attack)) * np.exp(-t / decay)
    end = np.clip((seconds - t) / min(.015, seconds * .25), 0, 1)
    return texture * envelope * np.sin(end * np.pi / 2) ** 2


def _dry_fracture(rng, rate, seconds=.047):
    """Broad dry fracture, no carrier or high-frequency tail."""
    audio = np.zeros(round(seconds * rate), np.float64)
    core = _packet(rng, rate, .029, rng.uniform(560, 780), 5900,
                   .00022, rng.uniform(.0031, .0045))
    _place(audio, core, .00035, rate, .46)
    edge = _packet(rng, rate, .012, 1700, 6700, .00014, .0012)
    _place(audio, edge, .00055, rate, .095)
    return audio


def _shock_body(rng, rate, amount=1.):
    """Independent short turbulent pressure body, audible after the first snap."""
    t = _time(.180, rate)
    noise = _band_noise(rng, len(t), rate, rng.uniform(135, 170), rng.uniform(1050, 1350))
    # A finite noisy pressure lobe has mass on phone speakers without sub-bass.
    envelope = (1 - np.exp(-t / .0028)) * np.exp(-t / rng.uniform(.030, .036))
    end = np.sin(np.clip((.180 - t) / .025, 0, 1) * np.pi / 2) ** 2
    audio = noise * envelope * .32
    modes = np.zeros(len(t), np.float64)
    # Non-harmonic and individually damped; no stable note or oscillating hum.
    for frequency, level, decay in ((183, .135, .043), (307, .105, .036),
                                    (493, .070, .027), (773, .034, .019)):
        frequency *= rng.uniform(.965, 1.035)
        phase = rng.uniform(-.11, .11)
        modes += level * np.sin(2 * np.pi * frequency * t + phase) * np.exp(-t / decay)
    modes *= (1 - np.exp(-t / .0018))
    audio += modes
    # The delayed short pressure knot broadens the body without another big boom.
    knot = _packet(rng, rate, .075, 170, 850, .002, .018)
    _place(audio, knot, rng.uniform(.019, .025), rate, .12)
    return audio * end * amount


def _pressure_front(rng, rate):
    t = _time(.024, rate)
    width = rng.uniform(.00095, .00125)
    q = (t - .0034) / width
    pulse = -q * np.exp(-.5 * q * q)
    pulse *= np.clip((.024 - t) / .006, 0, 1)
    return pulse


def _discharge(rng, rate, body_amount=1.):
    audio = np.zeros(round(.200 * rate), np.float64)
    _place(audio, _dry_fracture(rng, rate), .0003, rate)
    _place(audio, _pressure_front(rng, rate), .0015, rate, .17)
    _place(audio, _shock_body(rng, rate, body_amount), .003, rate)
    return audio


def _charge(rng, rate, n):
    audio = np.zeros(n, np.float64)
    for index, at in enumerate((.027, .117, .207, .286, .350)):
        # Keep separated contacts. Slightly denser final contacts imply charge
        # without introducing a rising tonal oscillator.
        at += rng.uniform(-.004, .004)
        _place(audio, _dry_fracture(rng, rate), at, rate, .075 + index * .014)
    small_body = _packet(rng, rate, .061, 240, 1450, .0013, .013)
    _place(audio, small_body, .351, rate, .040)
    return audio


def _crack(rng, rate, n, network=False):
    audio = np.zeros(n, np.float64)
    _place(audio, _discharge(rng, rate), .001, rate)
    # Subordinate local fractures continue the shock, without flooding the tail.
    for at, level in ((.043, .14), (.091, .055)):
        _place(audio, _dry_fracture(rng, rate), at + rng.uniform(-.0025, .0025), rate, level)
    if network:
        _place(audio, _discharge(rng, rate, .70), .25 + rng.uniform(-.002, .002), rate, .42)
        _place(audio, _discharge(rng, rate, .48), .50 + rng.uniform(-.002, .002), rate, .25)
        _place(audio, _dry_fracture(rng, rate), .543 + rng.uniform(-.002, .002), rate, .025)
    return audio


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Generate one deterministic mono float64 cue; finite, endpoints zero, peak<=.64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown thunder cue: {name}')
    if not isinstance(variation, (int, np.integer)) or variation < 1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate < 22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    rng = _rng(name, variation)
    n = round(CUE_DURATIONS[name] * sample_rate)
    audio = _charge(rng, sample_rate, n) if name == 'thu_charge' else _crack(rng, sample_rate, n, name == 'thu_network')
    audio = signal.sosfilt(signal.butter(2, 105, btype='highpass', fs=sample_rate, output='sos'), audio)
    if not np.all(np.isfinite(audio)):
        raise FloatingPointError('Generated a non-finite sample')
    fade_in = max(2, round(.0008 * sample_rate))
    fade_out = max(2, round(.012 * sample_rate))
    audio[:fade_in] *= np.linspace(0, 1, fade_in)
    audio[-fade_out:] *= np.linspace(1, 0, fade_out)
    peak = float(np.max(np.abs(audio)))
    audio *= min(1., .64 / max(peak, 1e-12))
    return np.asarray(audio, dtype=np.float64)
