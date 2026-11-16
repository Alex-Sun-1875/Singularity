"""Restrained fire and electric-arc studies: original procedural sound models.

Public API is import-safe and never writes, downloads or plays audio:
    synth_cue(name, variation=1, sample_rate=44100) -> mono float64 ndarray

Designed for the existing v2 cue schedule. These are synthetic models, not field
recordings; musical/aesthetic acceptance still requires human listening.
"""
from __future__ import annotations

import hashlib

import numpy as np
from scipy import signal


RATE = 44100
CUE_DURATIONS = {
    'fir_charge': .64,
    'fir_burst': .82,
    'fir_wall': 2.60,
    'thu_charge': .44,
    'thu_crack': .44,
    'thu_network': 1.10,
}

DESCRIPTIONS = {
    'fir_charge': 'Small ignition followed by irregular, growing flame breaths; no pitched charge tone.',
    'fir_burst': 'Compact ignition, a short low-mid pressure contact, then rolling flame and sparse fading embers.',
    'fir_wall': 'Restrained intermittent flame tongues with a few small ember ticks; no continuous noise wall.',
    'thu_charge': 'A handful of short, quiet pre-discharge arcs with real gaps; no rising whistle or buzz.',
    'thu_crack': 'One dry arc fracture and a compact low-mid contact, with two very small delayed branches.',
    'thu_network': 'One main discharge and two subordinate grouped arcs, each with a short, damped body.',
}

DESIGN_NOTES = {
    'direction': 'More realistic and restrained; small-scale combustion and dry electric arcs, not ultimate-sized impacts.',
    'provenance': 'Original deterministic NumPy/SciPy synthesis; no recordings, soundfonts, AI calls or downloads.',
    'fire': {
        'transient': 'A tiny ignition crack and a short band-limited bipolar pressure pulse.',
        'body': 'Independent breath-shaped turbulent packets with irregular spacing and changing bandwidth; no continuous white-noise bed.',
        'tail': 'The combustion expands over 0.1–0.3 seconds, then small embers become sparse and disappear.',
        'removedFromV2': 'Continuous low-frequency noise, regular 23/37Hz flutter and a descending sub-bass sine body.',
    },
    'lightning': {
        'transient': 'A short broadband arc fracture with a compact, rapidly damped structure contact.',
        'body': 'A few milliseconds of low-mid resonant energy rather than sustained pitched synthesis.',
        'tail': 'Mostly silence, interrupted by a small number of much quieter branch arcs.',
        'removedFromV2': '360–2100Hz ascending oscillator, 2.31x tonal partial and sawtooth amplitude modulation; long high hiss and rumble.',
    },
    'timing': 'All six durations match v2 exactly so the existing 15-second demonstrations retain their segment boundaries.',
    'variants': 'Deterministic variations alter packet timing, turbulent excitation, damping and small pressure differences; no large pitch transposition.',
    'mix': 'Peak headroom cap 0.58; no independent loudness normalization that would magnify quiet tails.',
    'acceptance': 'Technical measures can verify finite samples and bounded peaks; realism, restraint and impact need human audition.',
}


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'elemental-impact-v3:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _time(seconds, rate):
    return np.arange(max(2, round(seconds * rate)), dtype=np.float64) / rate


def _band_noise(rng, count, rate, low, high):
    low = max(20., float(low))
    high = min(float(high), rate * .44)
    if low >= high:
        low = high * .35
    audio = signal.sosfilt(signal.butter(2, [low, high], fs=rate, btype='bandpass', output='sos'), rng.standard_normal(count))
    return audio / max(float(np.sqrt(np.mean(audio * audio))), .03)


def _place(destination, source, at, rate, gain=1.):
    begin = round(at * rate)
    skip = max(0, -begin)
    begin = max(0, begin)
    count = min(len(destination) - begin, len(source) - skip)
    if count > 0:
        destination[begin:begin + count] += source[skip:skip + count] * gain


