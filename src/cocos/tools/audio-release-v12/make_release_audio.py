"""Release-only air sounds, using the existing original project DSP pipeline.

No contact transients, steel recordings, resonators, downloads or model calls.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / 'src/cocos/tools'
import importlib.util
spec = importlib.util.spec_from_file_location('_release12_tools', TOOLS / 'audio-impact-v10/make_game_contacts.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
RATE = 44100
RUNTIME = ROOT / 'src/cocos/assets/resources/audio/combat-v12'
OUT = ROOT / 'source-art/audio/release-only-v12'
CONFIG = {
    'war_swing': dict(family='war', seconds=.26, volume=.62),
    'bow_release': dict(family='bow', seconds=.22, volume=.64, low=480, high=3300, center=.044, width=.024, rms=.078),
    'fir_release': dict(family='fir', seconds=.36, volume=.40, low=180, high=2350, center=.075, width=.044, rms=.095),
    'thu_release': dict(family='thu', seconds=.30, volume=.40, low=400, high=3900, center=.055, width=.030, rms=.090),
}


def make_air(cue, variation, cfg, shared):
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(f'release-air-v12:{cue}:{variation}'.encode()).digest()[:8], 'little'))
    t = np.arange(round(cfg['seconds'] * RATE)) / RATE
    speed = rng.uniform(.95, 1.05)
    center, width = cfg['center'] * speed, cfg['width'] * speed
    # Smooth air displacement: no contact click, puncture, bow-limb knock,
    # metal clank, impact burst, thunder crack or musical oscillator.
    front = shared._band(rng, len(t), RATE, cfg['low'], cfg['high'])
    front *= np.exp(-.5 * ((t - center) / width) ** 2)
    wake = shared._band(rng, len(t), RATE, cfg['low'] * .8, cfg['high'] * .58)
    wake *= np.exp(-.5 * ((t - center * 1.9) / (width * 1.35)) ** 2) * .32
    audio = front + wake
    audio *= np.sin(np.clip(t / .012, 0, 1) * np.pi / 2) ** 2
    audio *= tool.gate(t, cfg['seconds'] - .006, .045)
    audio = tool.balance(audio, cfg['rms'], .018, .150)
    audio *= min(1., .50 / max(1e-12, float(np.max(np.abs(audio)))))
    audio[0] = audio[-1] = 0
    return audio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', type=Path, default=tool.DEFAULT_FFMPEG)
    args = parser.parse_args()
    if not args.ffmpeg.is_file():
        parser.error('Use an installed FFmpeg path; nothing is downloaded.')
    pcm = tool.load('_release12_pcm', TOOLS / 'prepare-combat-audio.py')
    legacy = tool.load('_release12_metrics', TOOLS / 'audio-direction-v2/sfx_samples.py')
    delivery = tool.load('_release12_delivery', TOOLS / 'audio-direction-v2/assemble_studies.py')
    writer = tool.load('_release12_writer', TOOLS / 'audio-impact-v8/make_wuxia_contacts.py')
    shared = tool.load('_release12_air', TOOLS / 'audio-impact-v5/physical_cues.py')
    music = {p.relative_to(ROOT).as_posix(): tool.digest(p) for p in (RUNTIME.parent / 'music').glob('*') if p.is_file()}
    for p in (RUNTIME, OUT / 'audition'):
        p.mkdir(parents=True, exist_ok=True)
    pcm.meta(RUNTIME, 'directory')
    assets, bank = [], {}
    for cue, cfg in CONFIG.items():
        family = cfg['family']
        folder = RUNTIME / family
        folder.mkdir(exist_ok=True)
        pcm.meta(folder, 'directory')
        for variation in (1, 2, 3):
            target = folder / f'{cue}_v{variation}.wav'
            source = RUNTIME.parent / 'combat-v11' / family / target.name
            if cue == 'war_swing':
                shutil.copyfile(source, target)
                provenance = dict(source=source.relative_to(ROOT).as_posix(), sourceSha256=tool.digest(source), bytePreserved=True)
            else:
                writer.write_runtime(target, make_air(cue, variation, cfg, shared))
                provenance = dict(source='Original project band-limited noise and smooth air envelope; deterministic seed includes cue and variation.', bytePreserved=False)
            pcm.meta(target, 'audio-clip')
            audio = pcm.read_wav(target)
            metrics = legacy.audio_metrics(audio)
            if not metrics['finite'] or metrics['clippingSamples'] or metrics['oversampledPeakDbfs'] > -1 or abs(len(audio) / RATE - cfg['seconds']) > 1 / RATE:
                raise ValueError(f'Invalid release sound: {target}')
            assets.append(dict(cue=cue, variation=variation, path=target.relative_to(ROOT).as_posix(),
                resourcePath=f'audio/combat-v12/{family}/{target.stem}', bytes=target.stat().st_size,
                sha256=tool.digest(target), metrics=metrics, playbackVolume=cfg['volume'], **provenance))
            bank[(cue, variation)] = audio
    if len({a['sha256'] for a in assets}) != 12:
        raise ValueError('Expected twelve distinct clips')
    reel = np.zeros((12 * RATE, 2))
    markers = []
    for section, (cue, cfg) in enumerate(CONFIG.items()):
        for variation, offset in ((1, .25), (1, 1.30), (2, 1.70), (3, 2.10)):
            at = section * 3 + offset
            # Preview preserves the actual runtime gain and is an offline reel.
            stereo = np.repeat(bank[(cue, variation)][:, None] / np.sqrt(2), 2, axis=1)
            legacy._tap(reel, stereo, at, RATE, cfg['volume'])
            markers.append(dict(cue=cue, variation=variation, at=at, volume=cfg['volume']))
    delivery.STUDY = OUT
    with tempfile.TemporaryDirectory(prefix='sword-fire-release-v12-') as scratch:
        preview = delivery.emit(args.ffmpeg, OUT / 'audition', 'release-only-v12', '剑与火 · 仅挥剑与释放呼啸', reel, Path(scratch))
    if any(tool.digest(ROOT / p) != sha for p, sha in music.items()):
        raise ValueError('Music changed')
    tool.dump(OUT / 'manifest.json', dict(version=12, date='2026-11-17',
        direction='No combat contacts or windup audio; only louder swings and clean release air.',
        production='Existing project original air sounds and installed NumPy/SciPy/FFmpeg. No recorded steel, model calls, downloads or runtime dependencies.',
        assets=assets, totalRuntimeBytes=sum(a['bytes'] for a in assets), preview=preview, markers=markers,
        protectedMusic=music, listeningAcceptance='Pending user audition of release-only balance.',
        runtimeAcceptance='See separate integration verification; offline preview is not engine/device playback.'))
    print(dict(clips=len(assets), bytes=sum(a['bytes'] for a in assets), output=str(OUT)))


if __name__ == '__main__':
    main()
