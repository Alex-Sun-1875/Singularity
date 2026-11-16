"""Arrow-tip metal contacts over the accepted weighted, short-air v6 bow.

Pure import-safe synthesis. No files, playback, recordings, downloads or model
calls. Armor contact is materially different from a normal/soft target: a small
hard arrow point, not a miniature copy of the warrior's broad blade clang.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
from pathlib import Path
import types

import numpy as np
from scipy import signal


RATE = 44100
CUE_DURATIONS = {
    'bow_draw': .62, 'bow_release': .30,
    'bow_pierce': .30, 'bow_heavy': .42,
}
CONTACT_DURATIONS = {'soft': .30, 'armor': .30}
DESCRIPTIONS = {
    'bow_draw': 'Retained low wood and string-tension friction; no new wind or musical string note.',
    'bow_release': 'Retained firm string latch and limb recoil, with only the existing short arrow air.',
    'bow_pierce': 'Weighted puncture and short shaft recoil with a very small, damped metal-tip contact.',
    'bow_heavy': 'A heavier weighted arrow contact with a firmer localized metal-tip clink and short metal rebound.',
}
DESIGN_NOTES = {
    'userPreference': 'Give warrior/bow impacts metal collision character while retaining the previously requested weight and short bow air.',
    'provenance': 'Original deterministic NumPy/SciPy material models using the accepted v6 bow source. No recordings, soundbanks, downloads, AI or playback.',
    'unchangedPreparation': 'bow_draw and bow_release directly reuse v6; no late air wake, guitar-like pluck or new pitched string is introduced.',
    'arrowMetal': 'A finite noise excitation drives localized non-harmonic 947/1361/1987/2719Hz tip modes. They damp in roughly 10–30ms and finish within 0.12s, with a small retouch rather than a long ringing plate.',
    'body': 'The v6 puncture, shaft recoil and weighted low-mid body are retained. Armor adds a small 251/443/719Hz contact support beneath the tip resonance.',
    'materialPolicy': {
        'synth_cue.bow_pierce': 'Subtle arrowhead resonance; this does not assert that every target wears armor.',
        'synth_cue.bow_heavy': 'Firmer local contact and very short metal rebound, still below a full armored collision.',
        'synth_contact.soft': 'Ordinary weighted v6 puncture; no added armor clang.',
        'synth_contact.armor': 'A distinctly harder localized metal contact over the same puncture, for an armored target.',
    },
    'contactDurationSeconds': CONTACT_DURATIONS.copy(),
    'air': 'No new air source. Existing v6 release/pierce/heavy air ends by .083/.064/.074s.',
    'exclusions': ['long wind', 'glass bell', 'long ringing chime', 'guitar string', 'scaled-down warrior clang'],
    'mix': 'Source peak cap .64 is safety only; target material changes source layers rather than uniformly raising playback gain.',
    'acceptance': 'Finite samples and envelope/frequency measures are technical evidence; metal identity and preference need user audition.',
}


@lru_cache(maxsize=1)
def _v6():
    path = Path(__file__).resolve().parents[1] / 'audio-impact-v6' / 'physical_cues.py'
    module = types.ModuleType('_weighted_v6_bow_for_v7')
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding='utf-8'), str(path), 'exec'), module.__dict__)
    return module


def _rng(name, variation):
    seed = int.from_bytes(hashlib.sha256(f'arrow-metal-v7:{name}:{variation}'.encode()).digest()[:8], 'little')
    return np.random.default_rng(seed)


def _place(destination, source, at, rate, gain=1.):
    begin = round(at * rate)
    skip = max(0, -begin)
    begin = max(0, begin)
    count = min(len(destination) - begin, len(source) - skip)
    if count > 0:
        destination[begin:begin + count] += source[skip:skip + count] * gain


def _window_rms(audio, rate, start, end, target):
    part = audio[round(start * rate):min(len(audio), round(end * rate))]
    return audio * target / max(1e-9, float(np.sqrt(np.mean(part * part))))


def _band(rng, n, rate, low, high):
    x = signal.sosfilt(signal.butter(2, [low, min(high, rate * .44)],
                                    btype='bandpass', fs=rate, output='sos'), rng.standard_normal(n))
    return x / max(1e-9, float(np.sqrt(np.mean(x * x))))


def _tip_modes(rng, rate, rms, firm=False):
    """Small hard-point contact, noise-excited and strongly damped."""
    seconds = .120 if firm else .100
    t = np.arange(round(seconds * rate), dtype=np.float64) / rate
    excitation = np.zeros(len(t), np.float64)
    count = max(5, round((.00105 if firm else .0008) * rate))
    excitation[:count] = rng.standard_normal(count) * np.sin(np.linspace(0, np.pi, count))
    out = np.zeros(len(t), np.float64)
    for frequency, level, decay in ((947, 1., .027), (1361, .67, .024),
                                    (1987, .47, .017), (2719, .23, .011)):
        frequency *= rng.uniform(.965, 1.035)
        decay *= rng.uniform(.89, 1.11) * (1.02 if firm else .82)
        radius = np.exp(-1 / (rate * decay))
        mode = signal.lfilter([1.], [1., -2 * radius * np.cos(2 * np.pi * frequency / rate), radius * radius], excitation)
        mode = _window_rms(mode, rate, .003, .043, 1.)
        out += mode * level
    # Finite contact grain prevents the modes becoming a pure glassy note.
    grain = _band(rng, len(t), rate, 750, 2950)
    grain *= -np.expm1(-t / .0009) * np.exp(-t / .0065)
    grain = _window_rms(grain, rate, .0015, .018, .25)
    out += grain
    out *= np.sin(np.clip(t / .0012, 0, 1) * np.pi / 2) ** 2
    out *= np.sin(np.clip((seconds - t) / .022, 0, 1) * np.pi / 2) ** 2
    return _window_rms(out, rate, .003, .046, rms)


def _contact_support(rng, rate):
    t = np.arange(round(.098 * rate), dtype=np.float64) / rate
    count = max(5, round(.002 * rate))
    excitation = np.zeros(len(t), np.float64)
    excitation[:count] = rng.standard_normal(count) * np.sin(np.linspace(0, np.pi, count))
    body = np.zeros(len(t), np.float64)
    for frequency, level, decay in ((251, 1., .021), (443, .66, .016), (719, .27, .010)):
        frequency *= rng.uniform(.96, 1.04)
        radius = np.exp(-1 / (rate * decay))
        mode = signal.lfilter([1.], [1., -2 * radius * np.cos(2 * np.pi * frequency / rate), radius * radius], excitation)
        body += _window_rms(mode, rate, .003, .043, 1.) * level
    body *= np.sin(np.clip((.098 - t) / .024, 0, 1) * np.pi / 2) ** 2
    return _window_rms(body, rate, .003, .045, .027)


def _validate(variation, sample_rate):
    if not isinstance(variation, (int, np.integer)) or variation < 1:
        raise ValueError('variation must be a positive integer')
    if not isinstance(sample_rate, (int, np.integer)) or sample_rate < 22050:
        raise ValueError('sample_rate must be an integer >= 22050')


def _finish(audio, rate):
    if not np.all(np.isfinite(audio)):
        raise FloatingPointError('Non-finite arrow metal synthesis')
    fade_in = max(2, round(.0008 * rate))
    fade_out = max(2, round(.018 * rate))
    audio[:fade_in] *= np.linspace(0, 1, fade_in)
    audio[-fade_out:] *= np.linspace(1, 0, fade_out)
    audio *= min(1., .64 / max(1e-12, float(np.max(np.abs(audio)))))
    return np.asarray(audio, dtype=np.float64)


def synth_cue(name: str, variation: int = 1, sample_rate: int = RATE) -> np.ndarray:
    """Generate one v7 bow cue with ordinary/light-tip versus hard contact balance."""
    if name not in CUE_DURATIONS:
        raise ValueError(f'Unknown bow cue: {name}')
    _validate(variation, sample_rate)
    audio = _v6().synth_cue(name, variation, sample_rate).copy()
    if name in ('bow_draw', 'bow_release'):
        return audio
    rng = _rng(name, variation)
    heavy = name == 'bow_heavy'
    # The arrowhead gives a small contact signature; actual armor uses the
    # material-specific API below rather than turning every hit into a clang.
    _place(audio, _tip_modes(rng, sample_rate, .038 if heavy else .014,
                            firm=heavy), .0038, sample_rate)
    if heavy:
        _place(audio, _tip_modes(rng, sample_rate, .012, firm=False),
               .023 + rng.uniform(-.0015, .0015), sample_rate)
    return _finish(audio, sample_rate)


def synth_contact(variation: int = 1, material: str = 'armor',
                  sample_rate: int = RATE) -> np.ndarray:
    """Return a .30s armor/soft arrow contact; material does not affect draw/release."""
    if material not in CONTACT_DURATIONS:
        raise ValueError("material must be 'armor' or 'soft'")
    _validate(variation, sample_rate)
    audio = _v6().synth_cue('bow_pierce', variation, sample_rate).copy()
    if material == 'soft':
        return audio
    rng = _rng('armor-contact', variation)
    _place(audio, _tip_modes(rng, sample_rate, .074, firm=True), .0028, sample_rate)
    _place(audio, _contact_support(rng, sample_rate), .004, sample_rate)
    _place(audio, _tip_modes(rng, sample_rate, .017, firm=False),
           .021 + rng.uniform(-.0015, .0015), sample_rate)
    return _finish(audio, sample_rate)