def _packet(rng, rate, seconds, low, high, attack, decay):
    """One finite breath with a local attack, body and fully faded release."""
    t = _time(seconds, rate)
    texture = _band_noise(rng, len(t), rate, low, high)
    envelope = (1 - np.exp(-t / max(attack, .0001))) * np.exp(-t / max(decay, .0005))
    end = np.clip((seconds - t) / min(.016, seconds * .22), 0, 1)
    return texture * envelope * np.sin(end * np.pi / 2) ** 2


def _pressure(rate, rng, strength=1.):
    """A short bipolar pressure contact, intentionally without a sub-bass sine."""
    t = _time(.038, rate)
    width = rng.uniform(.00057, .00076)
    phase = (t - .0033) / width
    core = -phase * np.exp(-.5 * phase * phase)
    # A very short, non-harmonic contact adds body without a long pitched ring.
    contact = np.zeros(len(t))
    for frequency, amp, damping in ((230, .22, .008), (387, .13, .006), (704, .055, .0035)):
        contact += amp * np.sin(2 * np.pi * frequency * rng.uniform(.98, 1.02) * t) * np.exp(-t / damping)
    contact *= np.minimum(t / .0014, 1)
    audio = core + contact
    audio *= np.clip((.038 - t) / .008, 0, 1)
    return audio * strength


def _ember(rate, rng, small=True):
    return _packet(rng, rate, .034 if small else .044,
                   rng.uniform(850, 1250), rng.uniform(3100, 4300),
                   .0008, rng.uniform(.0032, .0055))


def _arc(rate, rng, strength=1., body=True):
    """One dry arc with a 1–8ms fracture and a quickly damped contact body."""
    t = _time(.105, rate)
    audio = np.zeros(len(t))
    # A concentrated contact rather than a long high-frequency spray.
    fracture = _packet(rng, rate, .023, rng.uniform(540, 750), 5700,
                       .00024, rng.uniform(.0024, .0035))
    _place(audio, fracture, .0004, rate, .43)
    micro = _packet(rng, rate, .011, 1700, 6300, .00013, .0011)
    _place(audio, micro, .0007, rate, .13)
    if body:
        # All resonances die in a few cycles; no persistent tonal carrier.
        contact = np.zeros(len(t))
        for freq, gain, decay in ((245, .25, .012), (428, .14, .008), (731, .07, .005)):
            contact += gain * np.sin(2 * np.pi * freq * rng.uniform(.97, 1.03) * t) * np.exp(-t / decay)
        contact *= (1 - np.exp(-t / .0009))
        audio += contact
        low_grain = _packet(rng, rate, .056, 190, 1150, .0016, .010)
        _place(audio, low_grain, .0018, rate, .10)
    audio *= np.clip((.105 - t) / .014, 0, 1)
    return audio * strength


def _fire_charge(rng, rate, n):
    audio = np.zeros(n)
    _place(audio, _ember(rate, rng), .026, rate, .030)
    # Small, irregular flame breaths grow denser without a pitched sweep.
    for index, at in enumerate((.060, .145, .238, .325, .408, .490)):
        at += rng.uniform(-.006, .006)
        duration = rng.uniform(.086, .122)
        breath = _packet(rng, rate, duration, rng.uniform(240, 340),
                         rng.uniform(1550, 2400), .012, rng.uniform(.025, .042))
        _place(audio, breath, at, rate, .065 + .013 * index)
    _place(audio, _pressure(rate, rng), .424, rate, .026)
    return audio


def _fire_burst(rng, rate, n):
    audio = np.zeros(n)
    # Contact is small and quick; the audible expansion is in the next packets.
    _place(audio, _ember(rate, rng, False), .0015, rate, .105)
    _place(audio, _pressure(rate, rng), .010, rate, .135)
    for at, duration, gain in ((.017, .135, .23), (.071, .16, .18),
                              (.145, .16, .125), (.240, .14, .075), (.350, .14, .033)):
        at += rng.uniform(-.004, .004)
        # A distinct swelling exhalation; not a level white-noise explosion.
        flame = _packet(rng, rate, duration, rng.uniform(190, 290),
                        rng.uniform(1750, 2700), rng.uniform(.008, .016),
                        rng.uniform(.031, .046))
        _place(audio, flame, at, rate, gain)
    for at, gain in ((.235, .034), (.371, .021), (.514, .014), (.647, .007)):
        _place(audio, _ember(rate, rng), at + rng.uniform(-.009, .009), rate, gain)
    return audio


