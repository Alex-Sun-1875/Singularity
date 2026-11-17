"""Thicken the game-styled contacts after the user's V10 audition feedback.

Reuses the V10 delivery/validation pipeline. Remix transient/body separately
and add a new finite low-mid pressure layer, rather than lowering global pitch.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[4]
path = ROOT / 'src/cocos/tools/audio-impact-v10/make_game_contacts.py'
spec = importlib.util.spec_from_file_location('_weighted_game_authoring', path)
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)
RATE = tool.RATE


def make_contact(cue, variation, old, weight, shared, war, bow):
    warrior = cue.startswith('war_')
    heavy = cue in ('war_finish', 'bow_heavy')
    t = np.arange(len(old)) / RATE
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(f'weighted-game-v11:{cue}:{variation}'.encode()).digest()[:8], 'little'))
    # Complementary split preserves the original attack timing while allowing
    # the brittle edge and body to be balanced independently.
    body = signal.sosfilt(signal.butter(2, 1120 if warrior else 1250, 'lowpass', fs=RATE, output='sos'), old)
    edge = (old - body) * (.28 if warrior else .24)
    body *= .94
    # Finite band-limited pressure adds sustained weight in phone-audible mids.
    # No sine kick, sub-bass oscillator, extra metal ring or long bow-air tail.
    attack = np.sin(np.clip(t / .0022, 0, 1) * np.pi / 2) ** 2
    pressure = shared._band(rng, len(old), RATE, 155 if heavy else 180, 760 if warrior else 950)
    decay = .059 if warrior and heavy else .047 if warrior else .036 if heavy else .028
    pressure *= attack * np.exp(-t / decay) * tool.gate(t, .205 if warrior and heavy else .170 if warrior else .115)
    pressure = tool.balance(pressure, .095 if warrior and heavy else .078 if warrior else .054 if heavy else .045, .006, .085)
    # Soft saturation densifies the pressure layer only, leaving the retained
    # material response separate. This is not a full-mix treble cut alone.
    pressure = np.tanh(pressure * 3.) / 3.
    audio = body + edge + pressure
    match_gain = tool.rms(old) / max(1e-12, tool.rms(audio))
    audio *= match_gain
    audio = signal.sosfilt(signal.butter(2, 85, 'highpass', fs=RATE, output='sos'), audio)
    audio *= attack * tool.gate(t, tool.CONFIG[cue]['end'])
    safety_gain = min(1., .60 / max(1e-12, float(np.max(np.abs(audio)))))
    audio *= safety_gain
    audio[0] = audio[-1] = 0
    return audio, dict(baseline='V10 user-auditioned game contact', edgeRelativeGain=.28 if warrior else .24,
                       bodyCrossoverHz=1120 if warrior else 1250, bodyGain=.94,
                       newPressureBandHz=[155 if heavy else 180, 760 if warrior else 950],
                       pressureDecaySeconds=decay, pressureAttackSeconds=.0022,
                       activeRmsBefore=tool.rms(old), activeRmsAfter=tool.rms(audio),
                       matchGain=match_gain, safetyGain=safety_gain,
                       design='Reduce brittle high edge, retain material identity and add a finite saturated low-mid pressure body. No global pitch change or runtime gain increase.')


if __name__ == '__main__':
    tool.VERSION = 11
    tool.BASE = ROOT / 'src/cocos/assets/resources/audio/combat-v10'
    tool.RUNTIME = ROOT / 'src/cocos/assets/resources/audio/combat-v11'
    tool.OUT = ROOT / 'source-art/audio/impact-weighted-game-v11'
    tool.DIRECTION = 'User feedback: V10 is too crisp. Reduce the brittle edge, add thicker finite low-mid pressure and soften the first 2ms while retaining game energy and material differences.'
    tool.make_contact = make_contact
    tool.main()
