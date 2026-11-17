"""Author game-styled weapon contacts with the project's existing DSP tools.

No downloads, model calls, new dependencies, runtime synthesis or game export.
V9 recordings become a quiet, short texture beneath designed impact layers.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
from scipy import signal

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / 'src/cocos'
TOOLS = PROJECT / 'tools'
BASE = PROJECT / 'assets/resources/audio/combat-v9'
RUNTIME = PROJECT / 'assets/resources/audio/combat-v10'
OUT = ROOT / 'source-art/audio/impact-game-v10'
RATE = 44100
VERSION = 10
DIRECTION = 'Designed low-mid impact, cutting attack and brief energy follow-through; metal varies by material, V9 foley is a quiet short texture.'
DEFAULT_FFMPEG = Path('C:/Program Files (x86)/Lenovo/LegionZone/2.0.30.11033/SEGamingAI/services/editor/ffmpeg.exe')
# RMS assignments are authoring balances, not claims of listening approval.
CONFIG = {
    'war_slash': dict(body=.090, edge=.045, energy=.026, metal=.012, texture=.009, end=.235),
    'war_armor': dict(body=.095, edge=.048, energy=.021, metal=.035, texture=.012, end=.255),
    'war_finish': dict(body=.118, edge=.054, energy=.040, metal=.018, texture=.010, end=.295),
    'bow_pierce': dict(body=.066, edge=.037, energy=.010, metal=.005, texture=.004, end=.140),
    'bow_heavy': dict(body=.084, edge=.043, energy=.016, metal=.008, texture=.005, end=.180),
    'bow_armor': dict(body=.071, edge=.043, energy=.009, metal=.024, texture=.008, end=.165),
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def rms(audio, start=.003, end=.075):
    part = audio[round(start * RATE):round(end * RATE)]
    return float(np.sqrt(np.mean(part * part)))


def balance(audio, target, start=.003, end=.075):
    return audio * target / max(1e-12, rms(audio, start, end))


def gate(t, end, fade=.025):
    return np.sin(np.clip((end - t) / fade, 0, 1) * np.pi / 2) ** 2


def make_contact(cue, variation, old, weight, shared, war, bow):
    cfg = CONFIG[cue]
    warrior = cue.startswith('war_')
    armor = cue.endswith('armor')
    heavy = cue in ('war_finish', 'bow_heavy')
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(f'game-v10:{cue}:{variation}'.encode()).digest()[:8], 'little'))
    n = len(old)
    t = np.arange(n) / RATE
    attack = np.sin(np.clip(t / .001, 0, 1) * np.pi / 2) ** 2
    # Existing weighted synthetic body, stripped of physical resonant tails.
    body = signal.sosfilt(signal.butter(2, [155, 1250 if warrior else 1450], 'bandpass', fs=RATE, output='sos'), weight)
    body = np.tanh(body * 4.2) / 4.2
    body *= attack * np.exp(-np.maximum(0, t - .018) / (.040 if heavy else .028)) * gate(t, .155 if warrior else .105)
    body = balance(body, cfg['body'])
    # A defined cutting/point attack replaces the long, irregular foley scrape.
    edge = shared._band(rng, n, RATE, 850 if warrior else 1200, 4700 if armor else 3900)
    edge *= attack * np.exp(-t / (.011 if warrior else .007)) * gate(t, .055 if warrior else .035, .012)
    edge = balance(edge, cfg['edge'], .001, .025)
    # Two overlapping finite noise bands produce a descending energy gesture,
    # without a pitched laser, bell, bass-drum oscillator or added long bow air.
    top = shared._band(rng, n, RATE, 1150, 4100)
    low = shared._band(rng, n, RATE, 320, 1650)
    energy = (top * np.exp(-t / .018) + low * (1 - np.exp(-t / .010)) * np.exp(-t / (.060 if heavy else .040)))
    energy *= (1 - np.exp(-t / .003)) * gate(t, .190 if warrior and heavy else .145 if warrior else .065, .020)
    energy = balance(energy, cfg['energy'], .008, .075)
    # Retain recognisable armor response; ordinary contacts stay softer.
    metal = np.zeros(n)
    response = war._plate(rng, RATE, .19, armor=armor, heavy=heavy) if warrior else bow._tip_modes(rng, RATE, 1., firm=armor)
    shared._place(metal, response, .002, RATE)
    metal *= np.exp(-np.maximum(0, t - .016) / (.040 if armor else .023)) * gate(t, .165 if warrior else .100)
    metal = balance(metal, cfg['metal'])
    # V9/CC0 provenance remains: at most 45-65ms of quiet contact grain.
    texture = signal.sosfilt(signal.butter(2, [700, 3300], 'bandpass', fs=RATE, output='sos'), old)
    texture *= attack * np.exp(-t / .014) * gate(t, .065 if warrior else .045, .015)
    texture = balance(texture, cfg['texture'])
    layers = dict(body=body, edge=edge, energy=energy, metal=metal, recordedTexture=texture)
    audio = sum(layers.values())
    # Match the old active-window RMS, leaving the new timbre/envelope to carry
    # the improvement. No runtime gain increase or global pitch shift.
    match_gain = rms(old) / max(1e-12, rms(audio))
    audio *= match_gain
    audio = signal.sosfilt(signal.butter(2, 85, 'highpass', fs=RATE, output='sos'), audio)
    audio *= attack * gate(t, cfg['end'])
    safety_gain = min(1., .60 / max(1e-12, float(np.max(np.abs(audio)))))
    audio *= safety_gain
    audio[0] = audio[-1] = 0
    energies = {name: float(np.sum(layer * layer)) for name, layer in layers.items()}
    return audio, dict(layerEnergyFractions={name: value / sum(energies.values()) for name, value in energies.items()},
                       activeWindowSeconds=[.003, .075], activeRmsBefore=rms(old), activeRmsAfter=rms(audio),
                       matchGain=match_gain, safetyGain=safety_gain, audibleGateEndSeconds=cfg['end'],
                       recordedTextureEndSeconds=.065 if warrior else .045,
                       layerRmsTargets=cfg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=DEFAULT_FFMPEG)
    args = parser.parse_args()
    if not args.ffmpeg.is_file():
        parser.error('Pass an installed FFmpeg path. Nothing is downloaded.')
    pcm = load('_game10_pcm', TOOLS / 'prepare-combat-audio.py')
    legacy = load('_game10_metrics', TOOLS / 'audio-direction-v2/sfx_samples.py')
    delivery = load('_game10_delivery', TOOLS / 'audio-direction-v2/assemble_studies.py')
    matching = load('_game10_matching', TOOLS / 'audio-impact-v3/make_impact_studies.py')
    levels = load('_game10_levels', TOOLS / 'audio-impact-v4/make_burst_studies.py')
    previous = load('_game10_bank_helpers', TOOLS / 'audio-impact-v8/make_wuxia_contacts.py')
    physical = load('_game10_weight', TOOLS / 'audio-impact-v6/physical_cues.py')
    war = load('_game10_sword', TOOLS / 'audio-impact-v7/war_cues.py')
    bow = load('_game10_bow', TOOLS / 'audio-impact-v7/bow_cues.py')
    shared = physical._v5()
    previous.validate_source()
    delivery.STUDY = OUT
    originals = sorted(BASE.glob('*/*.wav'))
    if len(originals) != 45:
        raise ValueError('Expected complete 45-clip baseline bank')
    protected = {p.relative_to(ROOT).as_posix(): digest(p) for p in originals}
    music = {p.relative_to(ROOT).as_posix(): digest(p) for p in (BASE.parent / 'music').glob('*') if p.is_file()}
    for folder in (OUT / 'clips', OUT / 'audition', RUNTIME):
        folder.mkdir(parents=True, exist_ok=True)
    pcm.meta(RUNTIME, 'directory')
    assets, old_bank, new_bank = [], {}, {}
    for original in originals:
        cue, variant = original.stem.rsplit('_v', 1)
        variation = int(variant)
        family = original.parent.name
        folder = RUNTIME / family
        folder.mkdir(exist_ok=True)
        pcm.meta(folder, 'directory')
        destination = folder / original.name
        old = pcm.read_wav(original)
        item = dict(cue=cue, variation=variation, changed=cue in CONFIG,
                    source=original.relative_to(ROOT).as_posix(), sourceSha256=digest(original))
        if cue in CONFIG:
            weight_path = BASE.parent / 'combat-v7' / family / original.name
            audio, edits = make_contact(cue, variation, old, pcm.read_wav(weight_path), shared, war, bow)
            master = OUT / 'clips' / f'{cue}_v{variation:02d}.wav'
            legacy._write_wav(master, audio)
            item.update(edits=edits, weightSource=weight_path.relative_to(ROOT).as_posix(), weightSourceSha256=digest(weight_path),
                        sourceMaster=master.relative_to(ROOT).as_posix(), sourceMasterSha256=digest(master),
                        quantization=previous.write_runtime(destination, audio))
        else:
            shutil.copyfile(original, destination)
        audio = pcm.read_wav(destination)
        pcm.meta(destination, 'audio-clip')
        metrics = legacy.audio_metrics(audio)
        if not metrics['finite'] or metrics['clippingSamples'] or metrics['oversampledPeakDbfs'] > -1:
            raise ValueError(f'Unsafe runtime sound: {destination}')
        if len(audio) != len(old) or audio[0] != 0 or abs(audio[-1]) > 1 / 32767:
            raise ValueError(f'Duration or boundary mismatch: {destination}')
        item.update(runtimePath=destination.relative_to(ROOT).as_posix(), resourcePath=f'audio/combat-v{VERSION}/{family}/{destination.stem}',
                    uuid=json.loads(Path(str(destination) + '.meta').read_text())['uuid'],
                    bytes=destination.stat().st_size, sha256=digest(destination), metrics=metrics)
        assets.append(item)
        old_bank[(cue, variation)] = old
        new_bank[(cue, variation)] = audio
    changed = [a for a in assets if a['changed']]
    if len(changed) != 18 or len({a['sha256'] for a in changed}) != 18:
        raise ValueError('Expected 18 unique revised contacts')
    outputs = []
    main_events = [('war_slash',1,.35),('war_armor',1,1.65),('war_finish',1,3.),('bow_pierce',1,4.8),('bow_heavy',1,6.),('bow_armor',1,7.2),('war_slash',1,9.),('war_armor',2,9.4),('war_finish',3,9.82),('bow_armor',1,12.),('bow_armor',2,12.38),('bow_heavy',3,12.76),('war_armor',3,15.),('bow_armor',3,16.3)]
    comparison_events = [('war_slash',1,.35),('war_armor',1,1.45),('war_finish',1,2.55),('bow_pierce',1,4.05),('bow_heavy',1,4.95),('bow_armor',1,5.85),('war_slash',2,6.6),('war_armor',2,7.),('war_finish',3,7.4)]
    with tempfile.TemporaryDirectory(prefix='sword-fire-game-v10-') as temporary:
        scratch = Path(temporary)
        def measure(audio, name):
            path = scratch / f'{name}.wav'
            legacy._write_wav(path, audio)
            return delivery.loudness(args.ffmpeg, path)
        main_audio, markers = previous.render_phrase(new_bank, 18, main_events, legacy)
        measured = measure(main_audio, 'main')
        matched, gain, _ = matching.match_linear(main_audio, measured, levels.peak_target(measured), args.ffmpeg, scratch, 'main', legacy, delivery)
        result = delivery.emit(args.ffmpeg, OUT / 'audition', f'weapon-contacts-v{VERSION}', '剑与火 · 游戏化击打', matched, scratch)
        result.update(markers=markers, presentationGain=gain)
        outputs.append(result)
        phrases = [previous.render_phrase(bank, 8, comparison_events, legacy)[0] for bank in (old_bank, new_bank)]
        measures = [measure(part, f'ab-{i}') for i, part in enumerate(phrases)]
        target = min(levels.peak_target(level) for level in measures)
        pairs, pair_levels = [], []
        for version, part, level in zip((f'v{VERSION-1}', f'v{VERSION}'), phrases, measures):
            part, gain, measured = matching.match_linear(part, level, target, args.ffmpeg, scratch, version, legacy, delivery)
            pairs.append(part)
            pair_levels.append(dict(version=version, lufs=float(measured['input_i']), gain=gain))
        if abs(pair_levels[0]['lufs'] - pair_levels[1]['lufs']) > .15:
            raise ValueError('A/B loudness mismatch')
        comparison = np.concatenate((pairs[0], np.zeros((RATE, 2)), pairs[1], np.zeros((RATE, 2))))
        result = delivery.emit(args.ffmpeg, OUT / 'audition', f'v{VERSION-1}-v{VERSION}-matched', '剑与火 · 击打音色同响度对照', comparison, scratch)
        result.update(pairLevels=pair_levels, sections=[dict(version=f'v{VERSION-1}',start=0,end=8),dict(kind='silence',start=8,end=9),dict(version=f'v{VERSION}',start=9,end=17)])
        outputs.append(result)
    if any(digest(ROOT / p) != sha for p, sha in {**protected, **music}.items()):
        raise ValueError('Protected baseline or music changed')
    if any(a['sha256'] != a['sourceSha256'] for a in assets if not a['changed']):
        raise ValueError('Preserved cue changed')
    dump(OUT / 'manifest.json', dict(version=VERSION, date='2026-11-17',
         direction=DIRECTION,
         production='Existing original project layers and NumPy/SciPy/FFmpeg authoring pipeline. Original V9 CC0 contact texture retained with provenance. No downloads, AI calls or new runtime dependencies.',
         licenseEvidence='source-art/audio/impact-wuxia-v8/sources/starninjas/source-manifest.json',
         assets=assets, outputs=outputs, totalRuntimeBytes=sum(a['bytes'] for a in assets),
         preservation=dict(changedContacts=18, bytePreservedClips=27, oldBank=protected, music=music),
         validation=dict(clipCount=45, distinctChangedVariants=18, noClipping=True, unchangedDurations=True, sourceBoundaryChecks=True),
         listeningAcceptance='Pending user listening; numerical checks do not establish perceptual quality.',
         runtimeAcceptance='Assets generated; see separate integration verification.', deviceAcceptance='TapTap target-device listening pending.'))
    print(json.dumps(dict(output=str(OUT), runtime=str(RUNTIME), clips=45, changed=18, preserved=27,
                          bytes=sum(a['bytes'] for a in assets), comparisonLevels=pair_levels), ensure_ascii=False))


if __name__ == '__main__':
    main()
