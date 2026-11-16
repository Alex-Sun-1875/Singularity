"""Heavier elemental impacts with separately balanced body and material release.

Pure import-safe NumPy/SciPy synthesis. No files, playback, recordings, downloads
or AI calls. Keeps v5 cue lengths and audible fire/electrical release structure.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import runpy

import numpy as np
from scipy import signal


RATE = 44100
CUE_DURATIONS = {
    'fir_charge': .72, 'fir_burst': 1.05, 'fir_wall': 3.00,
    'thu_charge': .60, 'thu_crack': .80, 'thu_network': 1.45,
}
DESCRIPTIONS = {
    'fir_charge': 'Darker gathering combustion with modest damped pressure, without bright spark ticks.',
    'fir_burst': 'A weightier low-mid ignition and finite pressure volume, thick rolling combustion and subdued embers.',
    'fir_wall': 'Intermittent darker flame tongues with modest low-mid pressure and a fading natural release.',
    'thu_charge': 'Dark rough pre-discharge contacts and low-presence electrical sizzle; no laser or bright ticking.',
    'thu_crack': 'A rounded electrical fracture, a heavier 140–600Hz short shock body and dark sustained electrical sizzle.',
    'thu_network': 'A heavy first electrical shock with subordinate grouped impacts and successively weaker dark arc release.',
}
DESIGN_NOTES = {
    'userPreference': 'Less crisp and bright; more weight across professions while retaining accepted burst and longer material release.',
    'provenance': 'Original deterministic procedural models using existing NumPy/SciPy and previous project source code. No downloads, recorded samples or AI calls.',
    'sourceChanges': {
        'core': 'Accepted source is separated into low-mid pressure, middle texture and high edge. Bright edge is strongly reduced while the low-mid component is retained.',
        'newWeight': 'New finite noise excitation drives a non-harmonic bank around 149/211/303/437/591Hz with individually short damping; an independent turbulent pressure packet adds dense mass.',
        'fire': 'Additional low-mid rolling packets and reduced spark/ember edge produce thicker combustion. Finite breaths remain distinct from a constant noise wall.',
        'thunder': 'A newly authored short shock body supports the main contact and subordinate network groups; no descending sine kick, sub-bass dependency or long rumble.',
        'release': 'v5 fire/electric release is handled separately from impact weight. Electrical sizzle remains dense and sustained, with less high-frequency edge and a darker middle band.',
    },
    'spectralIntent': 'Weight is concentrated in the phone-audible 140–600Hz range; energy below 60Hz is rejected. This is a source-layer rebalance and added pressure model, not just one low-pass across the final sound.',
    'durations': CUE_DURATIONS.copy(),
    'mix': 'Peak cap .64, with no cue-by-cue loudness normalization. Audition comparison should match playback loudness.',
    'acceptance': 'Frequency and envelope measurements verify source changes; perceived heaviness and naturalness require user listening.',
}


@lru_cache(maxsize=1)
def _previous():
    path = Path(__file__).resolve().parents[1] / 'audio-impact-v5' / 'elemental_cues.py'
    return runpy.run_path(str(path))


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'elemental-weight-v6:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _place(destination, source, at, rate, gain=1.):
    begin = round(at * rate)
    skip = max(0, -begin)
    begin = max(0, begin)
    count = min(len(destination) - begin, len(source) - skip)
    if count > 0:
        destination[begin:begin + count] += source[skip:skip + count] * gain


def _band(audio, rate, low, high):
    return signal.sosfilt(signal.butter(2, [low, min(high, rate * .44)],
                                       btype='bandpass', fs=rate, output='sos'), audio)


def _rms_window(audio, rate, start, end, target):
    part = audio[round(start * rate):min(len(audio), round(end * rate))]
    return audio * target / max(1e-9, float(np.sqrt(np.mean(part * part))))


def _noise(rng, n, rate, low, high):
    out = _band(rng.standard_normal(n), rate, low, high)
    return out / max(1e-9, float(np.sqrt(np.mean(out * out))))


def _weighted_core(core, rate, fire):
    low_mid = _band(core, rate, 110 if fire else 125, 730)
    texture = _band(core, rate, 650, 2350)
    edge = _band(core, rate, 2200, 6500)
    return .92 * low_mid + (.42 if fire else .45) * texture + .100 * edge


def _weight_body(rng, rate, fire=True):
    """Finite noise-excited pressure volume; no swept sine drum oscillator."""
    seconds = .225 if fire else .185
    t = np.arange(round(seconds * rate), dtype=np.float64) / rate
    count = round((.0052 if fire else .0038) * rate)
    excitation = np.zeros(len(t), np.float64)
    excitation[:count] = rng.standard_normal(count) * np.sin(np.linspace(0, np.pi, count))
    modes = np.zeros(len(t), np.float64)
    for freq, level, decay in ((149, .58, .050), (211, 1., .049),
                                (303, .82, .043), (437, .55, .032), (591, .27, .023)):
        frequency = freq * rng.uniform(.96, 1.04)
        damping = decay * rng.uniform(.89, 1.11) * (1.10 if fire else 1.)
        radius = np.exp(-1 / (rate * damping))
        mode = signal.lfilter([1.], [1., -2 * radius * np.cos(2 * np.pi * frequency / rate), radius * radius], excitation)
        mode = _rms_window(mode, rate, .008, .070, 1.)
        modes += mode * level
    modes = _rms_window(modes, rate, .008, .085, .085 if fire else .100)
    turbulent = _noise(rng, len(t), rate, 135, 720)
    turbulent *= -np.expm1(-t / .0035) * np.exp(-t / (.043 if fire else .037))
    turbulent = _rms_window(turbulent, rate, .006, .065, .045 if fire else .052)
    out = modes + turbulent
    out *= np.sin(np.clip(t / .0025, 0, 1) * np.pi / 2) ** 2
    out *= np.sin(np.clip((seconds - t) / .035, 0, 1) * np.pi / 2) ** 2
    return out


def _rolling_pressure(rng, rate, seconds, target=.025):
    t = np.arange(round(seconds * rate), dtype=np.float64) / rate
    packet = _noise(rng, len(t), rate, rng.uniform(180, 250), rng.uniform(700, 1100))
    packet *= -np.expm1(-t / .014) * np.exp(-t / .055)
    packet *= np.sin(np.clip((seconds - t) / .035, 0, 1) * np.pi / 2) ** 2
    return _rms_window(packet, rate, .012, .085, target)


def _dark_release(release, rate, fire):
    if fire:
        return .96 * _band(release, rate, 160, 1350) + .23 * _band(release, rate, 1200, 3400)
    # Keep the v5 micro-discharge stream; reduce only its bright edge rather
    # than deleting the sustain or replacing it with a handful of isolated clicks.
    return 1.32 * _band(release, rate, 480, 2150) + .22 * _band(release, rate, 1900, 4300)


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Return one finite mono float64 impact with endpoints zero and peak<=.64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown elemental cue: {name}')
    if not isinstance(variation, (int, np.integer)) or variation < 1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate < 22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    previous = _previous()
    family = name[:3]
    fire = family == 'fir'
    n = round(CUE_DURATIONS[name] * sample_rate)
    old_core = previous['_v4'](family)['synth_cue'](name, variation, sample_rate)
    core = np.zeros(n, np.float64)
    _place(core, old_core, 0., sample_rate)
    # Isolate the accepted longer release so transient and sustain are voiced
    # independently; source changes to the body do not erase the electrical tail.
    old_complete = previous['synth_cue'](name, variation, sample_rate)
    release = old_complete - core
    out = _weighted_core(core, sample_rate, fire)
    out += _dark_release(release, sample_rate, fire)
    rng = _rng(name, variation)
    if name == 'fir_burst':
        _place(out, _weight_body(rng, sample_rate, True), .004, sample_rate)
        for at, rms in ((.055, .040), (.143, .030), (.247, .022), (.382, .013)):
            _place(out, _rolling_pressure(rng, sample_rate, .21, rms), at + rng.uniform(-.005, .005), sample_rate)
    elif name == 'fir_charge':
        _place(out, _weight_body(rng, sample_rate, True), .423, sample_rate, .13)
    elif name == 'fir_wall':
        _place(out, _weight_body(rng, sample_rate, True), .035, sample_rate, .13)
        for at in (.55, 1.23, 1.93, 2.54):
            _place(out, _rolling_pressure(rng, sample_rate, .19, .009), at + rng.uniform(-.025, .025), sample_rate)
    elif name == 'thu_charge':
        _place(out, _weight_body(rng, sample_rate, False), .350, sample_rate, .075)
    else:
        _place(out, _weight_body(rng, sample_rate, False), .0035, sample_rate)
        if name == 'thu_network':
            _place(out, _weight_body(rng, sample_rate, False), .253, sample_rate, .39)
            _place(out, _weight_body(rng, sample_rate, False), .503, sample_rate, .22)
    # Remove infrasonic buildup only. Body/edge balance is already established
    # independently above; this is not a final whole-sound low-pass treatment.
    out = signal.sosfilt(signal.butter(2, 85, btype='highpass', fs=sample_rate, output='sos'), out)
    if not np.all(np.isfinite(out)):
        raise FloatingPointError('Non-finite elemental weight synthesis')
    fade_in = max(2, round(.0011 * sample_rate))
    fade_out = max(2, round(.018 * sample_rate))
    out[:fade_in] *= np.linspace(0, 1, fade_in)
    out[-fade_out:] *= np.linspace(1, 0, fade_out)
    out *= min(1., .64 / max(1e-12, float(np.max(np.abs(out)))))
    return np.asarray(out, dtype=np.float64)
