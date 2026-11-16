"""Longer material-specific fire and electric-arc tails over accepted v4 impacts.

Pure synthesis API: mono float64, no writes/playback/downloads/model calls.
The original v4 burst sources are loaded lazily and retained; v5 adds actual
combustion/electrical sustain rather than extending a file with silent padding.
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
    'fir_charge': 'Accepted gathering flame extended with a final irregular combustion breath.',
    'fir_burst': 'Accepted v4 ignition and pressure body, followed by a longer rolling flame and embers reaching about 0.9 seconds.',
    'fir_wall': 'Accepted sparse flame tongues extended into a longer, fading combustion release.',
    'thu_charge': 'Small pre-discharge arcs followed by a rising-density rough electrical sizzle, without a tonal whistle.',
    'thu_crack': 'Accepted v4 main fracture and short thunder body plus an audible grouped electrical sizzle lasting roughly 0.1–0.7 seconds.',
    'thu_network': 'Accepted layered discharges at 0/.25/.50 seconds with overlapping, successively weaker electrical sizzle tails.',
}
DESIGN_NOTES = {
    'userPreference': '2026-11-16: allow a little more time; lightning should audibly sizzle, and other professions should keep material-specific releases.',
    'provenance': 'Original deterministic NumPy/SciPy models, reusing accepted local v4 source code; no recordings, downloads, soundbanks or AI generation.',
    'acceptedFront': 'The v4 fire/thunder synth outputs are copied without changing their source model. New release layers enter after the leading impact.',
    'electricSustain': {
        'texture': 'Hundreds of irregular, overlapping 6–16ms micro-discharge grains per second, assembled into finite rough groups. This is actual sustained electrical texture, not three isolated clicks or silent padding.',
        'range': 'Low-mid crack body remains from v4. Sizzle occupies a changing 650–5000Hz band with no pure carrier, laser sweep or fixed sawtooth.',
        'envelope': 'Quiet under the main crack, audible from about .1 to .7 seconds, with stochastic group gaps and gradual loss of charge.',
        'network': 'Successive discharges renew the tail at lower intensity; no equally loud re-explosions.',
    },
    'fireRelease': 'Independent slower flame breaths and sparse ember ticks continue to roughly .65–.9 seconds; no constant full-width white-noise wall.',
    'durations': CUE_DURATIONS.copy(),
    'mix': 'Source peak cap .64, no per-cue loudness normalization; added tails are lower than the retained impact.',
    'acceptance': 'Tail energy and active duration are technical evidence. Whether the sound reads as electrical sizzle and feels good requires human audition.',
}


@lru_cache(maxsize=2)
def _v4(family):
    filename = 'fire_cues.py' if family == 'fir' else 'thunder_cues.py'
    source = Path(__file__).resolve().parents[1] / 'audio-impact-v4' / filename
    return runpy.run_path(str(source))


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'elemental-tail-v5:{name}:{variation}'.encode()).digest()[:8], 'little')
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


def _noise(rng, n, rate, low, high):
    high = min(high, .44 * rate)
    low = min(max(20., low), high * .8)
    result = signal.sosfilt(signal.butter(2, [low, high], btype='bandpass', fs=rate,
                                          output='sos'), rng.standard_normal(n))
    return result / max(1e-9, float(np.sqrt(np.mean(result * result))))


def _packet(rng, rate, seconds, low, high, attack, decay):
    t = _time(seconds, rate)
    envelope = -np.expm1(-t / attack) * np.exp(-t / decay)
    ending = np.sin(np.clip((seconds - t) / min(.020, seconds * .23), 0, 1) * np.pi / 2) ** 2
    return _noise(rng, len(t), rate, low, high) * envelope * ending


def _rms_set(audio, target):
    return audio * target / max(1e-10, float(np.sqrt(np.mean(audio * audio))))


def _electrical_group(rng, rate, seconds):
    """A rough finite stream of overlapping micro-arcs with no tonal carrier."""
    out = np.zeros(round(seconds * rate), np.float64)
    at = rng.uniform(0., .001)
    while at < seconds - .008:
        duration = rng.uniform(.006, .016)
        grain = _packet(rng, rate, duration, rng.uniform(650, 1100),
                        rng.uniform(3200, 5000), rng.uniform(.00010, .00028),
                        rng.uniform(.0011, .0028))
        _place(out, grain, at, rate, rng.uniform(.55, 1.10))
        # Irregular dense events overlap; a stable buzz pitch is not introduced.
        at += rng.uniform(.0014, .0040)
    t = np.arange(len(out)) / rate
    attack = np.sin(np.clip(t / .005, 0, 1) * np.pi / 2) ** 2
    end = np.sin(np.clip((seconds - t) / .011, 0, 1) * np.pi / 2) ** 2
    return _rms_set(out * attack * end, 1.)


def _sizzle(rng, rate, seconds=.62, rms=.022, decay=.45):
    """Grouped sustained electrical texture, with small real gaps and discharge."""
    out = np.zeros(round(seconds * rate), np.float64)
    at = .0
    while at < seconds - .025:
        duration = min(rng.uniform(.055, .105), seconds - at)
        group = _electrical_group(rng, rate, duration)
        _place(out, group, at, rate, rng.uniform(.75, 1.10))
        at += duration - rng.uniform(.003, .012) + rng.uniform(.003, .015)
    t = np.arange(len(out)) / rate
    # A quiet but genuinely audible release, rather than an almost-zero noise bed.
    envelope = (.72 + .28 * np.exp(-t / .050)) * np.exp(-t / decay)
    envelope *= np.sin(np.clip(t / .012, 0, 1) * np.pi / 2) ** 2
    envelope *= np.sin(np.clip((seconds - t) / .065, 0, 1) * np.pi / 2) ** 2
    return _rms_set(out, rms) * envelope


def _thunder_tail(name, rng, rate, n):
    out = np.zeros(n, np.float64)
    if name == 'thu_charge':
        stream = _sizzle(rng, rate, .37, rms=.010, decay=.90)
        t = np.arange(len(stream)) / rate
        stream *= .45 + .55 * np.clip(t / .30, 0, 1)
        _place(out, stream, .185, rate)
    else:
        _place(out, _sizzle(rng, rate, .62, rms=.041, decay=.58), .090, rate)
        if name == 'thu_network':
            _place(out, _sizzle(rng, rate, .60, rms=.0135, decay=.42), .325, rate)
            _place(out, _sizzle(rng, rate, .60, rms=.0085, decay=.38), .570, rate)
    return out


def _ember(rng, rate):
    return _packet(rng, rate, .035, rng.uniform(1000, 1500),
                   rng.uniform(3600, 4800), .0006, rng.uniform(.0030, .0052))


def _fire_tail(name, rng, rate, n):
    out = np.zeros(n, np.float64)
    if name == 'fir_burst':
        # Overlapping but finite breaths decay through a longer release.
        for at, seconds, gain in ((.285, .20, .115), (.405, .21, .095),
                                  (.535, .20, .075), (.655, .19, .052),
                                  (.770, .16, .026)):
            flame = _packet(rng, rate, seconds, rng.uniform(220, 370),
                            rng.uniform(1700, 2700), rng.uniform(.012, .023),
                            rng.uniform(.045, .063))
            _place(out, flame, at + rng.uniform(-.008, .008), rate, gain)
        for at, gain in ((.610, .025), (.736, .021), (.838, .015), (.926, .008)):
            _place(out, _ember(rng, rate), at + rng.uniform(-.008, .008), rate, gain)
    elif name == 'fir_charge':
        for at, gain in ((.525, .085), (.605, .060)):
            flame = _packet(rng, rate, .102, 250, 2200, .013, .032)
            _place(out, flame, at + rng.uniform(-.006, .006), rate, gain)
    else:
        for at, gain in ((2.255, .078), (2.393, .066), (2.526, .049), (2.662, .029)):
            flame = _packet(rng, rate, .22, rng.uniform(240, 390),
                            rng.uniform(1600, 2450), .020, rng.uniform(.050, .067))
            _place(out, flame, at + rng.uniform(-.009, .009), rate, gain)
        for at, gain in ((2.430, .022), (2.658, .016), (2.836, .009)):
            _place(out, _ember(rng, rate), at + rng.uniform(-.008, .008), rate, gain)
    return out


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Generate retained v4 impact plus a longer material release, peak <= .64."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown elemental cue: {name}')
    if not isinstance(variation, (int, np.integer)) or variation < 1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate < 22050:
        raise ValueError('sample_rate must be an integer >= 22050')
    n = round(CUE_DURATIONS[name] * sample_rate)
    family = name[:3]
    retained = _v4(family)['synth_cue'](name, variation, sample_rate)
    audio = np.zeros(n, np.float64)
    _place(audio, retained, 0., sample_rate)
    rng = _rng(name, variation)
    if family == 'thu':
        added = _thunder_tail(name, rng, sample_rate, n)
        cutoff = 380
    else:
        added = _fire_tail(name, rng, sample_rate, n)
        cutoff = 130
    # Filter only new releases so the accepted v4 front is retained verbatim.
    added = signal.sosfilt(signal.butter(2, cutoff, btype='highpass', fs=sample_rate,
                                         output='sos'), added)
    audio += added
    if not np.all(np.isfinite(audio)):
        raise FloatingPointError('Non-finite elemental release')
    fade_in = max(2, round(.0008 * sample_rate))
    fade_out = max(2, round(.018 * sample_rate))
    audio[:fade_in] *= np.linspace(0., 1., fade_in)
    audio[-fade_out:] *= np.linspace(1., 0., fade_out)
    audio *= min(1., .64 / max(1e-12, float(np.max(np.abs(audio)))))
    return np.asarray(audio, dtype=np.float64)