def _fire_wall(rng, rate, n):
    audio = np.zeros(n)
    _place(audio, _ember(rate, rng), .025, rate, .037)
    at = .050
    while at < 2.28:
        duration = rng.uniform(.115, .190)
        strength = rng.uniform(.056, .110)
        # Sparse overlapping tongues; no continuously running noise generator.
        strength *= min(1., (at + .06) / .20) * min(1., (2.42 - at) / .48)
        flame = _packet(rng, rate, duration, rng.uniform(240, 400),
                        rng.uniform(1500, 2500), rng.uniform(.016, .028),
                        rng.uniform(.036, .058))
        _place(audio, flame, at, rate, strength)
        at += rng.uniform(.105, .165)
    for at in (.184, .527, .891, 1.413, 1.963, 2.270):
        _place(audio, _ember(rate, rng), at + rng.uniform(-.025, .025), rate,
               rng.uniform(.011, .022) * min(1., (2.5 - at) / .5))
    return audio


def _thunder_charge(rng, rate, n):
    audio = np.zeros(n)
    # Quiet separated electrical contacts; acceleration implies tension, not pitch.
    for index, at in enumerate((.026, .115, .207, .288, .352)):
        _place(audio, _arc(rate, rng, body=False), at + rng.uniform(-.004, .004),
               rate, .070 + .013 * index)
    return audio


def _thunder_crack(rng, rate, n, network=False):
    audio = np.zeros(n)
    _place(audio, _arc(rate, rng), .001, rate, .78)
    # Branches are well below the main contact, with actual silence between them.
    for at, level in ((.027, .14), (.072, .055)):
        _place(audio, _arc(rate, rng, body=False), at + rng.uniform(-.0025, .0025), rate, level)
    if network:
        # Preserve the existing authored 0/.25/.50s discharge grouping, but make
        # successive arcs subordinate instead of three equally loud explosions.
        _place(audio, _arc(rate, rng), .25 + rng.uniform(-.003, .003), rate, .31)
        _place(audio, _arc(rate, rng, body=False), .50 + rng.uniform(-.003, .003), rate, .16)
        _place(audio, _arc(rate, rng, body=False), .535 + rng.uniform(-.002, .002), rate, .027)
    return audio


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Return deterministic mono float64 audio, finite and with peak <= .58.

    Variations 1, 2 and 3 are the authored audition set. Larger positive integers
    remain deterministic, preserving the v2 generator's public calling contract.
    """
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown elemental cue: {name}')
    if not isinstance(variation, (int, np.integer)) or variation < 1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate < 22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    n = round(CUE_DURATIONS[name] * sample_rate)
    rng = _rng(name, variation)
    if name == 'fir_charge':
        audio = _fire_charge(rng, sample_rate, n)
    elif name == 'fir_burst':
        audio = _fire_burst(rng, sample_rate, n)
    elif name == 'fir_wall':
        audio = _fire_wall(rng, sample_rate, n)
    elif name == 'thu_charge':
        audio = _thunder_charge(rng, sample_rate, n)
    else:
        audio = _thunder_crack(rng, sample_rate, n, network=name == 'thu_network')
    # Low-frequency headroom is intentionally modest: no deep boom or rumble.
    cutoff = 125 if name.startswith('fir_') else 155
    audio = signal.sosfilt(signal.butter(2, cutoff, fs=sample_rate,
                                       btype='highpass', output='sos'), audio)
    # Do not fill intentional silence with a constant tiny DC offset by
    # subtracting the whole-record mean; the high-pass already rejects bias.
    if not np.all(np.isfinite(audio)):
        raise FloatingPointError('Non-finite generated sample')
    fade_in = max(2, round(.0012 * sample_rate))
    fade_out = max(2, round(.012 * sample_rate))
    audio[:fade_in] *= np.linspace(0., 1., fade_in)
    audio[-fade_out:] *= np.linspace(1., 0., fade_out)
    peak = float(np.max(np.abs(audio)))
    audio *= min(1., .58 / max(peak, 1e-12))
    return np.asarray(audio, dtype=np.float64)
